#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

NEGATIVE_CASES = {
    "no_auth",
    "alt_role",
    "replacement_variant",
    "operator_variant",
    "negative_control",
    "forbidden_control",
    "cross_account_control",
    "cross_tenant_control",
}
MUTATION_CASES = {
    "safe_probe_query",
    "field_expand_probe",
    "origin_probe",
    "method_content_type_probe",
    "callback_url_probe",
    "replacement_variant",
    "operator_variant",
}
READBACK_CASES = {
    "read_back",
    "readback",
    "state_readback",
    "ui_readback",
    "object_readback",
    "export_readback",
}
READBACK_HINTS = {
    "readback",
    "read_back",
    "browser_screenshot",
    "ui_state",
    "state_diff",
    "after_state",
    "response_diff",
    "object_readback",
    "export_readback",
}
JUDGE_EVENT_TYPES = {
    "test_started",
    "control_request_sent",
    "payload_attempted",
    "evidence_added",
    "endpoint_angle_tested",
    "evidence_reviewed",
    "verdict_set",
    "gap_found",
    "mapping_gap_found",
    "proxy_history_imported",
    "fresh_repro_completed",
}
SENSITIVE_MARKERS = ["authorization:", "cookie:", "x-api-key", "bearer ", "set-cookie:"]


@dataclass
class Judgement:
    test_id: str
    endpoint_id: str
    angle: str
    score: int
    decision: str
    confidence: str
    verdict: str
    present: list[str]
    missing: list[str]
    warnings: list[str]
    next_action: str
    review_path: str


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def json_dump(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)


def slugify(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() or ch in "._-" else "-" for ch in value.strip())
    while "--" in clean:
        clean = clean.replace("--", "-")
    return clean.strip("-") or "item"


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def write_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json_dump(event) + "\n")


def build_graph(root: Path) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_graph.py"), "--root", str(root)], check=True)


def case_name(event: dict[str, Any]) -> str:
    return str(event.get("case") or "").lower()


def evidence_path(event: dict[str, Any]) -> str:
    return str(event.get("evidence_path") or "")


def evidence_type(event: dict[str, Any]) -> str:
    return str(event.get("evidence_type") or "").lower()


def path_exists(root: Path, rel: str) -> bool:
    path = root / rel
    return bool(rel) and path.exists() and path.is_file() and path.stat().st_size > 0


def has_unredacted_secret(root: Path, rel: str) -> bool:
    if not path_exists(root, rel):
        return False
    text = (root / rel).read_text(encoding="utf-8", errors="ignore")[:30000].lower()
    if not any(marker in text for marker in SENSITIVE_MARKERS):
        return False
    return "[redacted]" not in text


def read_evidence_text(root: Path, rel: str) -> str:
    if not path_exists(root, rel):
        return ""
    return (root / rel).read_text(encoding="utf-8", errors="ignore")


def parse_status_and_body(text: str) -> tuple[int | None, str]:
    status: int | None = None
    match = re.search(r"(?im)^Status:\s*(\d{3})\b", text)
    if match:
        status = int(match.group(1))
    marker = "Body preview:"
    if marker in text:
        return status, text.split(marker, 1)[1].strip()
    marker = "Body:"
    if marker in text:
        return status, text.rsplit(marker, 1)[1].strip()
    return status, text[-4000:].strip()


def event_texts(root: Path, events: list[dict[str, Any]]) -> list[tuple[dict[str, Any], int | None, str]]:
    out: list[tuple[dict[str, Any], int | None, str]] = []
    for event in events:
        rel = evidence_path(event)
        text = read_evidence_text(root, rel)
        if not text:
            continue
        status, body = parse_status_and_body(text)
        out.append((event, status, body))
    return out


