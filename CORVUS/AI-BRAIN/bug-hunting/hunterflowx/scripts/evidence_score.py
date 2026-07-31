#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
READBACK_EVIDENCE_HINTS = {
    "readback",
    "read_back",
    "browser_screenshot",
    "ui_state",
    "state_diff",
    "after_state",
    "response_diff",
}
EVIDENCE_TYPES = {
    "evidence_added",
    "control_request_sent",
    "payload_attempted",
    "endpoint_angle_tested",
    "verdict_set",
}


@dataclass
class Score:
    test_id: str
    endpoint_id: str
    angle_id: str
    angle: str
    score: int
    grade: str
    present: list[str]
    missing: list[str]
    warnings: list[str]
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


def event_test_id(event: dict[str, Any]) -> str:
    return str(event.get("test_id") or "")


def evidence_path(event: dict[str, Any]) -> str:
    return str(event.get("evidence_path") or "")


def case_name(event: dict[str, Any]) -> str:
    return str(event.get("case") or "").lower()


def evidence_type(event: dict[str, Any]) -> str:
    return str(event.get("evidence_type") or "").lower()


def path_exists(root: Path, path: str) -> bool:
    return bool(path) and (root / path).exists() and (root / path).is_file() and (root / path).stat().st_size > 0


def has_sensitive_unredacted(root: Path, path: str) -> bool:
    if not path_exists(root, path):
        return False
    text = (root / path).read_text(encoding="utf-8", errors="ignore")[:20000].lower()
    sensitive_markers = ["authorization:", "cookie:", "x-api-key", "bearer "]
    if not any(marker in text for marker in sensitive_markers):
        return False
    return "[redacted]" not in text


