#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_queue


DEFAULT_CONFIG: dict[str, Any] = {
    "version": "1.0.0",
    "autonomy_levels": {
        "passive_auto": {
            "description": "Local analysis only; no live request or state change.",
            "requires_approval": False,
            "allowed_stages": ["recon", "source-read", "map-endpoint", "angle-plan", "evidence-score", "judge", "report", "governance", "attack-path-review"],
        },
        "active_safe_auto": {
            "description": "Low-risk active request inside allowlist; disabled by default.",
            "requires_approval": True,
            "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        },
        "active_requires_approval": {
            "description": "Live testing, replay, browser/Burp/Caido execution, or fresh repro.",
            "requires_approval": True,
            "allowed_stages": ["angle-exec", "fresh-repro", "active-test"],
        },
        "hard_deny": {
            "description": "Out-of-scope, destructive, forbidden path, or policy violation.",
            "requires_approval": False,
        },
    },
    "agent_roles": {
        "coordinator": "Maintains global state, queue, blockers, and next action.",
        "recon_agent": "Maps assets, endpoints, parameters, runtime observations, and external signals.",
        "source_mapper": "Reads source one file at a time and links file -> flow -> endpoint.",
        "attack_path_planner": "Builds hypotheses, chains, and ranked attack paths.",
        "executor": "Runs approved tests through browser/Burp/Caido/http under safety policy.",
        "validator": "Checks deterministic proof, controls, fresh repro, and repeatability.",
        "evidence_judge": "Decides reportability from saved evidence, not model confidence.",
        "report_reviewer": "Builds report, missing-proof gate, duplicate/status tracking.",
        "safety_governor": "Enforces allowlist, forbidden paths, rate limit, and approval.",
        "data_steward": "Controls retention, redaction, sanitized exports, and secret handling.",
    },
    "validation": {
        "hypothesis_is_not_finding": True,
        "requires_external_validation": True,
        "minimum_high_risk_reviewers": 4,
        "reportable_requires": ["baseline", "mutation", "negative_control", "read_back", "semantic_diff", "fresh_repro", "saved_evidence"],
    },
    "data_governance": {
        "retention_days": 90,
        "never_export_dirs": [".private"],
        "default_exclude_globs": ["*.pid", "*.log", "*.err.log", ".dashboard*", "*.sqlite", "*.db"],
        "redact_header_names": ["authorization", "cookie", "set-cookie", "x-csrf-token", "x-api-key", "api-key"],
        "redact_key_regex": "(?i)(token|secret|password|passwd|authorization|cookie|session|csrf|api[_-]?key)",
        "sanitize_export_text_only": True,
    },
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".http",
    ".csv",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".log",
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def config_path(root: Path) -> Path:
    return root / "data" / "ai_governance.json"


def write_default(root: Path, force: bool = False) -> Path:
    path = config_path(root)
    if force or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(DEFAULT_CONFIG)
        data["generated_at"] = now()
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def load_config(root: Path) -> tuple[dict[str, Any], Path]:
    path = config_path(root)
    if not path.exists():
        write_default(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    merged = dict(DEFAULT_CONFIG)
    merged.update(data if isinstance(data, dict) else {})
    return merged, path


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_events(root: Path) -> list[dict[str, Any]]:
    path = root / "data/events.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def write_event(root: Path, event: dict[str, Any]) -> None:
    events = read_events(root)
    path = root / "data/events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event.setdefault("id", f"evt-{len(events) + 1:06d}")
    event.setdefault("ts", now())
    event.setdefault("engagement_id", current_engagement_id(root))
    event.setdefault("actor", "governance")
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, separators=(",", ":")) + "\n")


def status(root: Path) -> dict[str, Any]:
    cfg, cfg_file = load_config(root)
    safety = read_json(root / "data/safety_policy.json", {})
    queue = read_json(root / "data/run_queue.json", {"tasks": []})
    report_lifecycle = read_json(root / "data/report_lifecycle.json", {"reports": []})
    events = read_events(root)
    return {
        "path": str(cfg_file),
        "config": cfg,
        "summary": {
            "allow_hosts_count": len(safety.get("allow_hosts") or []),
            "safety_mode": safety.get("mode", "missing"),
            "max_rps": safety.get("max_rps", "missing"),
            "queue_tasks": len(queue.get("tasks") or []),
            "active_tasks": sum(1 for task in queue.get("tasks") or [] if task.get("active")),
            "reports": len(report_lifecycle.get("reports") or []),
            "events": len(events),
        },
    }


def classify_task(task: dict[str, Any]) -> str:
    if task.get("autonomy_level"):
        return str(task["autonomy_level"])
    stage = str(task.get("stage") or "")
    command = " ".join(str(item) for item in task.get("command") or [])
    if task.get("active") or stage in {"angle-exec", "fresh-repro", "active-test"} or "angle-exec" in command:
        return "active_requires_approval"
    if task.get("status") == "blocked" and "out-of-scope" in str(task.get("blocked_reason", "")).lower():
        return "hard_deny"
    return "passive_auto"


def governance_checks(root: Path) -> dict[str, Any]:
    cfg, cfg_file = load_config(root)
    safety = read_json(root / "data/safety_policy.json", {})
    queue = read_json(root / "data/run_queue.json", {"tasks": []})
    events = read_events(root)
    findings = [e for e in events if e.get("type") in {"finding_promoted", "verdict_set"} and e.get("status") in {"confirmed", "finding_candidate"}]
    judged = {str(e.get("test_id") or ""): e for e in events if e.get("type") in {"evidence_judged", "judge_reviewed"}}
    evidence = {str(e.get("test_id") or ""): e for e in events if e.get("type") in {"evidence_added", "evidence_reviewed"}}
    hypotheses = [e for e in events if e.get("type") in {"creative_hypothesis_added", "chain_candidate_added", "attack_path_expanded"}]
    source_reads = [e for e in events if e.get("type") == "source_file_read"]
    source_reviews_missing = [e for e in source_reads if not str(e.get("review") or e.get("review_path") or "")]

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, severity: str, detail: str, next_action: str = "") -> None:
        checks.append({"name": name, "passed": passed, "severity": severity, "detail": detail, "next_action": next_action})

    allow_hosts = safety.get("allow_hosts") or []
    add(
        "safety_allowlist",
        bool(allow_hosts),
        "critical",
        f"{len(allow_hosts)} allow_hosts configured",
        "Fill data/safety_policy.json allow_hosts before active testing.",
    )
    add(
        "rate_budget",
        float(safety.get("max_rps") or 0) <= 10 and float(safety.get("max_rps") or 0) > 0,
        "medium",
        f"max_rps={safety.get('max_rps')}",
        "Keep max_rps at or below program rules; default recommendation is 10.",
    )

    tasks = queue.get("tasks") or []
    missing_autonomy = [task.get("id") for task in tasks if not task.get("autonomy_level")]
    active_without_approval_gate = [
        task.get("id")
        for task in tasks
        if classify_task(task) == "active_requires_approval" and task.get("approval") not in {"pending", "approved"}
    ]
    add(
        "autonomy_labels",
        not missing_autonomy,
        "medium",
        f"{len(missing_autonomy)} queue tasks missing explicit autonomy_level",
        "Run bbf queue seed again for new defaults or add autonomy metadata to manual tasks.",
    )
    add(
        "active_approval_gate",
        not active_without_approval_gate,
        "critical",
        f"{len(active_without_approval_gate)} active tasks lack approval gate state",
        "Active testing must be pending/approved, never silent auto-run.",
    )

    unjudged_findings = []
    for finding in findings:
        test_id = str(finding.get("test_id") or "")
        if test_id and test_id not in judged:
            unjudged_findings.append(test_id)
    add(
        "finding_judge_gate",
        not unjudged_findings,
        "critical",
        f"{len(unjudged_findings)} candidate/confirmed tests have no judge event",
        "Run bbf evidence-score and bbf judge before report promotion.",
    )

    evidence_gap = []
    for finding in findings:
        test_id = str(finding.get("test_id") or "")
        if test_id and test_id not in evidence:
            evidence_gap.append(test_id)
    add(
        "finding_evidence_gate",
        not evidence_gap,
        "critical",
        f"{len(evidence_gap)} candidate/confirmed tests have no evidence/review event",
        "Add baseline, mutation, negative control, read-back, and saved evidence files.",
    )

    add(
        "hypothesis_separation",
        all(e.get("type") != "verdict_set" for e in hypotheses),
        "medium",
        f"{len(hypotheses)} hypotheses/chains remain separate from verdict events",
        "Keep hypothesis events separate; convert only after execution and evidence judge.",
    )

    add(
        "source_review_artifacts",
        not source_reviews_missing,
        "medium",
        f"{len(source_reviews_missing)} source_file_read events missing review artifact path",
        "Every source_file_read should point to source-reviews/<id>.md.",
    )

    roles = cfg.get("agent_roles") or {}
    events_roles = {str(e.get("agent_role") or e.get("role") or "") for e in events}
    used_roles = sorted(role for role in roles if role in events_roles)
    add(
        "agent_role_coverage",
        len(used_roles) >= 4 or len(events) == 0,
        "medium",
        f"{len(used_roles)} explicit agent roles observed: {', '.join(used_roles) or 'none'}",
        "Tag major events with agent_role or use role-specific queue stages.",
    )

    data_cfg = cfg.get("data_governance") or {}
    add(
        "data_governance_config",
        bool(data_cfg.get("never_export_dirs")) and bool(data_cfg.get("redact_key_regex")),
        "critical",
        "Data retention/redaction policy is configured",
        "Keep .private excluded and create sanitized exports for sharing/VPS handoff.",
    )

    failed = [c for c in checks if not c["passed"]]
    score = round(((len(checks) - len(failed)) / max(1, len(checks))) * 100, 1)
    severity_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    highest = max((severity_rank.get(c["severity"], 0) for c in failed), default=0)
    decision = "ready" if not failed else ("blocked" if highest >= 3 else "needs_attention")
    result = {
        "version": "1.0.0",
        "generated_at": now(),
        "engagement_id": current_engagement_id(root),
        "config_path": str(cfg_file),
        "score": score,
        "decision": decision,
        "checks": checks,
        "failed_checks": failed,
    }
    return result