def semantic_response_checks(
    root: Path,
    control_events: list[dict[str, Any]],
    payload_events: list[dict[str, Any]],
    all_events: list[dict[str, Any]],
) -> tuple[int, list[str], list[str], list[str], dict[str, bool]]:
    points = 0
    present: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    baseline_texts = event_texts(root, control_events)
    variant_texts = event_texts(root, [event for event in payload_events if case_name(event) not in READBACK_CASES])
    readback_texts = event_texts(root, [event for event in all_events if case_name(event) in READBACK_CASES or "readback" in evidence_path(event).lower()])

    semantic_diff = False
    if baseline_texts and variant_texts:
        _, base_status, base_body = baseline_texts[-1]
        _, variant_status, variant_body = variant_texts[-1]
        if base_status != variant_status:
            semantic_diff = True
            points += 8
            present.append("semantic_status_diff")
        ratio = difflib.SequenceMatcher(None, base_body[:12000], variant_body[:12000]).ratio() if base_body or variant_body else 1.0
        if ratio < 0.98:
            semantic_diff = True
            points += 8
            present.append(f"semantic_body_diff ratio={ratio:.2f}")
        if not semantic_diff:
            missing.append("baseline and variant response semantics look identical")
    else:
        missing.append("semantic diff needs readable baseline and variant evidence")

    ownership_markers = ["owner", "owned", "account", "tenant", "workspace", "organization", "user_id", "role", "permission"]
    ownership_context = any(
        any(key in str(event.get(field) or "").lower() for key in ownership_markers)
        for event in all_events
        for field in ["reason", "note", "expected_result", "ownership_proof", "target", "path", "endpoint_id"]
    )
    ownership_context = ownership_context or any(
        any(key in body.lower() for key in ownership_markers)
        for _, _, body in baseline_texts + variant_texts + readback_texts
    )
    if ownership_context:
        points += 6
        present.append("ownership_or_role_context")
    else:
        warnings.append("ownership/role proof is not explicit in events or evidence text")

    if readback_texts:
        points += 5
        present.append("readback_text_parseable")
    else:
        warnings.append("read-back evidence exists only as metadata or is not parseable")

    return points, present, missing, warnings, {"semantic_diff": semantic_diff, "ownership_context": ownership_context}


def latest(events: list[dict[str, Any]], key: str) -> str:
    for event in reversed(events):
        value = event.get(key)
        if value:
            return str(value)
    return ""


