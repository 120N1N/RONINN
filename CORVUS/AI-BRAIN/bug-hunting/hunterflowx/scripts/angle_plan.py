#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Angle:
    name: str
    family: str
    question: str
    safe_strategy: str
    evidence: str


CORE_ANGLES = [
    Angle(
        "authn_session",
        "identity/session",
        "Does the endpoint reject missing, expired, replayed, downgraded, or cross-context sessions?",
        "Compare unauth, fake token, expired token, logged-out token, normal session, and alternate browser session.",
        "Baseline and variant request/response showing session boundary behavior.",
    ),
    Angle(
        "authz_role",
        "authorization",
        "Does role, permission, plan, or feature entitlement block the action server-side?",
        "Compare low-role, normal-role, admin-like owned role, and feature-disabled account where allowed.",
        "A/B role comparison and independent read-back when state changes.",
    ),
    Angle(
        "object_tenant_boundary",
        "authorization",
        "Can object, tenant, organization, project, or workspace identifiers cross ownership boundaries?",
        "Mutate one object or tenant identifier at a time across owned accounts and sibling endpoints.",
        "Ownership proof plus baseline, mutation, and read-back evidence.",
    ),
    Angle(
        "input_validation",
        "input/parser",
        "Does typed input reach parser, query, template, command, file, XML, JSON, GraphQL, or deserialization sinks unsafely?",
        "Use marker-only, negative-control, and context-specific payload families after understanding the sink.",
        "Control/variant pairs with rendered, timing, error, or source-sink evidence.",
    ),
    Angle(
        "state_transition",
        "workflow/state",
        "Can the workflow be skipped, replayed, reordered, duplicated, or partially completed?",
        "Model normal states first, then mutate exactly one transition using owned low-impact resources.",
        "Before/after server state and mutated transition request.",
    ),
    Angle(
        "business_logic",
        "workflow/business",
        "Can price, quota, invite, coupon, refund, approval, limit, or abuse-control invariants be violated?",
        "Write the expected invariant, test low-impact mutations, and read server state independently.",
        "Normal flow, forbidden mutation, and business-impact read-back.",
    ),
    Angle(
        "data_exposure",
        "data/privacy",
        "Does the endpoint expose fields, metadata, relationships, logs, exports, or hidden properties beyond the caller's need?",
        "Compare roles, accounts, filters, sparse fieldsets, expansions, exports, and undocumented fields.",
        "Response diff proving sensitive non-public data exposure.",
    ),
    Angle(
        "side_effect_write",
        "write/effect",
        "Can a read-like, preview, import, webhook, or background job cause unauthorized side effects?",
        "Trace every server-side write, notification, callback, email, job, or integration side effect.",
        "Request plus independent proof that the side effect occurred.",
    ),
    Angle(
        "rate_limit_or_race",
        "volume/concurrency",
        "Can rate, quota, redemption, ordering, idempotency, or concurrency controls be bypassed?",
        "Start with a single-request control, then use bounded replay or small synchronized batches inside rules.",
        "Single vs concurrent behavior and after-state proof.",
    ),
    Angle(
        "cache_cors_redirect",
        "browser/cache",
        "Can cache, CORS, redirect, referrer, cookie, or origin behavior expose or confuse trust boundaries?",
        "Compare origin, credential, cache key, redirect target, and shared-cache behavior safely.",
        "Header/response pairs and browser-visible proof where relevant.",
    ),
    Angle(
        "file_or_url_handling",
        "file/url/integration",
        "Can upload, import, preview, fetch, archive, path, URL, webhook, or callback handling be abused?",
        "Test extension/content-type/parser/redirect/scheme/path normalization with harmless controlled inputs.",
        "Upload/fetch trigger, server behavior, callback log, or retrieved-file proof.",
    ),
    Angle(
        "error_oracle",
        "observability/oracle",
        "Do errors, timing, validation differences, debug traces, or partial failures reveal sensitive behavior?",
        "Use paired controls, retry repeatability, and compare verbose error paths without destructive probing.",
        "Repeatable diff table or redacted error proof tied to impact.",
    ),
    Angle(
        "source_runtime_diff",
        "source/runtime",
        "Does source or JS show routes, guards, fields, sinks, or middleware that differ from runtime behavior?",
        "Link source file or JS route to live request, then test the mismatch as a concrete gap.",
        "Source-review artifact plus runtime request/response proof.",
    ),
    Angle(
        "chain_potential",
        "attack-chain",
        "Can a weak primitive become stronger by feeding another endpoint, role, token, file, webhook, or workflow?",
        "Map primitive -> capability -> next input before deciding whether the primitive is reportable.",
        "Chain candidate, next endpoint, and evidence path.",
    ),
]


