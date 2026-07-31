#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
HIGH_VALUE_ANGLES = [
    "object_tenant_boundary",
    "authz_role",
    "field_level_authorization",
    "business_logic",
    "state_transition",
    "client_trust_integrity",
    "async_job_export_import",
    "file_or_url_handling",
    "notification_webhook_callback",
    "input_validation",
    "data_exposure",
    "source_runtime_diff",
    "chain_potential",
]

KEYWORD_GROUPS = [
    ("money", 14, {"billing", "payment", "invoice", "checkout", "refund", "subscription", "coupon", "quota", "payout", "wallet"}),
    ("admin-or-role", 12, {"admin", "role", "permission", "policy", "staff", "moderator", "owner", "settings"}),
    ("identity-session", 11, {"auth", "login", "logout", "session", "token", "jwt", "oauth", "saml", "password", "reset", "mfa", "2fa"}),
    ("tenant-object", 11, {"tenant", "workspace", "organization", "organisation", "org", "team", "project", "account", "user", "member"}),
    ("data-export", 10, {"export", "download", "report", "csv", "pdf", "archive", "backup"}),
    ("file-url-integration", 10, {"upload", "import", "file", "attachment", "avatar", "webhook", "callback", "redirect", "url", "fetch", "proxy", "integration"}),
    ("api-surface", 7, {"graphql", "api", "v1", "v2", "internal", "mobile", "beta"}),
    ("async-bulk", 6, {"job", "queue", "worker", "bulk", "batch", "search", "filter", "cursor"}),
]


@dataclass
class EndpointSummary:
    endpoint_id: str
    asset_id: str = ""
    method: str = ""
    path: str = ""
    target: str = ""
    event_types: set[str] = field(default_factory=set)
    texts: list[str] = field(default_factory=list)
    params: set[str] = field(default_factory=set)
    planned_angles: set[str] = field(default_factory=set)
    tested_angles: set[str] = field(default_factory=set)
    tested_statuses: list[str] = field(default_factory=list)
    verdict_statuses: list[str] = field(default_factory=list)
    evidence_review_statuses: list[str] = field(default_factory=list)
    attack_surfaces: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    source_ids: set[str] = field(default_factory=set)
    source_files: set[str] = field(default_factory=set)
    chain_count: int = 0
    creative_count: int = 0
    test_planned_count: int = 0
    evidence_count: int = 0
    runtime_seen: bool = False
    verified_reachable: bool = False
    imported_static: bool = False
    source_flow_linked: bool = False
    source_runtime_diff: bool = False
    role_inferred: bool = False
    out_of_scope: bool = False
    by_design: bool = False


@dataclass
class PriorityScore:
    endpoint: EndpointSummary
    rank: int
    score: int
    priority: str
    status: str
    readiness: str
    reasons: list[str]
    next_action: str
    required_evidence: str


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


def endpoint_id_from_event(event: dict[str, Any]) -> str:
    return str(event.get("endpoint_id") or event.get("endpoint") or "").strip()


def endpoint_label(endpoint: EndpointSummary) -> str:
    label = f"{endpoint.method} {endpoint.path}".strip()
    return label or endpoint.target or endpoint.endpoint_id


def text_value(event: dict[str, Any], *keys: str) -> str:
    return " ".join(str(event.get(key) or "") for key in keys if event.get(key))


def endpoint_for(endpoints: dict[str, EndpointSummary], endpoint_id: str) -> EndpointSummary:
    if endpoint_id not in endpoints:
        endpoints[endpoint_id] = EndpointSummary(endpoint_id=endpoint_id)
    return endpoints[endpoint_id]


