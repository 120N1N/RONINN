#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Print coverage summary.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--graph", type=Path, help="graph_state.json path")
    args = parser.parse_args()

    graph_path = args.graph or args.root / "data/graph_state.json"
    if not graph_path.exists():
        raise SystemExit(f"missing graph state: {graph_path}")
    state = json.loads(graph_path.read_text(encoding="utf-8"))
    metrics = state.get("metrics", {})
    print(f"engagement: {state.get('engagement_id')}")
    for key in [
        "total_assets",
        "total_endpoints",
        "tested_endpoints",
        "not_tested_endpoints",
        "confirmed_findings",
        "finding_candidates",
        "inconclusive_tests",
        "planned_tests",
        "planned_angles",
        "tested_angles",
        "creative_ideas",
        "evidence_missing",
        "evidence_quality_sufficient",
        "evidence_quality_partial",
        "evidence_quality_incomplete",
        "evidence_quality_avg",
        "judge_tests_total",
        "judge_avg_score",
        "judge_reportable",
        "judge_candidate",
        "judge_needs_evidence",
        "judge_blocked",
        "judge_rejected",
        "source_files_total",
        "source_files_complete",
        "source_files_partial",
        "source_files_incomplete",
        "source_reviews_missing",
        "source_critical_missing",
        "source_completeness_avg",
        "risk_endpoints_ranked",
        "risk_top_score",
        "risk_avg_score",
        "risk_priority_p0",
        "risk_priority_p1",
        "risk_priority_p2",
        "risk_priority_p3",
        "domain_profiles_total",
        "domain_checks_planned",
        "domain_checks_complete",
        "domain_checks_partial",
        "domain_checks_missing",
        "domain_depth_avg",
        "domain_wp_score",
        "domain_onprem_score",
        "domain_mobile_score",
        "open_gaps",
        "active_loops",
        "dead_ends_without_decision",
    ]:
        print(f"{key}: {metrics.get(key, 0)}")

    print("\nopen gaps:")
    for node in state.get("nodes", []):
        if node.get("type") == "gap":
            print(f"- {node.get('id')}: {node.get('label')} [{node.get('status')}]")

    print("\nactive loops:")
    for node in state.get("nodes", []):
        if node.get("type") == "loop" and not str(node.get("status", "")).startswith("closed"):
            props = node.get("properties", {})
            print(f"- {node.get('id')}: {node.get('status')} next={props.get('next_action', '-')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