EXTENDED_ANGLES = [
    Angle(
        "method_content_type_variance",
        "protocol/parser",
        "Do alternate HTTP methods, content types, or duplicate parameters reach different handlers?",
        "Compare GET/POST/PATCH/DELETE where safe, JSON vs form, duplicate keys, and nested object encodings.",
        "Protocol matrix with accepted/rejected variants.",
    ),
    Angle(
        "field_level_authorization",
        "data/privacy",
        "Are sensitive response fields and writable properties authorized per role and per object?",
        "Test field expansion, sparse fields, mass assignment, hidden booleans, and role-specific attributes.",
        "Allowed vs disallowed field behavior with role/object proof.",
    ),
    Angle(
        "inventory_version_shadow_api",
        "inventory/api",
        "Does a deprecated, mobile-only, internal, beta, or versioned route have weaker controls?",
        "Compare v1/v2/mobile/admin/beta routes and JS-discovered routes against current documented routes.",
        "Route inventory diff and boundary test evidence.",
    ),
    Angle(
        "async_job_export_import",
        "async/data",
        "Do queued jobs, exports, imports, emails, reports, or background workers lose authorization context?",
        "Trigger low-impact jobs with owned data, then test ownership, polling, download, and callback boundaries.",
        "Job trigger, job status, output retrieval, and ownership proof.",
    ),
    Angle(
        "idempotency_replay_rollback",
        "workflow/state",
        "Can idempotency keys, retries, cancellation, rollback, timeout, or partial failure create inconsistent state?",
        "Replay and interrupt low-impact actions, then check final server state and duplicated effects.",
        "Retry/rollback request sequence and final-state proof.",
    ),
    Angle(
        "client_trust_integrity",
        "integrity/client",
        "Does the server trust client-calculated price, role, limit, feature flag, signature, or workflow state?",
        "Tamper client-controlled values one at a time and verify server-side recomputation or rejection.",
        "Control/tampered pair and server read-back.",
    ),
    Angle(
        "notification_webhook_callback",
        "integration/side-effect",
        "Can notifications, webhooks, callbacks, or integrations leak data or perform actions across tenants?",
        "Use controlled callback endpoints and owned integrations; compare tenant, role, and event payload boundaries.",
        "Callback log, payload sample, and ownership proof.",
    ),
    Angle(
        "search_filter_sort_pagination",
        "query/data",
        "Can filters, sorting, pagination, search operators, or cursor tokens expose unauthorized objects?",
        "Mutate filters, cursors, sort keys, search syntax, and page tokens with owned cross-account controls.",
        "Query/control/variant responses showing boundary behavior.",
    ),
]


