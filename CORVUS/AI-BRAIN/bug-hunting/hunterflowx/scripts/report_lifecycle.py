#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DECISION = "judge_reportable"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def json_dump(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=True)


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def lifecycle_path(root: Path) -> Path:
    return root / "data" / "report_lifecycle.json"


def read_events(root: Path) -> list[dict[str, Any]]:
    path = root / "data/events.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_event(root: Path, event: dict[str, Any]) -> None:
    events = read_events(root)
    event.setdefault("id", f"evt-{len(events) + 1:06d}")
    event.setdefault("ts", now())
    event.setdefault("engagement_id", current_engagement_id(root))
    event.setdefault("actor", "report")
    with (root / "data/events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json_dump(event) + "\n")


def load_lifecycle(root: Path) -> dict[str, Any]:
    path = lifecycle_path(root)
    if not path.exists():
        data = {"version": "1.0.0", "reports": []}
        save_lifecycle(root, data)
        return data
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid lifecycle JSON: {exc}") from exc
    data.setdefault("reports", [])
    return data


def save_lifecycle(root: Path, data: dict[str, Any]) -> None:
    path = lifecycle_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() or ch in "._-" else "-" for ch in value.strip())
    while "--" in clean:
        clean = clean.replace("--", "-")
    return clean.strip("-") or "item"


def latest_judgement(root: Path, test_id: str) -> dict[str, Any] | None:
    for event in reversed(read_events(root)):
        if event.get("type") == "evidence_judged" and str(event.get("test_id") or "") == test_id:
            return event
    return None


def proof_gate(root: Path, test_id: str) -> tuple[bool, list[str], dict[str, Any] | None]:
    judgement = latest_judgement(root, test_id)
    missing: list[str] = []
    events = read_events(root)
    if not judgement:
        return False, ["missing evidence_judged event"], None
    if judgement.get("status") != REQUIRED_DECISION:
        missing.append(f"judge status is `{judgement.get('status')}`, not `{REQUIRED_DECISION}`")
    for item in judgement.get("missing") or []:
        missing.append(str(item))
    warnings = [str(item) for item in judgement.get("warnings") or []]
    if any("fresh repro" in item.lower() or "fresh_repro" in item.lower() for item in warnings + missing):
        missing.append("fresh repro gate is not satisfied")
    if not any(
        event.get("type") == "fresh_repro_completed"
        and str(event.get("test_id") or "") == test_id
        and str(event.get("fresh_repro") or "").lower() == "passed"
        for event in events
    ):
        missing.append("fresh repro gate is not satisfied")
    return not missing, missing, judgement


def next_report_id(reports: list[dict[str, Any]]) -> str:
    index = len(reports) + 1
    existing = {str(item.get("id")) for item in reports}
    while f"report-{index:03d}" in existing:
        index += 1
    return f"report-{index:03d}"


def create_draft(root: Path, test_id: str, title: str, finding_id: str = "") -> dict[str, Any]:
    lifecycle = load_lifecycle(root)
    ok, missing, judgement = proof_gate(root, test_id)
    report_id = next_report_id(lifecycle["reports"])
    endpoint = str((judgement or {}).get("endpoint_id") or "-")
    angle = str((judgement or {}).get("angle") or "-")
    title = title or f"{endpoint} {angle}".strip()
    path = root / "reports" / "drafts" / f"{report_id}-{slugify(title)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Bug Bounty Report Draft\n\n"
        f"- Report ID: `{report_id}`\n"
        f"- Test ID: `{test_id}`\n"
        f"- Finding ID: `{finding_id or '-'}`\n"
        f"- Title: {title}\n"
        f"- Endpoint: `{endpoint}`\n"
        f"- Angle: `{angle}`\n"
        f"- Evidence gate: `{'pass' if ok else 'blocked'}`\n\n"
        "## Missing Before Submit\n\n"
        + ("\n".join(f"- {item}" for item in missing) if missing else "- none")
        + "\n\n## Summary\n\nTODO\n\n## Steps To Reproduce\n\nTODO\n\n## Impact\n\nTODO\n\n## Evidence\n\nTODO\n",
        encoding="utf-8",
    )
    record = {
        "id": report_id,
        "test_id": test_id,
        "finding_id": finding_id,
        "title": title,
        "path": str(path.relative_to(root)),
        "status": "draft_blocked" if not ok else "draft_ready",
        "missing_before_submit": missing,
        "created_at": now(),
        "updated_at": now(),
    }
    lifecycle["reports"].append(record)
    save_lifecycle(root, lifecycle)
    write_event(root, {"type": "report_draft_created", "status": "blocked" if not ok else "saved", "report_id": report_id, "test_id": test_id, "report_path": record["path"], "missing": missing})
    return record


def update_status(root: Path, report_id: str, status: str, note: str = "", bounty_value: str = "", retest_date: str = "") -> dict[str, Any]:
    lifecycle = load_lifecycle(root)
    for report in lifecycle["reports"]:
        if report.get("id") != report_id:
            continue
        if status in {"submitted", "triaged", "accepted"}:
            ok, missing, _ = proof_gate(root, str(report.get("test_id") or ""))
            if not ok:
                report["status"] = "submit_blocked"
                report["missing_before_submit"] = missing
                report["updated_at"] = now()
                save_lifecycle(root, lifecycle)
                return report
        report["status"] = status
        report["note"] = note
        if bounty_value:
            report["bounty_value"] = bounty_value
        if retest_date:
            report["retest_date"] = retest_date
        report["updated_at"] = now()
        save_lifecycle(root, lifecycle)
        write_event(root, {"type": "report_status_updated", "status": status, "report_id": report_id, "note": note})
        return report
    raise SystemExit(f"report not found: {report_id}")


def summarize(root: Path) -> dict[str, Any]:
    lifecycle = load_lifecycle(root)
    reports = lifecycle.get("reports") or []
    counts: dict[str, int] = {}
    for item in reports:
        counts[str(item.get("status") or "unknown")] = counts.get(str(item.get("status") or "unknown"), 0) + 1
    return {"version": lifecycle.get("version"), "updated_at": lifecycle.get("updated_at"), "counts": counts, "reports": reports}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage report lifecycle gates.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--root", type=Path, default=Path.cwd())
    draft = sub.add_parser("draft")
    draft.add_argument("--root", type=Path, default=Path.cwd())
    draft.add_argument("--test-id", required=True)
    draft.add_argument("--title", default="")
    draft.add_argument("--finding-id", default="")
    status = sub.add_parser("status")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("report_id")
    status.add_argument("status")
    status.add_argument("--note", default="")
    status.add_argument("--bounty-value", default="")
    status.add_argument("--retest-date", default="")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.cmd == "list":
        print(json.dumps(summarize(root), indent=2))
    elif args.cmd == "draft":
        print(json.dumps(create_draft(root, args.test_id, args.title, args.finding_id), indent=2))
    elif args.cmd == "status":
        print(json.dumps(update_status(root, args.report_id, args.status, args.note, args.bounty_value, args.retest_date), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
