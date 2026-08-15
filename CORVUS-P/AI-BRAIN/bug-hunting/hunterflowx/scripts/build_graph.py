#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_COLOR = {
    "not_tested": "gray",
    "mapped_only": "gray",
    "test_attempted": "yellow",
    "inconclusive": "yellow",
    "tested_secure": "green",
    "finding_candidate": "orange",
    "confirmed": "red",
    "out_of_scope": "black",
    "by_design": "black",
    "blocked": "black",
    "verified_reachable": "purple",
    "mapped_runtime": "purple",
    "mapped_static": "blue",
    "mapped_js": "blue",
    "running": "blue",
    "queued": "blue",
    "saved": "green",
    "closed": "green",
    "pivoting": "yellow",
    "evidence_sufficient": "green",
    "evidence_partial": "yellow",
    "evidence_incomplete": "red",
    "judge_reportable": "green",
    "judge_candidate": "orange",
    "judge_needs_evidence": "yellow",
    "judge_blocked": "black",
    "judge_rejected": "red",
    "source_complete": "green",
    "source_partial": "yellow",
    "source_incomplete": "red",
    "priority_critical": "red",
    "priority_high": "orange",
    "priority_medium": "yellow",
    "priority_low": "gray",
    "domain_planned": "blue",
    "domain_complete": "green",
    "domain_partial": "yellow",
    "domain_incomplete": "red",
    "done": "green",
    "failed": "red",
    "draft_ready": "green",
    "draft_blocked": "yellow",
    "submit_blocked": "red",
    "submitted": "blue",
    "triaged": "yellow",
    "accepted": "green",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return records


def add_node(nodes: dict[str, dict[str, Any]], node_id: str, node_type: str, label: str, **props: Any) -> None:
    if not node_id:
        return
    existing = nodes.get(node_id, {})
    properties = existing.get("properties", {})
    properties.update({k: v for k, v in props.items() if v is not None})
    status = props.get("status") or existing.get("status") or properties.get("status") or "mapped_only"
    nodes[node_id] = {
        "id": node_id,
        "type": node_type,
        "label": label,
        "status": status,
        "color": STATUS_COLOR.get(str(status), "gray"),
        "properties": properties,
    }


def add_edge(edges: dict[str, dict[str, Any]], source: str, target: str, edge_type: str, label: str = "") -> None:
    if not source or not target:
        return
    edge_id = f"edge-{edge_type}-{source}-{target}"
    edges[edge_id] = {"id": edge_id, "source": source, "target": target, "type": edge_type, "label": label}


def event_props(event: dict[str, Any], *reserved: str) -> dict[str, Any]:
    return {k: v for k, v in event.items() if k not in reserved}