def collect_endpoints(events: list[dict[str, Any]]) -> dict[str, EndpointSummary]:
    endpoints: dict[str, EndpointSummary] = {}
    endpoint_by_test: dict[str, str] = {}

    for event in events:
        endpoint_id = endpoint_id_from_event(event)
        test_id = str(event.get("test_id") or "")
        if endpoint_id and test_id:
            endpoint_by_test[test_id] = endpoint_id
        elif test_id and test_id in endpoint_by_test:
            endpoint_id = endpoint_by_test[test_id]

        if not endpoint_id:
            continue

        endpoint = endpoint_for(endpoints, endpoint_id)
        typ = str(event.get("type") or "")
        endpoint.event_types.add(typ)
        endpoint.texts.append(
            text_value(
                event,
                "path",
                "target",
                "surface",
                "attack_surface",
                "reason",
                "hypothesis",
                "chain",
                "capability",
                "source_file",
                "handler",
            )
        )

        if event.get("asset_id") and not endpoint.asset_id:
            endpoint.asset_id = str(event.get("asset_id"))
        if event.get("method"):
            endpoint.method = str(event.get("method")).upper()
        if event.get("path"):
            endpoint.path = str(event.get("path"))
        if event.get("target"):
            endpoint.target = str(event.get("target"))

        if typ == "endpoint_seen_runtime":
            endpoint.runtime_seen = True
        elif typ == "endpoint_verified_reachable":
            endpoint.verified_reachable = True
        elif typ in {"openapi_endpoint_imported", "graphql_operation_imported", "endpoint_discovered"}:
            endpoint.imported_static = True
        elif typ == "endpoint_role_inferred":
            endpoint.role_inferred = True
        elif typ == "param_discovered":
            param = str(event.get("param") or event.get("name") or event.get("param_id") or "")
            if param:
                endpoint.params.add(param)
        elif typ == "source_flow_linked":
            endpoint.source_flow_linked = True
            if event.get("source_id"):
                endpoint.source_ids.add(str(event.get("source_id")))
            if event.get("source_file"):
                endpoint.source_files.add(str(event.get("source_file")))
        elif typ == "attack_surface_mapped":
            surface = str(event.get("surface") or event.get("attack_surface") or event.get("reason") or "")
            if surface:
                endpoint.attack_surfaces.append(surface)
        elif typ == "endpoint_angle_planned":
            angle = str(event.get("angle") or event.get("bug_class") or "")
            if angle:
                endpoint.planned_angles.add(angle)
        elif typ == "endpoint_angle_tested":
            angle = str(event.get("angle") or event.get("bug_class") or "")
            if angle:
                endpoint.tested_angles.add(angle)
            if event.get("status"):
                endpoint.tested_statuses.append(str(event.get("status")))
        elif typ == "test_planned":
            endpoint.test_planned_count += 1
        elif typ == "evidence_added":
            endpoint.evidence_count += 1
        elif typ == "evidence_reviewed":
            if event.get("status"):
                endpoint.evidence_review_statuses.append(str(event.get("status")))
        elif typ == "verdict_set":
            status = str(event.get("status") or "")
            if status:
                endpoint.verdict_statuses.append(status)
            endpoint.out_of_scope = endpoint.out_of_scope or status == "out_of_scope"
            endpoint.by_design = endpoint.by_design or status == "by_design"
        elif typ in {"gap_found", "mapping_gap_found"}:
            endpoint.blockers.append(str(event.get("reason") or event.get("gap") or "gap recorded"))
        elif typ == "source_runtime_diff_added":
            endpoint.source_runtime_diff = True
        elif typ in {"chain_candidate_added", "attack_path_expanded"}:
            endpoint.chain_count += 1
        elif typ in {"creative_hypothesis_added", "creative_pivot_added"}:
            endpoint.creative_count += 1

    return endpoints


def has_any(text: str, words: set[str]) -> bool:
    lower = text.lower()
    return any(word in lower for word in words)