def fix_queue_metadata(root: Path) -> dict[str, Any]:
    queue = run_queue.load_queue(root)
    changed = 0
    for task in queue.get("tasks") or []:
        stage = str(task.get("stage") or "")
        active = bool(task.get("active"))
        blocked = str(task.get("blocked_reason") or "")
        if not task.get("autonomy_level"):
            task["autonomy_level"] = run_queue.default_autonomy(stage, active, blocked)
            changed += 1
        if not task.get("agent_role"):
            task["agent_role"] = run_queue.STAGE_AGENT_ROLES.get(stage, "coordinator")
            changed += 1
        if not task.get("validation_gate"):
            task["validation_gate"] = "operator_approval" if task.get("autonomy_level") == "active_requires_approval" else "event_ledger"
            changed += 1
    run_queue.save_queue(root, queue)
    return {"status": "updated" if changed else "unchanged", "changed_fields": changed, "tasks": len(queue.get("tasks") or [])}


def write_review(root: Path, result: dict[str, Any], no_event: bool = False) -> dict[str, Any]:
    data_path = root / "data/ai_governance_review.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_path = root / "output/ai-governance-review.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AI Governance Review",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Engagement: {result['engagement_id']}",
        f"- Score: {result['score']}",
        f"- Decision: {result['decision']}",
        "",
        "## Checks",
        "",
    ]
    for check in result["checks"]:
        state = "PASS" if check["passed"] else "FAIL"
        lines.extend(
            [
                f"### {state} - {check['name']}",
                "",
                f"- Severity: {check['severity']}",
                f"- Detail: {check['detail']}",
                f"- Next action: {check['next_action'] or '-'}",
                "",
            ]
        )
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    result["report_path"] = str(report_path.relative_to(root))
    if not no_event:
        write_event(
            root,
            {
                "type": "ai_governance_reviewed",
                "status": result["decision"],
                "score": result["score"],
                "report_path": result["report_path"],
                "failed_checks": [c["name"] for c in result["failed_checks"]],
            },
        )
    return result