def group_tests(events: list[dict[str, Any]], test_id_filter: str, endpoint_filter: str, angle_filter: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("type") not in JUDGE_EVENT_TYPES:
            continue
        test_id = str(event.get("test_id") or "")
        if not test_id:
            continue
        if test_id_filter and test_id != test_id_filter:
            continue
        if endpoint_filter and str(event.get("endpoint_id") or "") != endpoint_filter:
            continue
        if angle_filter and str(event.get("angle") or "") != angle_filter:
            continue
        grouped.setdefault(test_id, []).append(event)
    return grouped


def check_set(root: Path, events: list[dict[str, Any]]) -> tuple[int, list[str], list[str], list[str], dict[str, bool]]:
    present: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    points = 0

    control_events = [event for event in events if event.get("type") == "control_request_sent"]
    payload_events = [event for event in events if event.get("type") == "payload_attempted"]
    evidence_events = [event for event in events if event.get("type") == "evidence_added"]
    angle_events = [event for event in events if event.get("type") == "endpoint_angle_tested"]
    evidence_reviews = [event for event in events if event.get("type") == "evidence_reviewed"]
    verdict_events = [event for event in events if event.get("type") == "verdict_set"]
    gap_events = [event for event in events if event.get("type") in {"gap_found", "mapping_gap_found"}]

    baseline = bool([event for event in control_events if case_name(event) in {"", "baseline", "control", "baseline_control"}])
    baseline_evidence = bool([
        event for event in evidence_events
        if "baseline" in evidence_path(event).lower() or case_name(event) in {"baseline", "control", "baseline_control"}
    ])
    mutation = bool([
        event for event in payload_events
        if case_name(event) in MUTATION_CASES or case_name(event) not in {"", "baseline", "control"}
    ])
    mutation_evidence = bool([
        event for event in evidence_events
        if case_name(event) in MUTATION_CASES
        or any(name in evidence_path(event).lower() for name in MUTATION_CASES)
        or "mutat" in evidence_path(event).lower()
        or "variant" in evidence_path(event).lower()
    ])
    negative = bool([
        event for event in payload_events
        if case_name(event) in NEGATIVE_CASES or str(event.get("expected_result") or "").lower() in {"reject", "denied", "blocked"}
    ])
    negative_evidence = bool([
        event for event in evidence_events
        if case_name(event) in NEGATIVE_CASES
        or any(name in evidence_path(event).lower() for name in NEGATIVE_CASES)
        or "negative" in evidence_path(event).lower()
    ])
    readback = bool([
        event for event in events
        if case_name(event) in READBACK_CASES
        or any(hint in evidence_path(event).lower() for hint in READBACK_HINTS)
        or any(hint in evidence_type(event) for hint in READBACK_HINTS)
    ])
    existing_files = [event for event in evidence_events if path_exists(root, evidence_path(event))]
    missing_files = [evidence_path(event) for event in evidence_events if evidence_path(event) and not path_exists(root, evidence_path(event))]
    proxy_or_browser = [
        event for event in evidence_events
        if evidence_type(event).startswith(("burp_", "caido_", "browser_"))
        or "/burp/" in evidence_path(event)
        or "/caido/" in evidence_path(event)
        or "/screenshots/" in evidence_path(event)
    ]
    unredacted = [evidence_path(event) for event in evidence_events if has_unredacted_secret(root, evidence_path(event))]
    latest_review_status = latest(evidence_reviews, "status")
    latest_review_score = latest(evidence_reviews, "score")
    latest_verdict = latest(verdict_events, "status")
    semantic_points, semantic_present, semantic_missing, semantic_warnings, semantic_facts = semantic_response_checks(
        root,
        control_events,
        payload_events,
        events,
    )
    points += semantic_points
    present.extend(semantic_present)
    missing.extend(semantic_missing)
    warnings.extend(semantic_warnings)
    fresh_repro_passed = any(
        event.get("type") == "fresh_repro_completed"
        and str(event.get("fresh_repro") or "").lower() == "passed"
        for event in events
    )

    checks = [
        ("test_context", 5, bool(latest(events, "endpoint_id") and latest(events, "test_id")), "test has endpoint/test context"),
        ("baseline_request", 10, baseline, "baseline request missing"),
        ("baseline_evidence", 10, baseline_evidence, "baseline evidence missing"),
        ("mutated_request", 13, mutation, "mutated/variant request missing"),
        ("mutated_evidence", 12, mutation_evidence, "mutated/variant evidence missing"),
        ("negative_control", 13, negative, "negative control missing"),
        ("negative_control_evidence", 10, negative_evidence, "negative control evidence missing"),
        ("readback", 15, readback, "read-back or browser-visible state missing"),
        ("saved_evidence_files", 7, bool(existing_files), "non-empty saved evidence files missing"),
        ("endpoint_angle_tested", 5, bool(angle_events), "endpoint_angle_tested missing"),
    ]
    for key, value, ok, message in checks:
        if ok:
            points += value
            present.append(key)
        else:
            missing.append(message)

    if proxy_or_browser:
        points += 5
        present.append("proxy_or_browser_context")
    else:
        warnings.append("no Burp/Caido/browser-visible context")

    if latest_review_status == "evidence_sufficient":
        points += 8
        present.append("evidence_scorer_sufficient")
    elif latest_review_status == "evidence_partial":
        points += 4
        warnings.append("evidence scorer is partial")
    elif not latest_review_status:
        warnings.append("run bbf evidence-score before relying on this judgement")

    if verdict_events:
        points += 5
        present.append("verdict_event")
    else:
        warnings.append("no verdict_set event")

    if gap_events:
        warnings.append("gap event exists; resolve it before report")
    if missing_files:
        warnings.append("missing evidence file(s): " + ", ".join(missing_files[:5]))
    if unredacted:
        warnings.append("possible unredacted secret-bearing evidence: " + ", ".join(unredacted[:5]))
        points = max(0, points - 25)

    facts = {
        "baseline": baseline and baseline_evidence,
        "mutation": mutation and mutation_evidence,
        "negative": negative and negative_evidence,
        "readback": readback,
        "files": bool(existing_files),
        "proxy_or_browser": bool(proxy_or_browser),
        "unredacted_secret": bool(unredacted),
        "blocked": latest_verdict == "blocked" or bool(gap_events),
        "out_of_scope": latest_verdict == "out_of_scope",
        "by_design": latest_verdict == "by_design",
        "confirmed_or_candidate": latest_verdict in {"confirmed", "finding_candidate"},
        "tested_secure": latest_verdict == "tested_secure",
        "evidence_sufficient": latest_review_status == "evidence_sufficient",
        "semantic_diff": semantic_facts["semantic_diff"],
        "ownership_context": semantic_facts["ownership_context"],
        "fresh_repro": fresh_repro_passed,
    }
    if latest_review_score:
        try:
            points = max(points, min(100, int(float(latest_review_score))))
        except ValueError:
            pass
    return min(100, points), present, missing, warnings, facts


def decision_for(score: int, verdict: str, facts: dict[str, bool], missing: list[str]) -> tuple[str, str, str]:
    must_haves = facts["baseline"] and facts["mutation"] and facts["negative"] and facts["readback"] and facts["files"]
    if facts["out_of_scope"] or facts["by_design"]:
        return "judge_rejected", "high", "Do not report; keep policy/by-design evidence linked."
    if facts["blocked"]:
        return "judge_blocked", "medium", "Resolve the blocker/gap before judging reportability."
    if facts["unredacted_secret"]:
        return "judge_rejected", "high", "Redact secret-bearing evidence before any report or sharing."
    if facts["confirmed_or_candidate"] and score >= 85 and must_haves and facts["semantic_diff"] and facts["ownership_context"] and facts["fresh_repro"]:
        return "judge_reportable", "high", "Draft report with the judged evidence package and reproduce once more if scope requires it."
    if facts["confirmed_or_candidate"] and score >= 85 and must_haves and not facts["fresh_repro"]:
        return "judge_candidate", "medium", "Run `bbf fresh-repro --test-id <id>` with fresh session headers, then rerun `bbf judge`."
    if facts["confirmed_or_candidate"] and score >= 80 and must_haves and (not facts["semantic_diff"] or not facts["ownership_context"]):
        return "judge_candidate", "medium", "Add semantic response diff and explicit ownership/role proof before report."
    if facts["confirmed_or_candidate"] and score >= 65:
        return "judge_candidate", "medium", "Fix missing proof controls, then rerun `bbf evidence-score` and `bbf judge`."
    if facts["tested_secure"] and facts["negative"] and facts["baseline"] and score >= 70:
        return "judge_rejected", "medium", "Keep as tested_secure; no report unless new signal appears."
    if score >= 50:
        return "judge_needs_evidence", "medium", "Collect missing evidence: " + "; ".join(missing[:3])
    return "judge_needs_evidence", "low", "Rebuild the evidence package from baseline, mutation, negative control, and read-back."


def write_judgement_report(root: Path, judgement: Judgement) -> None:
    path = root / judgement.review_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Evidence Judge Review\n\n"
        f"- Test ID: `{judgement.test_id}`\n"
        f"- Endpoint: `{judgement.endpoint_id or '-'}`\n"
        f"- Angle: `{judgement.angle or '-'}`\n"
        f"- Score: `{judgement.score}`\n"
        f"- Decision: `{judgement.decision}`\n"
        f"- Confidence: `{judgement.confidence}`\n"
        f"- Latest verdict: `{judgement.verdict or '-'}`\n\n"
        "## Present\n\n"
        + ("\n".join(f"- {item}" for item in judgement.present) if judgement.present else "- none")
        + "\n\n## Missing\n\n"
        + ("\n".join(f"- {item}" for item in judgement.missing) if judgement.missing else "- none")
        + "\n\n## Warnings\n\n"
        + ("\n".join(f"- {item}" for item in judgement.warnings) if judgement.warnings else "- none")
        + "\n\n## Next Action\n\n"
        f"{judgement.next_action}\n",
        encoding="utf-8",
    )