def score_endpoint(endpoint: EndpointSummary, profile: str) -> tuple[int, list[str], str]:
    reasons: list[str] = []
    full_text = " ".join([endpoint.endpoint_id, endpoint.method, endpoint.path, endpoint.target] + endpoint.texts).lower()
    score = 0

    impact = 0
    for label, points, words in KEYWORD_GROUPS:
        if has_any(full_text, words):
            impact += points
            reasons.append(f"{label} signal +{points}")
    impact = min(34, impact)
    score += impact

    exposure = 0
    if endpoint.verified_reachable:
        exposure += 8
        reasons.append("verified reachable +8")
    elif endpoint.runtime_seen:
        exposure += 6
        reasons.append("seen in runtime traffic +6")
    if endpoint.imported_static:
        exposure += 4
        reasons.append("known from static/API inventory +4")
    if endpoint.source_flow_linked:
        exposure += 4
        reasons.append("linked to source flow +4")
    score += min(16, exposure)

    complexity = 0
    if endpoint.method in WRITE_METHODS:
        method_points = 9 if endpoint.method == "DELETE" else 8
        complexity += method_points
        reasons.append(f"{endpoint.method} can change state +{method_points}")
    if endpoint.params:
        param_points = min(6, len(endpoint.params) * 2)
        complexity += param_points
        reasons.append(f"{len(endpoint.params)} parameter(s) +{param_points}")
    if endpoint.attack_surfaces:
        surface_points = min(7, len(endpoint.attack_surfaces) * 4)
        complexity += surface_points
        reasons.append(f"attack surface mapped +{surface_points}")
    score += min(18, complexity)

    boundary = 0
    boundary_angles = endpoint.planned_angles & {"authz_role", "object_tenant_boundary", "field_level_authorization", "authn_session"}
    if has_any(full_text, {"role", "permission", "tenant", "workspace", "org", "owner", "invoice", "user", "account", "session", "token"}):
        boundary += 8
        reasons.append("auth/object boundary wording +8")
    if boundary_angles:
        angle_points = min(6, len(boundary_angles) * 3)
        boundary += angle_points
        reasons.append("boundary angle planned +" + str(angle_points))
    if endpoint.role_inferred:
        boundary += 3
        reasons.append("role inferred +3")
    score += min(15, boundary)

    chain = 0
    if endpoint.chain_count:
        chain_points = min(9, endpoint.chain_count * 5)
        chain += chain_points
        reasons.append(f"chain candidate/path +{chain_points}")
    if endpoint.source_runtime_diff:
        chain += 6
        reasons.append("source/runtime diff +6")
    if endpoint.creative_count:
        creative_points = min(5, endpoint.creative_count * 3)
        chain += creative_points
        reasons.append(f"creative hypothesis/pivot +{creative_points}")
    score += min(15, chain)

    coverage = 0
    untested_angles = endpoint.planned_angles - endpoint.tested_angles
    if endpoint.planned_angles and untested_angles:
        angle_gap_points = min(10, len(untested_angles) * 2)
        coverage += angle_gap_points
        reasons.append(f"{len(untested_angles)} planned untested angle(s) +{angle_gap_points}")
    elif not endpoint.planned_angles:
        coverage += 5
        reasons.append("no angle plan yet +5")
    if not endpoint.tested_angles and not endpoint.verdict_statuses:
        coverage += 8
        reasons.append("not tested yet +8")
    if endpoint.test_planned_count:
        coverage += min(4, endpoint.test_planned_count)
        reasons.append("test card exists +" + str(min(4, endpoint.test_planned_count)))
    score += min(18, coverage)

    if profile == "impact":
        score = int(score * 1.08)
    elif profile == "coverage":
        score += 8 if not endpoint.tested_angles else 0
    elif profile == "source":
        score += 8 if endpoint.source_flow_linked or endpoint.source_runtime_diff else 0
    elif profile == "runtime":
        score += 8 if endpoint.verified_reachable or endpoint.runtime_seen else 0

    reduction = 0
    secure_count = sum(1 for status in endpoint.tested_statuses + endpoint.verdict_statuses if status == "tested_secure")
    if secure_count:
        reduction += min(18, secure_count * 5)
        reasons.append(f"tested_secure evidence reduces priority -{min(18, secure_count * 5)}")
    if "evidence_sufficient" in endpoint.evidence_review_statuses:
        reduction += 6
        reasons.append("evidence already sufficient -6")
    if "confirmed" in endpoint.verdict_statuses:
        reduction += 30
        reasons.append("already confirmed; report/chain instead of first-test -30")
    if endpoint.out_of_scope or endpoint.by_design:
        reduction += 50
        reasons.append("out_of_scope/by_design reduces test priority -50")
    if any(status == "blocked" for status in endpoint.tested_statuses + endpoint.verdict_statuses) or endpoint.blockers:
        reduction += 8
        reasons.append("blocked/gap requires unblock before testing -8")

    score = max(0, min(100, score - reduction))
    return score, reasons[:8], next_action(endpoint)