def group_tests(events: list[dict[str, Any]], test_id_filter: str, endpoint_filter: str, angle_filter: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("type") not in EVIDENCE_TYPES:
            continue
        test_id = event_test_id(event)
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


def latest_value(events: list[dict[str, Any]], key: str) -> str:
    for event in reversed(events):
        value = event.get(key)
        if value:
            return str(value)
    return ""


def score_test(root: Path, test_id: str, events: list[dict[str, Any]], min_score: int) -> Score:
    present: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    points = 0

    control_events = [event for event in events if event.get("type") == "control_request_sent"]
    payload_events = [event for event in events if event.get("type") == "payload_attempted"]
    evidence_events = [event for event in events if event.get("type") == "evidence_added"]
    angle_events = [event for event in events if event.get("type") == "endpoint_angle_tested"]
    verdict_events = [event for event in events if event.get("type") == "verdict_set"]

    baseline_events = [event for event in control_events if case_name(event) in {"", "baseline", "control", "baseline_control"}]
    baseline_evidence = [
        event for event in evidence_events
        if "baseline" in evidence_path(event).lower() or case_name(event) in {"baseline", "control", "baseline_control"}
    ]
    mutated_events = [
        event for event in payload_events
        if case_name(event) in MUTATION_CASES or case_name(event) not in {"", "baseline", "control"}
    ]
    mutated_evidence = [
        event for event in evidence_events
        if any(name in evidence_path(event).lower() for name in MUTATION_CASES)
        or any(name in evidence_path(event).lower() for name in NEGATIVE_CASES)
        or case_name(event) in MUTATION_CASES
        or case_name(event) in NEGATIVE_CASES
    ]
    negative_events = [event for event in payload_events if case_name(event) in NEGATIVE_CASES or str(event.get("expected_result") or "").lower() in {"reject", "denied", "blocked"}]
    negative_evidence = [
        event for event in evidence_events
        if any(name in evidence_path(event).lower() for name in NEGATIVE_CASES)
        or case_name(event) in NEGATIVE_CASES
    ]
    readback_events = [
        event for event in events
        if case_name(event) in READBACK_CASES
        or any(hint in evidence_path(event).lower() for hint in READBACK_EVIDENCE_HINTS)
        or any(hint in evidence_type(event) for hint in READBACK_EVIDENCE_HINTS)
    ]
    existing_evidence = [event for event in evidence_events if path_exists(root, evidence_path(event))]
    missing_files = [evidence_path(event) for event in evidence_events if evidence_path(event) and not path_exists(root, evidence_path(event))]
    unredacted = [evidence_path(event) for event in evidence_events if has_sensitive_unredacted(root, evidence_path(event))]
    proxy_or_browser = [
        event for event in evidence_events
        if evidence_type(event).startswith(("burp_", "caido_", "browser_"))
        or "/burp/" in evidence_path(event)
        or "/caido/" in evidence_path(event)
        or "/screenshots/" in evidence_path(event)
    ]

    checks = [
        ("baseline_request", 12, bool(baseline_events), "baseline request/control_request_sent exists"),
        ("baseline_evidence", 13, bool(baseline_evidence), "baseline evidence file/event exists"),
        ("mutated_request", 15, bool(mutated_events), "mutated or variant request/payload_attempted exists"),
        ("mutated_evidence", 15, bool(mutated_evidence), "mutated/variant evidence exists"),
        ("negative_control", 15, bool(negative_events), "negative control exists"),
        ("negative_control_evidence", 10, bool(negative_evidence), "negative control evidence exists"),
        ("readback", 15, bool(readback_events), "read-back, browser state, or response diff evidence exists"),
        ("angle_tested", 5, bool(angle_events), "endpoint_angle_tested exists"),
    ]

    for key, value, ok, message in checks:
        if ok:
            points += value
            present.append(key)
        else:
            missing.append(message)

    if existing_evidence:
        points += 5
        present.append("evidence_files_exist")
    else:
        missing.append("no non-empty evidence files found")

    if proxy_or_browser:
        points += 5
        present.append("proxy_or_browser_context")
    else:
        warnings.append("no Burp/Caido/browser-visible context found")

    if verdict_events:
        points += 5
        present.append("verdict_event_exists")
    else:
        warnings.append("no verdict_set event yet")

    if missing_files:
        warnings.append("missing evidence files: " + ", ".join(missing_files[:5]))
    if unredacted:
        warnings.append("possible unredacted secret-bearing evidence: " + ", ".join(unredacted[:5]))
        points = max(0, points - 20)

    score = min(100, points)
    critical_missing = [
        item for item in missing
        if item.startswith("baseline")
        or item.startswith("mutated")
        or item.startswith("negative")
        or "read-back" in item
        or item.startswith("no non-empty evidence")
    ]
    if score >= min_score and not critical_missing:
        grade = "evidence_sufficient"
    elif score >= 50:
        grade = "evidence_partial"
    else:
        grade = "evidence_incomplete"

    review_dir = root / "evidence/reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"review-{slugify(test_id)}.md"
    endpoint_id = latest_value(events, "endpoint_id")
    angle_id = latest_value(events, "angle_id")
    angle = latest_value(events, "angle")
    review_path.write_text(
        "# Evidence Quality Review\n\n"
        f"- Test ID: `{test_id}`\n"
        f"- Endpoint: `{endpoint_id or '-'}`\n"
        f"- Angle: `{angle or '-'}`\n"
        f"- Score: `{score}`\n"
        f"- Grade: `{grade}`\n\n"
        "## Present\n\n"
        + "\n".join(f"- {item}" for item in present)
        + "\n\n## Missing\n\n"
        + ("\n".join(f"- {item}" for item in missing) if missing else "- none")
        + "\n\n## Warnings\n\n"
        + ("\n".join(f"- {item}" for item in warnings) if warnings else "- none")
        + "\n",
        encoding="utf-8",
    )

    return Score(
        test_id=test_id,
        endpoint_id=endpoint_id,
        angle_id=angle_id,
        angle=angle,
        score=score,
        grade=grade,
        present=present,
        missing=missing,
        warnings=warnings,
        review_path=str(review_path.relative_to(root)),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score evidence quality for executed tests.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--test-id", default="")
    parser.add_argument("--endpoint-id", default="")
    parser.add_argument("--angle", default="")
    parser.add_argument("--min-score", type=int, default=75)
    parser.add_argument("--all", action="store_true", help="Score all matching tests.")
    parser.add_argument("--no-event", action="store_true", help="Do not append evidence_reviewed events.")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--actor", default="ai")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    events_path = root / "data/events.jsonl"
    events = read_events(events_path)
    grouped = group_tests(events, args.test_id, args.endpoint_id, args.angle)
    if not grouped:
        raise SystemExit("no matching tests with evidence-related events found")

    items = list(grouped.items())
    if not args.all and not args.test_id:
        items = items[:1]

    next_num = len(events) + 1
    engagement_id = current_engagement_id(root)
    scores: list[Score] = []
    for test_id, test_events in items:
        score = score_test(root, test_id, test_events, args.min_score)
        scores.append(score)
        if not args.no_event:
            write_event(
                events_path,
                {
                    "id": f"evt-{next_num:06d}",
                    "ts": now(),
                    "engagement_id": engagement_id,
                    "actor": args.actor,
                    "type": "evidence_reviewed",
                    "status": score.grade,
                    "test_id": score.test_id,
                    "endpoint_id": score.endpoint_id,
                    "angle_id": score.angle_id,
                    "angle": score.angle,
                    "score": score.score,
                    "min_score": args.min_score,
                    "present": score.present,
                    "missing": score.missing,
                    "warnings": score.warnings,
                    "review_path": score.review_path,
                },
            )
            next_num += 1
        print(f"{score.test_id}: {score.score}/100 {score.grade}")
        if score.missing:
            print("  missing: " + "; ".join(score.missing))
        if score.warnings:
            print("  warnings: " + "; ".join(score.warnings))

    if not args.no_build:
        build_graph(root)
    print(f"reviewed {len(scores)} test(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