def judge_test(root: Path, test_id: str, events: list[dict[str, Any]]) -> Judgement:
    score, present, missing, warnings, facts = check_set(root, events)
    verdict = latest([event for event in events if event.get("type") == "verdict_set"], "status")
    decision, confidence, next_action = decision_for(score, verdict, facts, missing)
    endpoint_id = latest(events, "endpoint_id")
    angle = latest(events, "angle")
    review_path = f"evidence/judgements/judge-{slugify(test_id)}.md"
    judgement = Judgement(
        test_id=test_id,
        endpoint_id=endpoint_id,
        angle=angle,
        score=score,
        decision=decision,
        confidence=confidence,
        verdict=verdict,
        present=present,
        missing=missing,
        warnings=warnings,
        next_action=next_action,
        review_path=review_path,
    )
    write_judgement_report(root, judgement)
    return judgement


def write_summary(root: Path, judgements: list[Judgement], run_id: str) -> str:
    out = root / "data/judgements.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": "1.0.0",
        "generated_at": now(),
        "run_id": run_id,
        "judgements": [
            {
                "test_id": item.test_id,
                "endpoint_id": item.endpoint_id,
                "angle": item.angle,
                "score": item.score,
                "decision": item.decision,
                "confidence": item.confidence,
                "verdict": item.verdict,
                "missing": item.missing,
                "warnings": item.warnings,
                "next_action": item.next_action,
                "review_path": item.review_path,
            }
            for item in judgements
        ],
    }
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return str(out.relative_to(root))