def readiness(endpoint: EndpointSummary) -> str:
    if endpoint.out_of_scope or endpoint.by_design:
        return "closed_policy"
    if endpoint.blockers or any(status == "blocked" for status in endpoint.tested_statuses + endpoint.verdict_statuses):
        return "blocked"
    points = 0
    if endpoint.method and (endpoint.path or endpoint.target):
        points += 25
    if endpoint.verified_reachable or endpoint.runtime_seen:
        points += 20
    if endpoint.source_flow_linked:
        points += 15
    if endpoint.attack_surfaces:
        points += 15
    if endpoint.planned_angles:
        points += 15
    if endpoint.params:
        points += 5
    if endpoint.test_planned_count:
        points += 5
    if points >= 70:
        return "ready"
    if points >= 40:
        return "needs_context"
    return "low_signal"


def priority_label(score: int) -> tuple[str, str]:
    if score >= 80:
        return "P0", "priority_critical"
    if score >= 65:
        return "P1", "priority_high"
    if score >= 45:
        return "P2", "priority_medium"
    return "P3", "priority_low"


def choose_angle(endpoint: EndpointSummary) -> str:
    untested = endpoint.planned_angles - endpoint.tested_angles
    for angle in HIGH_VALUE_ANGLES:
        if angle in untested:
            return angle
    return sorted(untested)[0] if untested else ""


def next_action(endpoint: EndpointSummary) -> str:
    if endpoint.out_of_scope:
        return "Do not test; archive as out_of_scope with policy evidence."
    if endpoint.by_design:
        return "Do not retest unless policy/context changed; keep by_design evidence."
    if endpoint.blockers:
        return "Resolve blocker/gap first: " + endpoint.blockers[-1]
    if not endpoint.method or not (endpoint.path or endpoint.target):
        return f"Map method/path for `{endpoint.endpoint_id}` from browser/Burp/source before active testing."
    if not endpoint.source_flow_linked and ("source_file_read" in endpoint.event_types or "source_flow_linked" not in endpoint.event_types):
        return "Link endpoint to source/runtime flow if source is available, then map attack surface."
    if not endpoint.attack_surfaces:
        return "Run source/runtime analysis and write `attack_surface_mapped` before payload testing."
    if not endpoint.planned_angles:
        return f"Run `bbf angle-plan full --endpoint-id {endpoint.endpoint_id}`."
    angle = choose_angle(endpoint)
    if angle:
        return f"Run `bbf angle-exec --endpoint-id {endpoint.endpoint_id} --angle {angle} --allow-active` with owned-account controls."
    if endpoint.evidence_review_statuses and endpoint.evidence_review_statuses[-1] != "evidence_sufficient":
        return f"Fix evidence gaps, then run `bbf evidence-score --endpoint-id {endpoint.endpoint_id} --all`."
    if endpoint.chain_count:
        return "Expand chain candidate into the next endpoint or close with evidence-backed verdict."
    return "Review coverage; add creative hypothesis or close remaining angles with evidence."


