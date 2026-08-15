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
BBF = str(ROOT / "bin" / "bbf")
ACTIVE_STAGES = {"angle-exec", "fresh-repro", "active-test", "execute_or_import_evidence"}
STAGE_AGENT_ROLES = {
    "recon": "recon_agent",
    "source-read": "source_mapper",
    "map-endpoint": "recon_agent",
    "angle-plan": "attack_path_planner",
    "angle-exec": "executor",
    "evidence-score": "validator",
    "judge": "evidence_judge",
    "fresh-repro": "validator",
    "report": "report_reviewer",
    "governance": "safety_governor",
    "attack-path-review": "attack_path_planner",
    "complete_source_mapping": "source_mapper",
    "fill_auth_context": "coordinator",
    "create_angle_plan": "attack_path_planner",
    "review_chain_potential": "attack_path_planner",
    "execute_or_import_evidence": "executor",
    "judge_reportability": "evidence_judge",
}


def default_autonomy(stage: str, active: bool, blocked_reason: str = "") -> str:
    if "out-of-scope" in blocked_reason.lower() or "forbidden" in blocked_reason.lower():
        return "hard_deny"
    if active or stage in ACTIVE_STAGES:
        return "active_requires_approval"
    return "passive_auto"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def queue_path(root: Path) -> Path:
    return root / "data" / "run_queue.json"


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}/{parts[idx + 2]}"
    return root.name


def json_dump(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=True)


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
    event.setdefault("engagement_id", current_engagement_id(root).replace("/", "-"))
    event.setdefault("actor", "queue")
    with path.open("a", encoding="utf-8") as f:
        f.write(json_dump(event) + "\n")


def load_queue(root: Path) -> dict[str, Any]:
    path = queue_path(root)
    if not path.exists():
        data = {"version": "1.0.0", "engagement_id": current_engagement_id(root), "tasks": []}
        save_queue(root, data)
        return data
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid queue JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: queue must be a JSON object")
    data.setdefault("tasks", [])
    data.setdefault("version", "1.0.0")
    data.setdefault("engagement_id", current_engagement_id(root))
    return data


def save_queue(root: Path, data: dict[str, Any]) -> None:
    path = queue_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def next_task_id(tasks: list[dict[str, Any]], stage: str) -> str:
    prefix = "task-" + "".join(ch if ch.isalnum() else "-" for ch in stage.lower()).strip("-")
    existing = {str(task.get("id")) for task in tasks}
    index = 1
    while f"{prefix}-{index:03d}" in existing:
        index += 1
    return f"{prefix}-{index:03d}"


def normalize_command(command: list[str]) -> list[str]:
    if command and command[0] == "bbf":
        return [BBF, *command[1:]]
    return command


def add_task(
    root: Path,
    *,
    stage: str,
    label: str,
    command: list[str],
    active: bool = False,
    blocked_reason: str = "",
    source: str = "manual",
    meta: dict[str, Any] | None = None,
    autonomy_level: str = "",
    agent_role: str = "",
    validation_gate: str = "",
) -> dict[str, Any]:
    queue = load_queue(root)
    tasks = queue["tasks"]
    approval = "pending" if active else "not_required"
    status = "blocked" if blocked_reason else "queued"
    task = {
        "id": next_task_id(tasks, stage),
        "stage": stage,
        "label": label,
        "command": command,
        "active": active,
        "autonomy_level": autonomy_level or default_autonomy(stage, active, blocked_reason),
        "agent_role": agent_role or STAGE_AGENT_ROLES.get(stage, "coordinator"),
        "validation_gate": validation_gate or ("operator_approval" if active else "event_ledger"),
        "approval": approval,
        "status": status,
        "attempts": 0,
        "blocked_reason": blocked_reason,
        "created_at": now(),
        "updated_at": now(),
        "source": source,
        "meta": meta or {},
    }
    tasks.append(task)
    save_queue(root, queue)
    write_event(
        root,
        {
            "type": "run_queue_task_added",
            "status": status,
            "task_id": task["id"],
            "stage": stage,
            "label": label,
            "active": active,
            "approval": approval,
            "autonomy_level": task["autonomy_level"],
            "agent_role": task["agent_role"],
            "validation_gate": task["validation_gate"],
            "blocked_reason": blocked_reason,
        },
    )
    return task


