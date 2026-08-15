#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


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
    event.setdefault("actor", "fresh-repro")
    with (root / "data/events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json_dump(event) + "\n")


def latest_test_event(events: list[dict[str, Any]], test_id: str) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("type") == "endpoint_angle_tested" and str(event.get("test_id") or "") == test_id:
            return event
    return None


def mark(root: Path, test_id: str, passed: bool, evidence_path: str, reason: str) -> dict[str, Any]:
    event = {
        "type": "fresh_repro_completed",
        "status": "closed" if passed else "blocked",
        "test_id": test_id,
        "fresh_repro": "passed" if passed else "failed",
        "evidence_path": evidence_path,
        "reason": reason,
    }
    write_event(root, event)
    return event


def run_replay(root: Path, test_id: str, headers_file: Path | None, alt_headers_file: Path | None, replace: list[str], allow_active: bool) -> dict[str, Any]:
    events = read_events(root)
    original = latest_test_event(events, test_id)
    if not original:
        return mark(root, test_id, False, "", "missing original endpoint_angle_tested event")
    if not headers_file:
        return mark(root, test_id, False, "", "fresh repro requires --headers-file for a fresh session/account")
    if not allow_active:
        return mark(root, test_id, False, "", "fresh repro refused without --allow-active")
    cmd = [
        sys.executable,
        str(ROOT / "scripts/angle_exec.py"),
        "--root",
        str(root),
        "--endpoint-id",
        str(original.get("endpoint_id") or ""),
        "--angle",
        str(original.get("angle") or ""),
        "--method",
        str(original.get("method") or "GET"),
        "--url",
        str(original.get("target") or ""),
        "--transport",
        str(original.get("transport") or "caido"),
        "--headers-file",
        str(headers_file),
        "--rerun",
        "--allow-active",
    ]
    if original.get("proxy"):
        cmd.extend(["--proxy", str(original.get("proxy"))])
    if alt_headers_file:
        cmd.extend(["--alt-headers-file", str(alt_headers_file)])
    for item in replace:
        cmd.extend(["--replace", item])
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    log_dir = root / "evidence/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"fresh-repro-{test_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    log_path.write_text((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return mark(root, test_id, proc.returncode == 0, str(log_path.relative_to(root)), "fresh replay completed" if proc.returncode == 0 else f"fresh replay failed with exit {proc.returncode}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fresh replay gate before reportable judgement.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--test-id", default="")
    parser.add_argument("--headers-file", type=Path)
    parser.add_argument("--alt-headers-file", type=Path)
    parser.add_argument("--replace", action="append", default=[])
    parser.add_argument("--allow-active", action="store_true")
    parser.add_argument("--mark-pass", action="store_true")
    parser.add_argument("--mark-fail", action="store_true")
    parser.add_argument("--evidence-path", default="")
    parser.add_argument("--reason", default="")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not args.test_id:
        raise SystemExit("--test-id is required")
    if args.mark_pass or args.mark_fail:
        print(json.dumps(mark(root, args.test_id, args.mark_pass, args.evidence_path, args.reason or "manual fresh repro mark"), indent=2))
        return 0
    result = run_replay(root, args.test_id, args.headers_file, args.alt_headers_file, args.replace, args.allow_active)
    print(json.dumps(result, indent=2))
    return 0 if result.get("fresh_repro") == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
