#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attack_graph import build_attack_graph
import run_queue


MISSING_WEIGHTS = {
    "js_file": 12,
    "api_route": 5,
    "param": 8,
    "auth_role": 18,
    "test_angle": 15,
    "chaining": 20,
    "evidence": 30,
    "finding": 10,
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
    event.setdefault("actor", "attack_path_review")
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, separators=(",", ":")) + "\n")


def node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(node.get("id")): node for node in graph.get("nodes", [])}


def first_missing(path: dict[str, Any]) -> str:
    missing = path.get("missing_stages") or []
    order = ["js_file", "auth_role", "test_angle", "chaining", "evidence", "finding", "param", "api_route"]
    for stage in order:
        if stage in missing:
            return stage
    return ""


def next_action(stage: str, path: dict[str, Any]) -> tuple[str, list[str], bool, str]:
    endpoint_id = str(path.get("endpoint_id") or "")
    angle_id = str(path.get("angle_id") or "")
    test_id = str(path.get("test_id") or "")
    if stage == "js_file":
        return (
            "complete_source_mapping",
            ["bbf", "source-verify", "--queue-missing"],
            False,
            "Source/JS is not linked to this route; read and link source one file at a time.",
        )
    if stage == "auth_role":
        return (
            "fill_auth_context",
            ["bbf", "event", "endpoint_role_inferred", "--endpoint-id", endpoint_id, "--role", "owned-account-role-tbd", "--status", "needs_context"],
            False,
            "Auth role is unknown; add owned account role/session context before execution.",
        )
    if stage == "test_angle":
        return (
            "create_angle_plan",
            ["bbf", "angle-plan", "full", "--endpoint-id", endpoint_id],
            False,
            "No durable angle exists for this route; generate full multi-angle coverage.",
        )
    if stage == "chaining":
        return (
            "review_chain_potential",
            ["bbf", "event", "chain_candidate_added", "--endpoint-id", endpoint_id, "--angle-id", angle_id, "--status", "needs_chain_review"],
            False,
            "Attack path has not been chained; review source/runtime pivots and impact path.",
        )
    if stage == "evidence":
        return (
            "execute_or_import_evidence",
            ["bbf", "angle-exec", "--endpoint-id", endpoint_id, "--allow-active"],
            True,
            "Evidence missing; execute approved test or import Burp/Caido history.",
        )
    if stage == "finding":
        command = ["bbf", "judge", "--test-id", test_id] if test_id else ["bbf", "judge", "--endpoint-id", endpoint_id]
        return (
            "judge_reportability",
            command,
            False,
            "Path has evidence but no reportable finding; run semantic judge and fresh repro if needed.",
        )
    return (
        "review_path",
        ["bbf", "coverage"],
        False,
        "Review this path manually and record the next concrete event.",
    )


def priority(score: float) -> str:
    if score >= 70:
        return "P0"
    if score >= 50:
        return "P1"
    if score >= 30:
        return "P2"
    return "P3"