def required_evidence(endpoint: EndpointSummary) -> str:
    angle = choose_angle(endpoint)
    if angle in {"object_tenant_boundary", "authz_role", "field_level_authorization"}:
        return "baseline owned account, alternate role/account negative control, mutated object request, independent read-back"
    if angle in {"business_logic", "state_transition", "client_trust_integrity"}:
        return "normal flow baseline, one safe mutation, forbidden/negative control, server-side read-back"
    if angle in {"file_or_url_handling", "notification_webhook_callback"}:
        return "baseline, controlled URL/file/callback mutation, callback/server log, read-back"
    if endpoint.method in WRITE_METHODS:
        return "baseline, mutated request, negative control, before/after read-back"
    return "baseline, variant request, negative control, response diff/read-back"


def rank_endpoints(endpoints: dict[str, EndpointSummary], profile: str, include_low: bool) -> list[PriorityScore]:
    scored: list[PriorityScore] = []
    for endpoint in endpoints.values():
        score, reasons, _ = score_endpoint(endpoint, profile)
        priority, status = priority_label(score)
        if not include_low and priority == "P3":
            continue
        scored.append(
            PriorityScore(
                endpoint=endpoint,
                rank=0,
                score=score,
                priority=priority,
                status=status,
                readiness=readiness(endpoint),
                reasons=reasons,
                next_action=next_action(endpoint),
                required_evidence=required_evidence(endpoint),
            )
        )
    scored.sort(
        key=lambda item: (
            item.score,
            item.readiness == "ready",
            item.endpoint.verified_reachable or item.endpoint.runtime_seen,
            len(item.endpoint.planned_angles - item.endpoint.tested_angles),
        ),
        reverse=True,
    )
    for index, item in enumerate(scored, 1):
        item.rank = index
    return scored


def write_outputs(root: Path, ranked: list[PriorityScore], profile: str, limit: int, run_id: str) -> str:
    selected = ranked[:limit]
    rows = []
    for item in selected:
        endpoint = item.endpoint
        rows.append(
            "| {rank} | {priority} | `{endpoint_id}` | `{label}` | {score} | {readiness} | {reason} | {next_action} | {evidence} |".format(
                rank=item.rank,
                priority=item.priority,
                endpoint_id=endpoint.endpoint_id,
                label=endpoint_label(endpoint).replace("|", "/"),
                score=item.score,
                readiness=item.readiness,
                reason="<br>".join(item.reasons).replace("|", "/") or "-",
                next_action=item.next_action.replace("|", "/"),
                evidence=item.required_evidence.replace("|", "/"),
            )
        )
    text = (
        "# Priority Testing Plan\n\n"
        f"- Generated by: `bbf risk-prioritize`\n"
        f"- Run ID: `{run_id}`\n"
        f"- Profile: `{profile}`\n"
        f"- Ranked endpoints: `{len(ranked)}`\n"
        f"- Shown: `{len(selected)}`\n\n"
        "## Risk Formula\n\n"
        "Score combines business-impact keywords, runtime reachability, write methods, parameters, "
        "source-flow context, attack-surface mapping, boundary angles, chain/creative signals, "
        "and coverage gaps. Existing `tested_secure`, sufficient evidence, confirmed, out-of-scope, "
        "or blocked state reduces first-test priority.\n\n"
        "## Ranked Queue\n\n"
        "| Rank | Priority | Endpoint ID | Method/Path | Score | Readiness | Why | Next Action | Required Evidence |\n"
        "|---:|---|---|---|---:|---|---|---|---|\n"
        + ("\n".join(rows) if rows else "| - | - | - | - | - | - | No endpoints available | - | - |")
        + "\n\n## Priority Meaning\n\n"
        "- `P0`: test first when scope and safety allow it.\n"
        "- `P1`: high-value next queue.\n"
        "- `P2`: useful but behind stronger signals.\n"
        "- `P3`: low signal or already mostly handled.\n"
    )
    (root / "priority-testing-plan.md").write_text(text, encoding="utf-8")

    data = {
        "version": "1.0.0",
        "generated_at": now(),
        "run_id": run_id,
        "profile": profile,
        "ranked_endpoints": len(ranked),
        "priorities": [
            {
                "rank": item.rank,
                "priority": item.priority,
                "status": item.status,
                "score": item.score,
                "readiness": item.readiness,
                "endpoint_id": item.endpoint.endpoint_id,
                "asset_id": item.endpoint.asset_id,
                "method": item.endpoint.method,
                "path": item.endpoint.path,
                "target": item.endpoint.target,
                "reasons": item.reasons,
                "next_action": item.next_action,
                "required_evidence": item.required_evidence,
            }
            for item in selected
        ],
    }
    out = root / "data/risk_priorities.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return str(out.relative_to(root))