def build(events: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    endpoint_tests: dict[str, set[str]] = {}
    test_status: dict[str, str] = {}
    test_evidence: dict[str, set[str]] = {}
    angle_status: dict[str, str] = {}
    evidence_review_status: dict[str, str] = {}
    evidence_review_score: dict[str, int] = {}
    evidence_judge_status: dict[str, str] = {}
    evidence_judge_score: dict[str, int] = {}
    latest_judge_metrics: dict[str, Any] = {}
    latest_source_metrics: dict[str, Any] = {}
    latest_risk_metrics: dict[str, Any] = {}
    latest_domain_metrics: dict[str, Any] = {}
    queue_status: dict[str, str] = {}
    report_status: dict[str, str] = {}
    domain_profiles: set[str] = set()
    domain_check_status: dict[str, str] = {}
    creative_nodes: set[str] = set()
    loop_decisions: dict[str, set[str]] = {}
    dead_ends: set[str] = set()
    engagement_id = "unknown"

    for event in events:
        engagement_id = str(event.get("engagement_id") or engagement_id)
        typ = event.get("type")
        asset_id = str(event.get("asset_id") or "")
        endpoint_id = str(event.get("endpoint_id") or "")
        test_id = str(event.get("test_id") or "")
        loop_id = str(event.get("loop_id") or "")

        if typ == "asset_added":
            label = str(event.get("host") or event.get("asset") or asset_id)
            status = "mapped_only"
            if event.get("scope_status") == "out_of_scope":
                status = "out_of_scope"
            elif event.get("testability") == "blocked":
                status = "blocked"
            add_node(nodes, asset_id, "asset", label, status=status, **event_props(event, "status"))

        elif typ in {
            "endpoint_discovered",
            "endpoint_seen_runtime",
            "endpoint_verified_reachable",
            "openapi_endpoint_imported",
            "graphql_operation_imported",
        }:
            method = event.get("method", "")
            path = event.get("path", endpoint_id)
            status = {
                "endpoint_discovered": "mapped_only",
                "endpoint_seen_runtime": "mapped_runtime",
                "endpoint_verified_reachable": "verified_reachable",
                "openapi_endpoint_imported": "mapped_static",
                "graphql_operation_imported": "mapped_static",
            }[typ]
            add_node(nodes, endpoint_id, "endpoint", f"{method} {path}".strip(), status=status, **event_props(event, "status"))
            if asset_id:
                add_edge(edges, asset_id, endpoint_id, "asset_has_endpoint", "hosts")

        elif typ == "js_endpoint_extracted":
            js_id = str(event.get("js_id") or event.get("script_url") or f"js-{event.get('id')}")
            label = str(event.get("script_url") or event.get("page_url") or js_id)
            add_node(nodes, js_id, "js", label, status="mapped_js", **event_props(event, "status"))
            if asset_id:
                add_edge(edges, asset_id, js_id, "asset_has_js", "script")

        elif typ == "route_source_parsed":
            source_id = str(event.get("source_id") or event.get("source_file") or f"source-{event.get('id')}")
            add_node(nodes, source_id, "source", source_id, status="mapped_static", **event_props(event, "status"))
            if endpoint_id:
                add_edge(edges, source_id, endpoint_id, "source_has_endpoint", "route")

        elif typ in {"source_file_queued", "source_file_read"}:
            source_id = str(event.get("source_id") or event.get("file_id") or event.get("source_file") or f"source-{event.get('id')}")
            label = str(event.get("source_file") or event.get("path") or source_id)
            status = str(event.get("status") or ("queued" if typ == "source_file_queued" else "mapped_static"))
            add_node(nodes, source_id, "source", label, status=status, **event_props(event, "status"))
            if asset_id:
                add_edge(edges, asset_id, source_id, "asset_has_source", "source")

        elif typ == "source_flow_linked":
            source_id = str(event.get("source_id") or event.get("file_id") or event.get("source_file") or f"source-{event.get('id')}")
            flow_id = str(event.get("flow_id") or f"flow-{event.get('id')}")
            label = str(event.get("flow") or event.get("handler") or flow_id)
            add_node(nodes, source_id, "source", str(event.get("source_file") or source_id), status="mapped_static", **event_props(event, "status"))
            add_node(nodes, flow_id, "flow", label, status="mapped_static", **event_props(event, "status"))
            add_edge(edges, source_id, flow_id, "source_has_flow", "flow")
            if endpoint_id:
                add_edge(edges, flow_id, endpoint_id, "flow_has_endpoint", "endpoint")

        elif typ == "attack_surface_mapped":
            surface_id = str(event.get("surface_id") or f"surface-{event.get('id')}")
            label = str(event.get("surface") or event.get("attack_surface") or event.get("reason") or surface_id)
            add_node(nodes, surface_id, "attack_surface", label, status=str(event.get("status") or "mapped_only"), **event_props(event, "status"))
            add_edge(edges, endpoint_id or asset_id or str(event.get("source_id") or ""), surface_id, "has_attack_surface", "surface")

        elif typ in {"endpoint_angle_planned", "endpoint_angle_tested"}:
            angle = str(event.get("angle") or event.get("bug_class") or "angle")
            angle_id = str(event.get("angle_id") or f"angle-{endpoint_id}-{angle}".replace("/", "-"))
            status = str(event.get("status") or ("queued" if typ == "endpoint_angle_planned" else "test_attempted"))
            add_node(nodes, angle_id, "angle", angle, status=status, **event_props(event, "status"))
            if endpoint_id:
                add_edge(edges, endpoint_id, angle_id, "endpoint_has_angle", angle)
                if typ == "endpoint_angle_tested":
                    endpoint_tests.setdefault(endpoint_id, set()).add(angle_id)
            angle_status[angle_id] = status

        elif typ in {"creative_hypothesis_added", "creative_pivot_added"}:
            creative_id = str(event.get("hypothesis_id") or event.get("pivot_id") or f"creative-{event.get('id')}")
            label = str(event.get("hypothesis") or event.get("pivot") or event.get("idea") or event.get("reason") or creative_id)
            node_type = "hypothesis" if typ == "creative_hypothesis_added" else "pivot"
            status = str(event.get("status") or "queued")
            creative_nodes.add(creative_id)
            add_node(nodes, creative_id, node_type, label, status=status, **event_props(event, "status"))
            add_edge(edges, endpoint_id or asset_id or loop_id or str(event.get("source_id") or ""), creative_id, "has_creative_idea", "creative")

        elif typ == "param_discovered":
            param = str(event.get("param") or event.get("name") or "param")
            param_id = str(event.get("param_id") or f"param-{endpoint_id}-{param}".replace("/", "-"))
            add_node(nodes, param_id, "parameter", param, **event)
            add_edge(edges, endpoint_id, param_id, "endpoint_has_param", str(event.get("param_location") or "param"))

        elif typ in {"loop_started", "loop_iteration_started", "loop_closed"}:
            status = str(event.get("loop_state") or ("closed" if typ == "loop_closed" else "running"))
            add_node(nodes, loop_id, "loop", loop_id, status=status, **event_props(event, "status"))
            add_edge(edges, loop_id, endpoint_id, "loop_has_endpoint", "tracks")

        elif typ in {"test_planned", "test_started", "payload_attempted", "control_request_sent"}:
            status = str(event.get("status") or ("queued" if typ == "test_planned" else "test_attempted"))
            add_node(nodes, test_id, "test", test_id, status=status, **event_props(event, "status"))
            if endpoint_id:
                if typ != "test_planned":
                    endpoint_tests.setdefault(endpoint_id, set()).add(test_id)
                add_edge(edges, endpoint_id, test_id, "endpoint_has_test", str(event.get("bug_class") or "test"))
            if loop_id:
                add_edge(edges, loop_id, test_id, "loop_has_test", "test")
            test_status.setdefault(test_id, status)

        elif typ == "evidence_added":
            evidence_id = str(event.get("evidence_id") or event.get("evidence_path") or f"ev-{test_id}")
            add_node(nodes, evidence_id, "evidence", evidence_id, status="saved", **event_props(event, "status"))
            if test_id:
                add_edge(edges, test_id, evidence_id, "test_has_evidence", str(event.get("evidence_type") or "evidence"))
                test_evidence.setdefault(test_id, set()).add(evidence_id)
            elif endpoint_id:
                add_edge(edges, endpoint_id, evidence_id, "endpoint_has_evidence", str(event.get("evidence_type") or "evidence"))

        elif typ == "evidence_reviewed":
            status = str(event.get("status") or "evidence_incomplete")
            review_id = str(event.get("review_id") or f"review-{test_id}")
            label = str(event.get("review_path") or f"{test_id} evidence review")
            add_node(nodes, review_id, "evidence_review", label, status=status, **event_props(event, "status"))
            if test_id:
                add_edge(edges, test_id, review_id, "test_has_evidence_review", status)
            if endpoint_id:
                add_edge(edges, endpoint_id, review_id, "endpoint_has_evidence_review", status)
            evidence_review_status[test_id or review_id] = status
            try:
                evidence_review_score[test_id or review_id] = int(event.get("score") or 0)
            except (TypeError, ValueError):
                evidence_review_score[test_id or review_id] = 0

        elif typ == "evidence_judged":
            status = str(event.get("status") or "judge_needs_evidence")
            judge_id = str(event.get("judge_id") or f"judge-{test_id}-{event.get('id')}")
            label = str(event.get("review_path") or f"{test_id} evidence judge")
            add_node(nodes, judge_id, "evidence_judge", label, status=status, **event_props(event, "status"))
            if test_id:
                add_edge(edges, test_id, judge_id, "test_has_evidence_judge", status)
            if endpoint_id:
                add_edge(edges, endpoint_id, judge_id, "endpoint_has_evidence_judge", status)
            evidence_judge_status[test_id or judge_id] = status
            try:
                evidence_judge_score[test_id or judge_id] = int(event.get("score") or 0)
            except (TypeError, ValueError):
                evidence_judge_score[test_id or judge_id] = 0

        elif typ in {"proxy_history_imported", "fresh_repro_completed"}:
            node_id = str(event.get("evidence_path") or event.get("source_request_id") or f"{typ}-{event.get('id')}")
            status = str(event.get("status") or "saved")
            label = str(event.get("source") or event.get("fresh_repro") or typ)
            add_node(nodes, node_id, "evidence", label, status=status, **event_props(event, "status"))
            if test_id:
                add_edge(edges, test_id, node_id, "test_has_evidence", typ)
                test_evidence.setdefault(test_id, set()).add(node_id)
            if endpoint_id:
                add_edge(edges, endpoint_id, node_id, "endpoint_has_evidence", typ)

        elif typ in {"run_queue_task_added", "run_queue_task_approved", "run_queue_task_started", "run_queue_task_finished", "run_queue_task_blocked"}:
            task_id = str(event.get("task_id") or f"task-{event.get('id')}")
            status = str(event.get("queue_status") or event.get("status") or "queued")
            label = str(event.get("label") or event.get("stage") or task_id)
            add_node(nodes, task_id, "queue_task", label, status=status, **event_props(event, "status", "label"))
            queue_status[task_id] = status

        elif typ in {"report_draft_created", "report_ready", "report_status_updated"}:
            report_id = str(event.get("report_id") or event.get("report_path") or f"report-{event.get('id')}")
            status = str(event.get("status") or "draft_ready")
            label = str(event.get("report_path") or event.get("title") or report_id)
            add_node(nodes, report_id, "report", label, status=status, **event_props(event, "status", "label"))
            if test_id:
                add_edge(edges, test_id, report_id, "test_has_report", status)
            report_status[report_id] = status

        elif typ == "judge_reviewed":
            review_id = str(event.get("review_id") or f"judge-review-{event.get('id')}")
            label = str(event.get("summary_path") or "judge review")
            add_node(nodes, review_id, "judge_review", label, status=str(event.get("status") or "saved"), **event_props(event, "status"))
            latest_judge_metrics = {
                "judge_tests_total": event.get("tests_judged", 0),
                "judge_avg_score": event.get("judge_avg_score", 0),
                "judge_reportable": event.get("judge_reportable", 0),
                "judge_candidate": event.get("judge_candidate", 0),
                "judge_needs_evidence": event.get("judge_needs_evidence", 0),
                "judge_blocked": event.get("judge_blocked", 0),
                "judge_rejected": event.get("judge_rejected", 0),
            }

        elif typ == "source_completeness_reviewed":
            status = str(event.get("status") or "source_incomplete")
            review_id = str(event.get("review_id") or f"source-completeness-{event.get('id')}")
            label = str(event.get("review_path") or "source completeness review")
            add_node(nodes, review_id, "source_completeness", label, status=status, **event_props(event, "status"))
            source_root = str(event.get("source_root") or "")
            if source_root:
                source_root_id = f"source-root-{hashlib.sha1(source_root.encode('utf-8')).hexdigest()[:8]}"
                add_node(nodes, source_root_id, "source_root", source_root, status=status, source_root=source_root)
                add_edge(edges, source_root_id, review_id, "source_root_has_completeness_review", status)
            latest_source_metrics = {
                "source_files_total": event.get("files_total", 0),
                "source_files_complete": event.get("files_complete", 0),
                "source_files_partial": event.get("files_partial", 0),
                "source_files_incomplete": event.get("files_incomplete", 0),
                "source_reviews_missing": event.get("reviews_missing", 0),
                "source_critical_missing": event.get("critical_missing", 0),
                "source_completeness_avg": event.get("score", 0),
            }

        elif typ == "endpoint_prioritized":
            status = str(event.get("status") or "priority_low")
            priority_id = str(event.get("priority_id") or f"risk-{endpoint_id}-{event.get('id')}")
            label = str(event.get("priority") or status)
            add_node(nodes, priority_id, "risk_priority", label, status=status, **event_props(event, "status"))
            if endpoint_id:
                method = str(event.get("method") or "")
                path = str(event.get("path") or event.get("target") or endpoint_id)
                add_node(nodes, endpoint_id, "endpoint", f"{method} {path}".strip(), status="mapped_only", **event_props(event, "status"))
                add_edge(edges, endpoint_id, priority_id, "endpoint_has_risk_priority", label)

        elif typ == "risk_prioritization_reviewed":
            review_id = str(event.get("review_id") or f"risk-review-{event.get('id')}")
            label = str(event.get("output_path") or "risk prioritization review")
            add_node(nodes, review_id, "risk_review", label, status=str(event.get("status") or "saved"), **event_props(event, "status"))
            latest_risk_metrics = {
                "risk_endpoints_ranked": event.get("endpoints_ranked", 0),
                "risk_top_score": event.get("top_score", 0),
                "risk_avg_score": event.get("avg_score", 0),
                "risk_priority_p0": event.get("priority_p0", 0),
                "risk_priority_p1": event.get("priority_p1", 0),
                "risk_priority_p2": event.get("priority_p2", 0),
                "risk_priority_p3": event.get("priority_p3", 0),
            }

        elif typ == "domain_profile_loaded":
            profile_id = str(event.get("profile_id") or f"domain-{event.get('domain') or event.get('id')}")
            domain_profiles.add(profile_id)
            label = str(event.get("name") or event.get("domain") or profile_id)
            add_node(nodes, profile_id, "domain_profile", label, status=str(event.get("status") or "domain_planned"), **event_props(event, "status"))

        elif typ in {"domain_check_planned", "domain_check_completed"}:
            check_id = str(event.get("check_id") or f"domain-check-{event.get('id')}")
            profile_id = str(event.get("profile_id") or f"domain-{event.get('domain') or 'general'}")
            status = str(event.get("status") or ("domain_planned" if typ == "domain_check_planned" else "domain_complete"))
            label = str(event.get("title") or check_id)
            add_node(nodes, profile_id, "domain_profile", str(event.get("domain") or profile_id), status="domain_planned", **event_props(event, "status"))
            add_node(nodes, check_id, "domain_check", label, status=status, **event_props(event, "status"))
            add_edge(edges, profile_id, check_id, "domain_has_check", str(event.get("category") or "domain"))
            domain_profiles.add(profile_id)
            domain_check_status[check_id] = status
            if endpoint_id:
                add_edge(edges, endpoint_id, check_id, "endpoint_has_domain_check", str(event.get("domain") or "domain"))
            source_id = str(event.get("source_id") or event.get("file_id") or "")
            if source_id:
                add_edge(edges, source_id, check_id, "source_has_domain_check", str(event.get("domain") or "domain"))

        elif typ == "domain_depth_reviewed":
            review_id = str(event.get("review_id") or f"domain-review-{event.get('id')}")
            label = str(event.get("review_path") or "domain depth review")
            status = str(event.get("status") or "domain_incomplete")
            add_node(nodes, review_id, "domain_depth_review", label, status=status, **event_props(event, "status"))
            latest_domain_metrics = {
                "domain_profiles_total": len(str(event.get("domains") or "").split(",")) if event.get("domains") else len(domain_profiles),
                "domain_checks_planned": event.get("checks_total", 0),
                "domain_checks_complete": event.get("checks_complete", 0),
                "domain_checks_partial": event.get("checks_partial", 0),
                "domain_checks_missing": event.get("checks_missing", 0),
                "domain_depth_avg": event.get("score", 0),
                "domain_wp_score": event.get("domain_wp_score", 0),
                "domain_onprem_score": event.get("domain_onprem_score", 0),
                "domain_mobile_score": event.get("domain_mobile_score", 0),
            }

        elif typ == "verdict_set":
            status = str(event.get("status") or "inconclusive")
            verdict_id = f"verdict-{test_id}-{status}"
            add_node(nodes, verdict_id, "verdict", status, status=status, **event_props(event, "status"))
            add_edge(edges, test_id, verdict_id, "test_has_verdict", status)
            test_status[test_id] = status
            if status in {"confirmed", "finding_candidate"}:
                finding_id = str(event.get("finding_id") or f"finding-{test_id}")
                add_node(nodes, finding_id, "finding", finding_id, status=status, **event_props(event, "status"))
                add_edge(edges, finding_id, test_id, "finding_from_test", status)

        elif typ in {"gap_found", "mapping_gap_found"}:
            gap_id = str(event.get("gap_id") or f"gap-{event.get('id')}")
            add_node(nodes, gap_id, "gap", str(event.get("reason") or event.get("gap") or gap_id), status="blocked", **event_props(event, "status"))
            add_edge(edges, test_id or endpoint_id or loop_id, gap_id, "blocked_by_gap", "gap")

        elif typ == "source_runtime_diff_added":
            diff_id = str(event.get("diff_id") or f"diff-{event.get('id')}")
            add_node(nodes, diff_id, "diff", str(event.get("key") or event.get("reason") or diff_id), status="inconclusive", **event_props(event, "status"))
            add_edge(edges, endpoint_id or asset_id or loop_id, diff_id, "has_runtime_diff", "diff")

        elif typ == "dead_end_recorded":
            dead_id = str(event.get("dead_end_id") or f"dead-{event.get('id')}")
            dead_ends.add(dead_id)
            add_node(nodes, dead_id, "gap", str(event.get("reason") or dead_id), status="inconclusive", **event_props(event, "status"))
            add_edge(edges, test_id or loop_id, dead_id, "dead_end_recorded", "dead end")

        elif typ in {"pivot_decision", "strategy_adjusted", "retest_scheduled"}:
            pivot_id = str(event.get("pivot_id") or f"pivot-{event.get('id')}")
            loop_decisions.setdefault(loop_id or test_id, set()).add(pivot_id)
            add_node(nodes, pivot_id, "pivot", str(event.get("pivot_type") or typ), status="test_attempted", **event_props(event, "status"))
            add_edge(edges, test_id or loop_id, pivot_id, "creates_pivot", typ)
            if loop_id:
                add_edge(edges, pivot_id, loop_id, "pivot_reopens_loop", "retest")

        elif typ in {"attack_path_expanded", "chain_candidate_added"}:
            path_id = str(event.get("attack_path_id") or f"path-{event.get('id')}")
            label = str(event.get("chain") or event.get("capability") or path_id)
            add_node(nodes, path_id, "attack_path", label, status="test_attempted", **event_props(event, "status"))
            add_edge(edges, loop_id or endpoint_id, path_id, "loop_expands_to_path", "path")

        elif typ == "fingerprint_added":
            fp_id = str(event.get("fingerprint_id") or f"fp-{event.get('id')}")
            add_node(nodes, fp_id, "fingerprint", str(event.get("fingerprint") or fp_id), status="mapped_only", **event_props(event, "status"))
            add_edge(edges, endpoint_id or asset_id, fp_id, "has_fingerprint", "fingerprint")

    endpoint_ids = [n["id"] for n in nodes.values() if n["type"] == "endpoint"]
    tested_endpoints = sum(1 for eid in endpoint_ids if endpoint_tests.get(eid))
    confirmed = sum(1 for status in test_status.values() if status == "confirmed")
    candidates = sum(1 for status in test_status.values() if status == "finding_candidate")
    inconclusive = sum(1 for status in test_status.values() if status == "inconclusive")
    open_gaps = sum(1 for n in nodes.values() if n["type"] == "gap" and n.get("status") in {"blocked", "inconclusive"})
    evidence_missing = sum(1 for tid in test_status if not test_evidence.get(tid) and test_status.get(tid) not in {"not_tested", "queued"})
    active_loops = sum(1 for n in nodes.values() if n["type"] == "loop" and not str(n.get("status", "")).startswith("closed"))
    dead_without_decision = len(dead_ends) if not loop_decisions else max(0, len(dead_ends) - sum(len(v) for v in loop_decisions.values()))

    return {
        "version": "1.0.0",
        "engagement_id": engagement_id,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "metrics": {
            "total_assets": sum(1 for n in nodes.values() if n["type"] == "asset"),
            "total_endpoints": len(endpoint_ids),
            "tested_endpoints": tested_endpoints,
            "not_tested_endpoints": max(0, len(endpoint_ids) - tested_endpoints),
            "confirmed_findings": confirmed,
            "finding_candidates": candidates,
            "inconclusive_tests": inconclusive,
            "planned_tests": sum(1 for status in test_status.values() if status == "queued"),
            "planned_angles": sum(1 for status in angle_status.values() if status == "queued"),
            "tested_angles": sum(1 for status in angle_status.values() if status != "queued"),
            "creative_ideas": len(creative_nodes),
            "evidence_missing": evidence_missing,
            "evidence_quality_sufficient": sum(1 for status in evidence_review_status.values() if status == "evidence_sufficient"),
            "evidence_quality_partial": sum(1 for status in evidence_review_status.values() if status == "evidence_partial"),
            "evidence_quality_incomplete": sum(1 for status in evidence_review_status.values() if status == "evidence_incomplete"),
            "evidence_quality_avg": round(sum(evidence_review_score.values()) / len(evidence_review_score), 1) if evidence_review_score else 0,
            "judge_tests_total": latest_judge_metrics.get("judge_tests_total", len(evidence_judge_status)),
            "judge_avg_score": latest_judge_metrics.get(
                "judge_avg_score",
                round(sum(evidence_judge_score.values()) / len(evidence_judge_score), 1) if evidence_judge_score else 0,
            ),
            "judge_reportable": latest_judge_metrics.get("judge_reportable", sum(1 for status in evidence_judge_status.values() if status == "judge_reportable")),
            "judge_candidate": latest_judge_metrics.get("judge_candidate", sum(1 for status in evidence_judge_status.values() if status == "judge_candidate")),
            "judge_needs_evidence": latest_judge_metrics.get("judge_needs_evidence", sum(1 for status in evidence_judge_status.values() if status == "judge_needs_evidence")),
            "judge_blocked": latest_judge_metrics.get("judge_blocked", sum(1 for status in evidence_judge_status.values() if status == "judge_blocked")),
            "judge_rejected": latest_judge_metrics.get("judge_rejected", sum(1 for status in evidence_judge_status.values() if status == "judge_rejected")),
            "source_files_total": latest_source_metrics.get("source_files_total", 0),
            "source_files_complete": latest_source_metrics.get("source_files_complete", 0),
            "source_files_partial": latest_source_metrics.get("source_files_partial", 0),
            "source_files_incomplete": latest_source_metrics.get("source_files_incomplete", 0),
            "source_reviews_missing": latest_source_metrics.get("source_reviews_missing", 0),
            "source_critical_missing": latest_source_metrics.get("source_critical_missing", 0),
            "source_completeness_avg": latest_source_metrics.get("source_completeness_avg", 0),
            "risk_endpoints_ranked": latest_risk_metrics.get("risk_endpoints_ranked", 0),
            "risk_top_score": latest_risk_metrics.get("risk_top_score", 0),
            "risk_avg_score": latest_risk_metrics.get("risk_avg_score", 0),
            "risk_priority_p0": latest_risk_metrics.get("risk_priority_p0", 0),
            "risk_priority_p1": latest_risk_metrics.get("risk_priority_p1", 0),
            "risk_priority_p2": latest_risk_metrics.get("risk_priority_p2", 0),
            "risk_priority_p3": latest_risk_metrics.get("risk_priority_p3", 0),
            "domain_profiles_total": latest_domain_metrics.get("domain_profiles_total", len(domain_profiles)),
            "domain_checks_planned": latest_domain_metrics.get("domain_checks_planned", len(domain_check_status)),
            "domain_checks_complete": latest_domain_metrics.get("domain_checks_complete", sum(1 for status in domain_check_status.values() if status == "domain_complete")),
            "domain_checks_partial": latest_domain_metrics.get("domain_checks_partial", sum(1 for status in domain_check_status.values() if status == "domain_partial")),
            "domain_checks_missing": latest_domain_metrics.get("domain_checks_missing", sum(1 for status in domain_check_status.values() if status in {"domain_planned", "domain_incomplete", "queued"})),
            "domain_depth_avg": latest_domain_metrics.get("domain_depth_avg", 0),
            "domain_wp_score": latest_domain_metrics.get("domain_wp_score", 0),
            "domain_onprem_score": latest_domain_metrics.get("domain_onprem_score", 0),
            "domain_mobile_score": latest_domain_metrics.get("domain_mobile_score", 0),
            "open_gaps": open_gaps,
            "active_loops": active_loops,
            "dead_ends_without_decision": dead_without_decision,
            "queue_tasks_total": len(queue_status),
            "queue_tasks_blocked": sum(1 for status in queue_status.values() if status == "blocked"),
            "queue_tasks_done": sum(1 for status in queue_status.values() if status in {"done", "closed"}),
            "reports_total": len(report_status),
            "reports_submitted": sum(1 for status in report_status.values() if status == "submitted"),
            "reports_accepted": sum(1 for status in report_status.values() if status == "accepted"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build graph_state.json from events.jsonl.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--events", type=Path, help="Events JSONL path")
    parser.add_argument("--out", type=Path, help="Output graph_state.json path")
    args = parser.parse_args()

    root = args.root.resolve()
    events_path = args.events or root / "data/events.jsonl"
    out_path = args.out or root / "data/graph_state.json"
    state = build(read_jsonl(events_path), root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