def seed_queue(root: Path) -> dict[str, Any]:
    queue = load_queue(root)
    defaults = [
        ("governance", "Review AI autonomy, safety, data governance, and validation gates", ["bbf", "ai-governance", "check"], False, "", "passive_auto", "safety_governor", "governance_review"),
        ("recon", "Review current graph and coverage", ["bbf", "coverage"], False, ""),
        ("source-read", "Verify one-file-at-a-time source coverage", ["bbf", "source-verify", "--queue-missing"], False, ""),
        ("map-endpoint", "Prioritize mapped endpoints", ["bbf", "risk-prioritize", "--limit", "25"], False, ""),
        ("attack-path-review", "Rank source-to-finding attack paths and queue next pivots", ["bbf", "attack-path-review", "--limit", "25"], False, "", "passive_auto", "attack_path_planner", "attack_path_review"),
        ("angle-plan", "Generate full multi-angle plan for selected endpoint", ["bbf", "angle-plan", "full"], False, "select endpoint/method/path before running"),
        ("angle-exec", "Execute approved endpoint angle through Caido", ["bbf", "angle-exec", "--transport", "caido", "--allow-active"], True, "requires endpoint, headers, scope policy, and explicit approval"),
        ("evidence-score", "Score all available evidence packages", ["bbf", "evidence-score", "--all"], False, ""),
        ("judge", "Judge evidence reportability", ["bbf", "judge", "--all"], False, ""),
        ("fresh-repro", "Fresh repro gate for candidate/reportable tests", ["bbf", "fresh-repro"], True, "requires test id and fresh auth headers"),
        ("report", "Review report lifecycle and missing proof", ["bbf", "report-lifecycle", "list"], False, ""),
    ]
    existing = {(str(task.get("stage") or ""), str(task.get("label") or "")) for task in queue.get("tasks") or []}
    for item in defaults:
        stage, label, command, active, blocked = item[:5]
        if (stage, label) in existing:
            continue
        autonomy = item[5] if len(item) > 5 else ""
        role = item[6] if len(item) > 6 else ""
        gate = item[7] if len(item) > 7 else ""
        add_task(root, stage=stage, label=label, command=command, active=active, blocked_reason=blocked, source="seed", autonomy_level=autonomy, agent_role=role, validation_gate=gate)
    return load_queue(root)