def emit_events(root: Path, events_path: Path, events: list[dict[str, Any]], ranked: list[PriorityScore], limit: int, run_id: str, profile: str, actor: str, output_path: str) -> None:
    engagement_id = current_engagement_id(root)
    selected = ranked[:limit]
    counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for item in ranked:
        counts[item.priority] += 1

    next_num = len(events) + 1
    for item in selected:
        endpoint = item.endpoint
        priority_id = f"risk-{run_id}-{item.rank:03d}"
        write_event(
            events_path,
            {
                "id": f"evt-{next_num:06d}",
                "ts": now(),
                "engagement_id": engagement_id,
                "actor": actor,
                "type": "endpoint_prioritized",
                "status": item.status,
                "priority_id": priority_id,
                "run_id": run_id,
                "rank": item.rank,
                "priority": item.priority,
                "risk_score": item.score,
                "readiness": item.readiness,
                "endpoint_id": endpoint.endpoint_id,
                "asset_id": endpoint.asset_id,
                "method": endpoint.method,
                "path": endpoint.path,
                "target": endpoint.target,
                "reasons": item.reasons,
                "next_action": item.next_action,
                "required_evidence": item.required_evidence,
                "source": "bbf risk-prioritize",
            },
        )
        next_num += 1

    top_score = selected[0].score if selected else 0
    avg_score = round(sum(item.score for item in ranked) / len(ranked), 1) if ranked else 0
    write_event(
        events_path,
        {
            "id": f"evt-{next_num:06d}",
            "ts": now(),
            "engagement_id": engagement_id,
            "actor": actor,
            "type": "risk_prioritization_reviewed",
            "status": "saved",
            "review_id": f"risk-review-{run_id}",
            "run_id": run_id,
            "profile": profile,
            "output_path": output_path,
            "endpoints_ranked": len(ranked),
            "top_score": top_score,
            "avg_score": avg_score,
            "priority_p0": counts["P0"],
            "priority_p1": counts["P1"],
            "priority_p2": counts["P2"],
            "priority_p3": counts["P3"],
            "top_endpoint_id": selected[0].endpoint.endpoint_id if selected else "",
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rank endpoints by risk and testing value for large engagements.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--profile", choices=["balanced", "impact", "coverage", "source", "runtime"], default="balanced")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--include-low", action="store_true", help="Include P3 endpoints in the plan.")
    parser.add_argument("--no-event", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--actor", default="ai")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    events_path = root / "data/events.jsonl"
    events = read_events(events_path)
    endpoints = collect_endpoints(events)
    ranked = rank_endpoints(endpoints, args.profile, args.include_low)
    run_seed = f"{now()}|{current_engagement_id(root)}|{args.profile}|{len(events)}"
    run_id = hashlib.sha1(run_seed.encode("utf-8")).hexdigest()[:10]
    output_path = write_outputs(root, ranked, args.profile, args.limit, run_id)

    if not args.no_event:
        emit_events(root, events_path, events, ranked, args.limit, run_id, args.profile, args.actor, output_path)
    if not args.no_build:
        build_graph(root)

    print(f"ranked endpoints: {len(ranked)}")
    print(f"output: {output_path}")
    for item in ranked[: args.limit]:
        print(f"{item.rank}. {item.priority} {item.score}/100 {item.endpoint.endpoint_id} {endpoint_label(item.endpoint)} -> {item.next_action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