def review(root: Path, limit: int = 25) -> dict[str, Any]:
    graph = build_attack_graph(root)
    nodes = node_map(graph)
    records: list[dict[str, Any]] = []
    for path in graph.get("paths", []):
        missing = [str(item) for item in path.get("missing_stages") or []]
        missing_score = sum(MISSING_WEIGHTS.get(stage, 5) for stage in missing)
        completeness = float(path.get("completeness") or 0)
        score = min(100.0, round((100 - completeness) + missing_score, 1))
        stage = first_missing(path)
        action, command, active, reason = next_action(stage, path)
        node_labels = {}
        for key, node_id in (path.get("nodes") or {}).items():
            node = nodes.get(str(node_id), {})
            node_labels[key] = {
                "id": node_id,
                "label": node.get("label", node_id),
                "status": node.get("status", ""),
            }
        records.append(
            {
                "path_id": path.get("id"),
                "priority": priority(score),
                "score": score,
                "completeness": completeness,
                "endpoint_id": path.get("endpoint_id"),
                "angle_id": path.get("angle_id"),
                "test_id": path.get("test_id"),
                "status": path.get("status"),
                "missing_stages": missing,
                "first_missing_stage": stage,
                "next_action": action,
                "queue_command": command,
                "active": active,
                "blocked_reason": reason if active else "",
                "reason": reason,
                "nodes": node_labels,
            }
        )
    records.sort(key=lambda item: ({"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(str(item["priority"]), 9), -float(item["score"])))
    selected = records[:limit]
    result = {
        "version": "1.0.0",
        "generated_at": now(),
        "engagement_id": current_engagement_id(root),
        "total_paths": len(records),
        "limit": limit,
        "priorities": selected,
        "summary": {
            "p0": sum(1 for item in selected if item["priority"] == "P0"),
            "p1": sum(1 for item in selected if item["priority"] == "P1"),
            "needs_source": sum(1 for item in selected if item["first_missing_stage"] == "js_file"),
            "needs_auth": sum(1 for item in selected if item["first_missing_stage"] == "auth_role"),
            "needs_chain": sum(1 for item in selected if item["first_missing_stage"] == "chaining"),
            "needs_evidence": sum(1 for item in selected if item["first_missing_stage"] == "evidence"),
            "needs_judge": sum(1 for item in selected if item["first_missing_stage"] == "finding"),
        },
    }
    return result


def write_outputs(root: Path, result: dict[str, Any], no_event: bool = False) -> dict[str, Any]:
    data_path = root / "data/attack_path_priorities.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_path = root / "output/attack-path-review.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Attack Path Review",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Engagement: {result['engagement_id']}",
        f"- Total paths: {result['total_paths']}",
        "",
        "## Summary",
        "",
    ]
    for key, value in result["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Prioritized Paths", ""])
    for item in result["priorities"]:
        endpoint_label = item["nodes"].get("api_route", {}).get("label", item["endpoint_id"]) if isinstance(item.get("nodes"), dict) else item["endpoint_id"]
        lines.extend(
            [
                f"### {item['priority']} - {endpoint_label}",
                "",
                f"- Path: {item['path_id']}",
                f"- Score: {item['score']}",
                f"- Completeness: {item['completeness']}",
                f"- Missing: {', '.join(item['missing_stages']) or '-'}",
                f"- Next action: {item['next_action']}",
                f"- Reason: {item['reason']}",
                f"- Command: `{' '.join(item['queue_command'])}`",
                "",
            ]
        )
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    result["report_path"] = str(report_path.relative_to(root))
    if not no_event:
        write_event(
            root,
            {
                "type": "attack_path_reviewed",
                "status": "reviewed",
                "report_path": result["report_path"],
                "total_paths": result["total_paths"],
                **result["summary"],
            },
        )
    return result


def queue_actions(root: Path, result: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    queued: list[dict[str, Any]] = []
    for item in result.get("priorities", [])[:limit]:
        command = [str(part) for part in item.get("queue_command") or []]
        if not command:
            continue
        task = run_queue.add_task(
            root,
            stage=str(item.get("next_action") or "attack-path-review"),
            label=f"{item.get('priority')} {item.get('next_action')} for {item.get('endpoint_id')}",
            command=command,
            active=bool(item.get("active")),
            blocked_reason=str(item.get("blocked_reason") or ""),
            source="attack-path-review",
            meta={
                "path_id": item.get("path_id"),
                "endpoint_id": item.get("endpoint_id"),
                "angle_id": item.get("angle_id"),
                "priority": item.get("priority"),
                "score": item.get("score"),
            },
        )
        queued.append(task)
    return queued


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rank attack paths and create concrete next actions.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--queue", action="store_true", help="Queue next actions for top paths.")
    parser.add_argument("--queue-limit", type=int, default=5)
    parser.add_argument("--no-event", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = write_outputs(root, review(root, args.limit), no_event=args.no_event)
    if args.queue:
        result["queued_tasks"] = queue_actions(root, result, args.queue_limit)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