def redact_text(text: str, cfg: dict[str, Any]) -> str:
    key_regex = str((cfg.get("data_governance") or {}).get("redact_key_regex") or DEFAULT_CONFIG["data_governance"]["redact_key_regex"])
    text = re.sub(r"(?im)^(\s*(?:authorization|cookie|set-cookie|x-csrf-token|x-api-key|api-key)\s*[:=]\s*).+$", r"\1<REDACTED>", text)
    text = re.sub(rf"({key_regex})(['\"]?\s*[:=]\s*['\"]?)[^'\"\s,]+", r"\1\2<REDACTED>", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer <REDACTED>", text)
    return text


def should_skip(rel: Path, cfg: dict[str, Any]) -> bool:
    data_cfg = cfg.get("data_governance") or {}
    never_dirs = set(data_cfg.get("never_export_dirs") or [".private"])
    if any(part in never_dirs for part in rel.parts):
        return True
    globs = data_cfg.get("default_exclude_globs") or []
    return any(rel.match(str(pattern)) or rel.name == str(pattern) for pattern in globs)


def sanitized_export(root: Path, out: Path | None = None) -> dict[str, Any]:
    cfg, _ = load_config(root)
    out_path = out or root / "output" / f"sanitized-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    included = 0
    skipped = 0
    include_roots = ["data", "notes", "findings", "reports", "evidence", "source-reviews", "domain-depth", "output", "scope.md", "coverage-matrix.md", "multi-angle-coverage.md", "test-ledger.md", "priority-testing-plan.md"]
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in include_roots:
            base = root / item
            if not base.exists():
                continue
            paths = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
            for path in paths:
                rel = path.relative_to(root)
                if should_skip(rel, cfg):
                    skipped += 1
                    continue
                if path.suffix.lower() not in TEXT_EXTENSIONS:
                    skipped += 1
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    skipped += 1
                    continue
                zf.writestr(str(rel), redact_text(text, cfg))
                included += 1
    result = {
        "status": "created",
        "path": str(out_path),
        "included_files": included,
        "skipped_files": skipped,
        "generated_at": now(),
    }
    write_event(
        root,
        {
            "type": "sanitized_export_created",
            "status": "created",
            "export_path": str(out_path.relative_to(root) if out_path.is_relative_to(root) else out_path),
            "included_files": included,
            "skipped_files": skipped,
        },
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI governance, autonomy, validation, and data handling controls.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init")
    init.add_argument("--root", type=Path, default=Path.cwd())
    init.add_argument("--force", action="store_true")

    status_cmd = sub.add_parser("status")
    status_cmd.add_argument("--root", type=Path, default=Path.cwd())

    check = sub.add_parser("check")
    check.add_argument("--root", type=Path, default=Path.cwd())
    check.add_argument("--no-event", action="store_true")
    check.add_argument("--fix-queue", action="store_true", help="Backfill autonomy/agent/validation metadata before checking.")

    fix = sub.add_parser("fix-queue")
    fix.add_argument("--root", type=Path, default=Path.cwd())

    export = sub.add_parser("sanitize-export")
    export.add_argument("--root", type=Path, default=Path.cwd())
    export.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "init":
        print(write_default(root, force=args.force))
    elif args.cmd == "status":
        print(json.dumps(status(root), indent=2))
    elif args.cmd == "check":
        if args.fix_queue:
            fix_queue_metadata(root)
        print(json.dumps(write_review(root, governance_checks(root), no_event=args.no_event), indent=2))
    elif args.cmd == "fix-queue":
        print(json.dumps(fix_queue_metadata(root), indent=2))
    elif args.cmd == "sanitize-export":
        print(json.dumps(sanitized_export(root, args.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