def emit_events(root: Path, events_path: Path, events: list[dict[str, Any]], judgements: list[Judgement], run_id: str, actor: str, summary_path: str) -> None:
    engagement_id = current_engagement_id(root)
    next_num = len(events) + 1
    for item in judgements:
        write_event(
            events_path,
            {
                "id": f"evt-{next_num:06d}",
                "ts": now(),
                "engagement_id": engagement_id,
                "actor": actor,
                "type": "evidence_judged",
                "status": item.decision,
                "run_id": run_id,
                "test_id": item.test_id,
                "endpoint_id": item.endpoint_id,
                "angle": item.angle,
                "score": item.score,
                "confidence": item.confidence,
                "latest_verdict": item.verdict,
                "present": item.present,
                "missing": item.missing,
                "warnings": item.warnings,
                "next_action": item.next_action,
                "review_path": item.review_path,
            },
        )
        next_num += 1

    counts = {key: 0 for key in ["judge_reportable", "judge_candidate", "judge_needs_evidence", "judge_blocked", "judge_rejected"]}
    for item in judgements:
        counts[item.decision] = counts.get(item.decision, 0) + 1
    avg_score = round(sum(item.score for item in judgements) / len(judgements), 1) if judgements else 0
    write_event(
        events_path,
        {
            "id": f"evt-{next_num:06d}",
            "ts": now(),
            "engagement_id": engagement_id,
            "actor": actor,
            "type": "judge_reviewed",
            "status": "saved",
            "run_id": run_id,
            "summary_path": summary_path,
            "tests_judged": len(judgements),
            "judge_avg_score": avg_score,
            **counts,
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Judge evidence reportability, not just visibility.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--test-id", default="")
    parser.add_argument("--endpoint-id", default="")
    parser.add_argument("--angle", default="")
    parser.add_argument("--all", action="store_true", help="Judge all matching tests.")
    parser.add_argument("--no-event", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--actor", default="ai")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    events_path = root / "data/events.jsonl"
    events = read_events(events_path)
    grouped = group_tests(events, args.test_id, args.endpoint_id, args.angle)
    if not grouped:
        raise SystemExit("no matching tests found to judge")

    items = list(grouped.items())
    if not args.all and not args.test_id:
        items = items[:1]

    judgements = [judge_test(root, test_id, test_events) for test_id, test_events in items]
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")
    summary_path = write_summary(root, judgements, run_id)
    if not args.no_event:
        emit_events(root, events_path, events, judgements, run_id, args.actor, summary_path)
    if not args.no_build:
        build_graph(root)

    for item in judgements:
        print(f"{item.test_id}: {item.score}/100 {item.decision} confidence={item.confidence}")
        if item.missing:
            print("  missing: " + "; ".join(item.missing[:5]))
        if item.warnings:
            print("  warnings: " + "; ".join(item.warnings[:5]))
    print(f"judged {len(judgements)} test(s)")
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