CREATIVE_SEEDS = [
    (
        "source_runtime_diff",
        "A route or JS call exists without a visible UI path; it may be a hidden feature, old flow, or missing middleware.",
        "Create a source/runtime diff and test role, object, version, and feature-flag boundaries.",
    ),
    (
        "weird_response_differential",
        "Different errors for similar invalid inputs may expose parser, auth, object existence, or query behavior.",
        "Build a tiny control matrix and only escalate when the diff is repeatable and safe.",
    ),
    (
        "extra_field_accepted",
        "Accepted unknown fields may imply mass assignment, integrity failure, or hidden feature flags.",
        "Test one harmless extra field at a time and read back server state.",
    ),
    (
        "async_or_export_flow",
        "Background exports, reports, or jobs may lose the original user's authorization context.",
        "Map trigger, polling, download, and output ownership with owned data only.",
    ),
    (
        "url_or_callback_input",
        "URL, webhook, avatar, import, preview, or integration inputs may become SSRF, open redirect, or unsafe upstream API use.",
        "Use controlled callback infrastructure and respect program SSRF limits.",
    ),
    (
        "business_shortcut",
        "A legitimate workflow may allow skip, replay, duplicate, downgrade, refund, quota, or approval bypass.",
        "Model the invariant and mutate one transition with low-impact owned resources.",
    ),
    (
        "shadow_api_inventory",
        "Mobile, beta, deprecated, or versioned API routes may have stale auth or weaker validation.",
        "Compare behavior across versions and route families before payload testing.",
    ),
    (
        "cache_or_origin_boundary",
        "Cache key, CORS, redirect, referrer, cookie, or origin behavior may expose data between contexts.",
        "Run browser-visible origin/cache controls with owned accounts.",
    ),
    (
        "third_party_trust",
        "External API, webhook, package, CDN, or integration data may be trusted without validation.",
        "Map upstream input to downstream effect and test only controlled integrations.",
    ),
    (
        "weak_signal_chain",
        "A low-impact primitive may be valuable only if chained into token, file, role, webhook, or state control.",
        "Record primitive -> capability -> next input before deciding reportability.",
    ),
]


PROFILES = {
    "core": (CORE_ANGLES, False),
    "deep": (CORE_ANGLES + EXTENDED_ANGLES, False),
    "creative": ([], True),
    "full": (CORE_ANGLES + EXTENDED_ANGLES, True),
}


def slugify(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    return clean.strip("-") or "target"


def json_dump(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)


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
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json_dump(event) + "\n")


def append_unique_row(path: Path, row: str, header: str) -> None:
    if not path.exists():
        path.write_text(header, encoding="utf-8")
    current = path.read_text(encoding="utf-8")
    if row not in current:
        marker = "\nAllowed statuses:"
        if marker in current:
            updated = current.replace(marker, row + "\n" + marker, 1)
            path.write_text(updated, encoding="utf-8")
        else:
            with path.open("a", encoding="utf-8") as f:
                f.write(row + "\n")


