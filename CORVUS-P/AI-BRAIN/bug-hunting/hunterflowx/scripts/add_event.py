#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


EVENT_TYPES = {
    "scope_loaded",
    "asset_added",
    "role_added",
    "rate_limit_loaded",
    "endpoint_discovered",
    "param_discovered",
    "endpoint_seen_runtime",
    "endpoint_verified_reachable",
    "endpoint_role_inferred",
    "source_file_queued",
    "source_file_read",
    "source_flow_linked",
    "attack_surface_mapped",
    "endpoint_angle_planned",
    "endpoint_angle_tested",
    "creative_hypothesis_added",
    "creative_pivot_added",
    "chain_candidate_added",
    "route_source_parsed",
    "js_endpoint_extracted",
    "openapi_endpoint_imported",
    "graphql_operation_imported",
    "mapping_gap_found",
    "source_runtime_diff_added",
    "loop_started",
    "loop_iteration_started",
    "analysis_completed",
    "attack_path_expanded",
    "fingerprint_added",
    "strategy_adjusted",
    "dead_end_recorded",
    "pivot_decision",
    "retest_scheduled",
    "loop_closed",
    "test_planned",
    "test_started",
    "payload_attempted",
    "control_request_sent",
    "evidence_added",
    "gap_found",
    "verdict_set",
    "finding_promoted",
    "finding_demoted",
    "coverage_reviewed",
    "evidence_reviewed",
    "evidence_judged",
    "judge_reviewed",
    "source_completeness_reviewed",
    "endpoint_prioritized",
    "risk_prioritization_reviewed",
    "domain_profile_loaded",
    "domain_check_planned",
    "domain_check_completed",
    "domain_depth_reviewed",
    "ai_governance_reviewed",
    "agent_role_reviewed",
    "autonomy_boundary_set",
    "data_governance_reviewed",
    "sanitized_export_created",
    "attack_path_reviewed",
    "run_queue_task_added",
    "run_queue_task_approved",
    "run_queue_task_started",
    "run_queue_task_finished",
    "run_queue_task_blocked",
    "proxy_history_imported",
    "fresh_repro_completed",
    "report_status_updated",
    "neo4j_action_requested",
    "operator_note_added",
    "report_draft_created",
    "report_ready",
}


def engagement_root(path: Path | None) -> Path:
    return path.resolve() if path else Path.cwd()


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def parse_extra(tokens: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    i = 0
    while i < len(tokens):
        key = tokens[i]
        if not key.startswith("--"):
            raise SystemExit(f"unexpected argument: {key}")
        clean = key[2:].replace("-", "_")
        if i + 1 >= len(tokens) or tokens[i + 1].startswith("--"):
            data[clean] = True
            i += 1
        else:
            data[clean] = tokens[i + 1]
            i += 2
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append one workflow event.")
    parser.add_argument("type", help="Event type")
    parser.add_argument("--root", type=Path, help="Engagement root. Defaults to current directory.")
    parser.add_argument("--event-file", type=Path, help="Read full event JSON from file.")
    parser.add_argument("--actor", default="ai")
    parser.add_argument("--engagement", dest="engagement_id")
    parser.add_argument("--id", dest="event_id")
    args, extra = parser.parse_known_args(argv)

    root = engagement_root(args.root)
    event_type = args.type
    if event_type not in EVENT_TYPES:
        raise SystemExit(f"unknown event type: {event_type}")

    if args.event_file:
        event = json.loads(args.event_file.read_text(encoding="utf-8"))
    else:
        now = datetime.now(timezone.utc).astimezone().isoformat()
        event = {
            "id": args.event_id or "",
            "ts": now,
            "engagement_id": args.engagement_id or current_engagement_id(root),
            "actor": args.actor,
            "type": event_type,
        }
        event.update(parse_extra(extra))

    out = root / "data/events.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            if event.get("id") == "":
                f.seek(0)
                next_num = sum(1 for line in f.read().splitlines() if line.strip()) + 1
                event["id"] = f"evt-{next_num:06d}"

            missing = {"id", "ts", "engagement_id", "actor", "type"} - {key for key, value in event.items() if value}
            if missing:
                raise SystemExit(f"event missing required fields: {sorted(missing)}")

            f.seek(0, 2)
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
            f.flush()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    print(f"wrote {event['id']} {event['type']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