def find_task(queue: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in queue.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise SystemExit(f"task not found: {task_id}")


def approve_task(root: Path, task_id: str) -> dict[str, Any]:
    queue = load_queue(root)
    task = find_task(queue, task_id)
    task["approval"] = "approved"
    if task.get("status") == "blocked" and str(task.get("blocked_reason") or "").startswith("requires"):
        task["status"] = "queued"
        task["blocked_reason"] = ""
    task["updated_at"] = now()
    save_queue(root, queue)
    write_event(root, {"type": "run_queue_task_approved", "status": "queued", "task_id": task_id, "stage": task.get("stage")})
    return task


def block_task(root: Path, task_id: str, reason: str) -> dict[str, Any]:
    queue = load_queue(root)
    task = find_task(queue, task_id)
    task["status"] = "blocked"
    task["blocked_reason"] = reason
    task["updated_at"] = now()
    save_queue(root, queue)
    write_event(root, {"type": "run_queue_task_blocked", "status": "blocked", "task_id": task_id, "stage": task.get("stage"), "reason": reason})
    return task


def runnable(task: dict[str, Any]) -> tuple[bool, str]:
    if task.get("autonomy_level") == "hard_deny":
        return False, "task autonomy_level is hard_deny"
    if task.get("status") not in {"queued", "failed"}:
        return False, f"status is {task.get('status')}"
    if task.get("autonomy_level") == "active_requires_approval" and task.get("approval") != "approved":
        return False, "active task requires approval"
    if task.get("blocked_reason"):
        return False, str(task.get("blocked_reason"))
    if not task.get("command"):
        return False, "missing command"
    return True, ""


def run_task(root: Path, task_id: str) -> dict[str, Any]:
    queue = load_queue(root)
    task = find_task(queue, task_id)
    ok, reason = runnable(task)
    if not ok:
        task["status"] = "blocked"
        task["blocked_reason"] = reason
        task["updated_at"] = now()
        save_queue(root, queue)
        return task

    task["status"] = "running"
    task["attempts"] = int(task.get("attempts") or 0) + 1
    task["started_at"] = now()
    task["updated_at"] = now()
    save_queue(root, queue)
    write_event(root, {"type": "run_queue_task_started", "status": "test_attempted", "task_id": task_id, "stage": task.get("stage")})

    command = normalize_command([str(item) for item in task.get("command") or []])
    try:
        proc = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=int(task.get("timeout") or 600))
        output = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        task["returncode"] = proc.returncode
        task["last_output"] = output[-8000:]
        task["status"] = "done" if proc.returncode == 0 else "failed"
        task["blocked_reason"] = "" if proc.returncode == 0 else f"command exited {proc.returncode}"
    except subprocess.TimeoutExpired as exc:
        task["returncode"] = None
        task["last_output"] = (exc.stdout or "") + (exc.stderr or "")
        task["status"] = "failed"
        task["blocked_reason"] = "command timed out"

    task["finished_at"] = now()
    task["updated_at"] = now()
    save_queue(root, queue)
    write_event(
        root,
        {
            "type": "run_queue_task_finished",
            "status": "closed" if task["status"] == "done" else "blocked",
            "task_id": task_id,
            "stage": task.get("stage"),
            "returncode": task.get("returncode"),
            "queue_status": task["status"],
            "blocked_reason": task.get("blocked_reason", ""),
        },
    )
    return task


def run_next(root: Path) -> dict[str, Any] | None:
    queue = load_queue(root)
    for task in queue.get("tasks", []):
        ok, _ = runnable(task)
        if ok:
            return run_task(root, str(task["id"]))
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the dashboard run queue / command center.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ["list", "seed", "run-next"]:
        p = sub.add_parser(name)
        p.add_argument("--root", type=Path, default=Path.cwd())
    add = sub.add_parser("add")
    add.add_argument("--root", type=Path, default=Path.cwd())
    add.add_argument("--stage", required=True)
    add.add_argument("--label", required=True)
    add.add_argument("--active", action="store_true")
    add.add_argument("--blocked-reason", default="")
    add.add_argument("--autonomy-level", default="")
    add.add_argument("--agent-role", default="")
    add.add_argument("--validation-gate", default="")
    add.add_argument("command", nargs=argparse.REMAINDER)
    approve = sub.add_parser("approve")
    approve.add_argument("--root", type=Path, default=Path.cwd())
    approve.add_argument("task_id")
    block = sub.add_parser("block")
    block.add_argument("--root", type=Path, default=Path.cwd())
    block.add_argument("task_id")
    block.add_argument("reason")
    run = sub.add_parser("run")
    run.add_argument("--root", type=Path, default=Path.cwd())
    run.add_argument("task_id")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "list":
        print(json.dumps(load_queue(root), indent=2))
    elif args.cmd == "seed":
        print(json.dumps(seed_queue(root), indent=2))
    elif args.cmd == "add":
        command = [item for item in args.command if item != "--"]
        if not command:
            raise SystemExit("add requires command after --")
        print(json.dumps(add_task(root, stage=args.stage, label=args.label, command=command, active=args.active, blocked_reason=args.blocked_reason, autonomy_level=args.autonomy_level, agent_role=args.agent_role, validation_gate=args.validation_gate), indent=2))
    elif args.cmd == "approve":
        print(json.dumps(approve_task(root, args.task_id), indent=2))
    elif args.cmd == "block":
        print(json.dumps(block_task(root, args.task_id, args.reason), indent=2))
    elif args.cmd == "run":
        print(json.dumps(run_task(root, args.task_id), indent=2))
    elif args.cmd == "run-next":
        task = run_next(root)
        print(json.dumps(task or {"status": "empty", "message": "no runnable task"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