def build_graph(root: Path) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_graph.py"), "--root", str(root)], check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create durable multi-angle and creative exploration events for one endpoint.")
    parser.add_argument("profile", choices=sorted(PROFILES), nargs="?", default="full")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--asset-id", default="")
    parser.add_argument("--endpoint-id", default="")
    parser.add_argument("--method", default="")
    parser.add_argument("--path", default="")
    parser.add_argument("--target", default="")
    parser.add_argument("--loop-id", default="")
    parser.add_argument("--actor", default="ai")
    parser.add_argument("--source", default="bbf angle-plan")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    events_path = root / "data/events.jsonl"
    events = read_events(events_path)
    next_num = len(events) + 1
    engagement_id = current_engagement_id(root)
    method = args.method.upper() if args.method else ""
    endpoint_id = args.endpoint_id or f"ep-{slugify(args.path or args.target or args.asset_id or 'target')}"
    endpoint_label = f"{method} {args.path}".strip() or args.target or endpoint_id
    ts = datetime.now(timezone.utc).astimezone().isoformat()
    written_angles = 0
    written_creative = 0

    if endpoint_id and not any(str(e.get("endpoint_id") or "") == endpoint_id and e.get("type") in {"endpoint_discovered", "endpoint_seen_runtime", "endpoint_verified_reachable", "openapi_endpoint_imported", "graphql_operation_imported"} for e in events):
        endpoint_event: dict[str, Any] = {
            "id": f"evt-{next_num:06d}",
            "ts": ts,
            "engagement_id": engagement_id,
            "actor": args.actor,
            "type": "endpoint_discovered",
            "status": "mapped_only",
            "asset_id": args.asset_id,
            "endpoint_id": endpoint_id,
            "source": args.source,
        }
        if method:
            endpoint_event["method"] = method
        if args.path:
            endpoint_event["path"] = args.path
        if args.target:
            endpoint_event["target"] = args.target
        write_event(events_path, endpoint_event)
        next_num += 1

    angles, include_creative = PROFILES[args.profile]
    existing_angle_ids = {str(e.get("angle_id") or "") for e in events}
    coverage_header = (
        "# Multi-Angle Endpoint Coverage\n\n"
        "Use one row per endpoint angle. Do not mark an endpoint as covered only because one payload was tried.\n\n"
        "| Endpoint ID | Method/Path | Angle | Status | Evidence/Event | Gap/Next Action |\n"
        "|---|---|---|---|---|---|\n"
    )
    for angle in angles:
        angle_id = f"angle-{slugify(endpoint_id)}-{slugify(angle.name)}"
        if angle_id in existing_angle_ids:
            continue
        event_id = f"evt-{next_num:06d}"
        event: dict[str, Any] = {
            "id": event_id,
            "ts": ts,
            "engagement_id": engagement_id,
            "actor": args.actor,
            "type": "endpoint_angle_planned",
            "status": "queued",
            "asset_id": args.asset_id,
            "endpoint_id": endpoint_id,
            "angle_id": angle_id,
            "angle": angle.name,
            "coverage_family": angle.family,
            "question": angle.question,
            "safe_strategy": angle.safe_strategy,
            "evidence_needed": angle.evidence,
            "anti_bias": "This is an endpoint angle, not an IDOR-only checklist item.",
            "source": args.source,
        }
        if method:
            event["method"] = method
        if args.path:
            event["path"] = args.path
        if args.target:
            event["target"] = args.target
        if args.loop_id:
            event["loop_id"] = args.loop_id
        write_event(events_path, event)
        row = f"| {endpoint_id} | {endpoint_label} | {angle.name} | queued | {event_id} | {angle.question} |"
        append_unique_row(root / "multi-angle-coverage.md", row, coverage_header)
        next_num += 1
        written_angles += 1

    if include_creative:
        existing_creative = {str(e.get("hypothesis_id") or "") for e in events}
        creative_header = (
            "# Creative Exploration\n\n"
            "Use this file to keep AI creative without letting it bypass the workflow.\n\n"
            "Rule:\n\n```text\nthink freely, act safely, record everything\n```\n\n"
            "| ID | Source Signal | Creative Hypothesis | Safe Next Test | Event ID | Status |\n"
            "|---|---|---|---|---|---|\n"
        )
        for signal, hypothesis, safe_next_test in CREATIVE_SEEDS:
            hypothesis_id = f"hyp-{slugify(endpoint_id)}-{slugify(signal)}"
            if hypothesis_id in existing_creative:
                continue
            event_id = f"evt-{next_num:06d}"
            event = {
                "id": event_id,
                "ts": ts,
                "engagement_id": engagement_id,
                "actor": args.actor,
                "type": "creative_hypothesis_added",
                "status": "queued",
                "asset_id": args.asset_id,
                "endpoint_id": endpoint_id,
                "hypothesis_id": hypothesis_id,
                "source_signal": signal,
                "hypothesis": hypothesis,
                "safe_next_test": safe_next_test,
                "source": args.source,
            }
            if method:
                event["method"] = method
            if args.path:
                event["path"] = args.path
            if args.target:
                event["target"] = args.target
            if args.loop_id:
                event["loop_id"] = args.loop_id
            write_event(events_path, event)
            row = f"| {hypothesis_id} | {signal} | {hypothesis} | {safe_next_test} | {event_id} | queued |"
            append_unique_row(root / "creative-exploration.md", row, creative_header)
            next_num += 1
            written_creative += 1

    if not args.no_build:
        build_graph(root)

    print(f"planned {written_angles} endpoint angles for {endpoint_id}")
    print(f"queued {written_creative} creative hypotheses for {endpoint_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
