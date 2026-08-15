#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import ai_governance


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_DIRS = ["docs", "rules", "notes", "findings", "report", "evidence"]


def usage() -> None:
    print("usage: init_engagement.py <program> <target>", file=sys.stderr)


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def copy_template(src_name: str, dst: Path) -> None:
    src = ROOT / "templates" / "engagement" / src_name
    write_if_missing(dst, src.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        usage()
        return 2

    program = argv[1].strip().replace("/", "-")
    target = argv[2].strip().replace("/", "-")
    if not program or not target:
        usage()
        return 2

    engagement_id = f"{program}-{target}"
    program_root = ROOT / "engagements" / program
    base = program_root / target

    for rel in PROGRAM_DIRS:
        (program_root / rel).mkdir(parents=True, exist_ok=True)

    program_placeholders = {
        "docs/README.md": f"# {program} Documentation\n\nProgram-level documentation, assets, methodology notes, and external references.\n",
        "rules/scope.md": f"# {program} Scope\n\nProgram-level scope, in-scope assets, out-of-scope assets, rate limits, and testing restrictions.\n",
        "rules/program-rules.md": f"# {program} Program Rules\n\nCopy platform/program rules here before active testing.\n",
        "notes/README.md": f"# {program} Notes\n\nProgram-level observations that apply across targets.\n",
        "findings/.gitkeep": "",
        "report/.gitkeep": "",
        "evidence/.gitkeep": "",
    }
    for rel, content in program_placeholders.items():
        write_if_missing(program_root / rel, content)

    dirs = [
        "data",
        "notes/loop",
        "leads",
        "leads/test-cards",
        "domain-depth",
        "source-reviews",
        "source-reviews/_completeness",
        "primitives",
        "findings/candidates",
        "findings/confirmed",
        "reports/drafts",
        "reports/submitted",
        "reports/archived",
        "evidence/burp",
        "evidence/caido",
        "evidence/responses",
        "evidence/reviews",
        "evidence/judgements",
        "evidence/screenshots",
        "evidence/logs",
        "output",
        "metrics",
        "scripts",
        ".private",
    ]
    for rel in dirs:
        (base / rel).mkdir(parents=True, exist_ok=True)

    for rel in [
        "evidence/burp/.gitkeep",
        "evidence/caido/.gitkeep",
        "evidence/responses/.gitkeep",
        "evidence/reviews/.gitkeep",
        "evidence/judgements/.gitkeep",
        "evidence/screenshots/.gitkeep",
        "evidence/logs/.gitkeep",
        "leads/test-cards/.gitkeep",
        "source-reviews/_completeness/.gitkeep",
    ]:
        write_if_missing(base / rel, "")

    copy_template("scope.md", base / "scope.md")
    copy_template("notes_rules.md", base / "notes/rules.md")
    copy_template("recent-state.md", base / "notes/recent-state.md")
    copy_template("loop_queue.md", base / "notes/loop/queue.md")
    copy_template("loop_log.md", base / "notes/loop/log.md")
    copy_template("coverage-matrix.md", base / "coverage-matrix.md")
    copy_template("multi-angle-coverage.md", base / "multi-angle-coverage.md")
    copy_template("owasp-a01-a10-coverage.md", base / "owasp-a01-a10-coverage.md")
    copy_template("source-file-queue.md", base / "source-file-queue.md")
    copy_template("creative-exploration.md", base / "creative-exploration.md")
    copy_template("test-ledger.md", base / "test-ledger.md")
    copy_template("unknowns.md", base / "unknowns.md")
    copy_template("priority-testing-plan.md", base / "priority-testing-plan.md")

    report_template = ROOT / "templates" / "reports" / "report-template.md"
    write_if_missing(base / "reports/drafts/report-template.md", report_template.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).astimezone().isoformat()
    write_if_missing(
        base / "data/safety_policy.json",
        json.dumps(
            {
                "version": "1.0.0",
                "mode": "enforce",
                "max_rps": 10,
                "allow_hosts": [],
                "allow_schemes": ["https", "http"],
                "allow_methods": ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
                "forbidden_path_patterns": ["*/logout*", "*/delete-account*", "*/billing/charge*", "*/payments/capture*", "*/admin/destroy*"],
                "active_testing_requires_approval": True,
                "notes": [
                    "Fill allow_hosts before live testing.",
                    "Use owned accounts and non-destructive payloads only.",
                    "Keep max_rps at or below the program rules.",
                ],
            },
            indent=2,
        )
        + "\n",
    )
    write_if_missing(
        base / "data/run_queue.json",
        json.dumps({"version": "1.0.0", "engagement_id": engagement_id, "tasks": []}, indent=2) + "\n",
    )
    write_if_missing(
        base / "data/report_lifecycle.json",
        json.dumps({"version": "1.0.0", "reports": []}, indent=2) + "\n",
    )
    governance = dict(ai_governance.DEFAULT_CONFIG)
    governance["generated_at"] = now
    write_if_missing(base / "data/ai_governance.json", json.dumps(governance, indent=2) + "\n")

    events = base / "data/events.jsonl"
    if not events.exists():
        events.write_text(
            json.dumps(
                {
                    "id": "evt-init-001",
                    "ts": now,
                    "engagement_id": engagement_id,
                    "actor": "system",
                    "type": "operator_note_added",
                    "notes": "Engagement initialized. Fill scope.md and notes/rules.md before live testing.",
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

    graph = base / "data/graph_state.json"
    if not graph.exists():
        graph.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "engagement_id": engagement_id,
                    "generated_at": now,
                    "nodes": [],
                    "edges": [],
                    "metrics": {
                        "total_assets": 0,
                        "total_endpoints": 0,
                        "tested_endpoints": 0,
                        "not_tested_endpoints": 0,
                        "confirmed_findings": 0,
                        "finding_candidates": 0,
                        "inconclusive_tests": 0,
                        "planned_tests": 0,
                        "planned_angles": 0,
                        "tested_angles": 0,
                        "creative_ideas": 0,
                        "evidence_missing": 0,
                        "evidence_quality_sufficient": 0,
                        "evidence_quality_partial": 0,
                        "evidence_quality_incomplete": 0,
                        "evidence_quality_avg": 0,
                        "judge_tests_total": 0,
                        "judge_avg_score": 0,
                        "judge_reportable": 0,
                        "judge_candidate": 0,
                        "judge_needs_evidence": 0,
                        "judge_blocked": 0,
                        "judge_rejected": 0,
                        "source_files_total": 0,
                        "source_files_complete": 0,
                        "source_files_partial": 0,
                        "source_files_incomplete": 0,
                        "source_reviews_missing": 0,
                        "source_critical_missing": 0,
                        "source_completeness_avg": 0,
                        "risk_endpoints_ranked": 0,
                        "risk_top_score": 0,
                        "risk_avg_score": 0,
                        "risk_priority_p0": 0,
                        "risk_priority_p1": 0,
                        "risk_priority_p2": 0,
                        "risk_priority_p3": 0,
                        "domain_profiles_total": 0,
                        "domain_checks_planned": 0,
                        "domain_checks_complete": 0,
                        "domain_checks_partial": 0,
                        "domain_checks_missing": 0,
                        "domain_depth_avg": 0,
                        "domain_wp_score": 0,
                        "domain_onprem_score": 0,
                        "domain_mobile_score": 0,
                        "open_gaps": 0,
                        "active_loops": 0,
                        "dead_ends_without_decision": 0,
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    shutil.copy2(ROOT / "AGENTS.md", base / "AGENTS.md")
    print(base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
