#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DomainCheck:
    check_id: str
    title: str
    category: str
    objective: str
    next_action: str
    evidence: str
    angles: tuple[str, ...] = ()


@dataclass(frozen=True)
class DomainProfile:
    key: str
    name: str
    source_workflow: str
    operating_rule: str
    checks: tuple[DomainCheck, ...]


PROFILES: dict[str, DomainProfile] = {
    "wp": DomainProfile(
        key="wp",
        name="WordPress plugin depth",
        source_workflow="hunterflowx-domain-profile",
        operating_rule="Route Patchstack/Wordfence first, then audit hooks, nonce, capability, sanitizer context, and local-lab PoC.",
        checks=(
            DomainCheck(
                "wp-platform-routing",
                "Patchstack/Wordfence platform routing",
                "scope/platform",
                "Decide whether the plugin is in scope for Patchstack, Wordfence, both, or neither before investing audit time.",
                "Record install count, updated date, platform scope, privilege threshold, and preferred submission platform.",
                "program scope citation plus platform decision",
            ),
            DomainCheck(
                "wp-plugin-intel",
                "Plugin metadata and known CVE history",
                "target-intel",
                "Collect slug, version, install count, changelog, known CVEs, and feature-by-design notes.",
                "Create plugin-intel notes and link CVE or changelog references to source review priorities.",
                "plugin-intel artifact",
            ),
            DomainCheck(
                "wp-entrypoint-map",
                "Hook and route inventory",
                "mapping",
                "Map add_action, add_filter, shortcode, admin_init, admin_post, wp_ajax, wp_ajax_nopriv, and REST routes.",
                "Create endpoint_discovered or route_source_parsed events for every reachable hook/route.",
                "hook map with source file and line references",
                ("wp_hook_inventory",),
            ),
            DomainCheck(
                "wp-capability-nonce",
                "Capability and nonce enforcement",
                "authorization",
                "Check every AJAX, REST, admin-post, and state-changing handler for current_user_can and nonce verification.",
                "Plan and test low-role, unauth, subscriber, and intended-role controls.",
                "baseline plus low-role/unauth controls",
                ("wp_capability_nonce", "authz_role"),
            ),
            DomainCheck(
                "wp-rest-permission-callback",
                "REST permission_callback coverage",
                "authorization",
                "Verify every register_rest_route has a meaningful permission_callback and object-level checks.",
                "Compare REST route behavior across owned roles and object ownership.",
                "REST route matrix and role/object comparison",
                ("wp_rest_permission_callback", "object_tenant_boundary"),
            ),
            DomainCheck(
                "wp-sanitizer-context",
                "Sanitizer and escaping context",
                "input/output",
                "Read sanitizer behavior and output context before declaring XSS, SQLi, path, or HTML handling safe.",
                "Document sanitizer body, output sink, and 2-3 bypass attempts for every rejected hypothesis.",
                "sanitizer walkthrough and bypass-attempt notes",
                ("wp_sanitizer_context", "input_validation"),
            ),
            DomainCheck(
                "wp-sql-data-layer",
                "SQL and data-layer safety",
                "data/query",
                "Trace $wpdb query, prepare, get_results, options/usermeta, and dynamic table/column names.",
                "Test only context-specific safe markers and prove whether parameters reach query construction.",
                "source-to-query flow and safe test evidence",
                ("wp_sql_data_layer",),
            ),
            DomainCheck(
                "wp-file-upload-url",
                "File, upload, import, and URL handling",
                "file/url",
                "Check upload validation, MIME/type mismatch, path traversal, import parsers, SSRF-like URL fetches, and redirects.",
                "Use harmless owned files and controlled callback endpoints where program rules allow.",
                "upload/fetch request, server response, and callback or storage proof",
                ("wp_file_upload_url", "file_or_url_handling"),
            ),
            DomainCheck(
                "wp-options-privilege",
                "Options, usermeta, and privilege-changing writes",
                "privilege/state",
                "Find writes to options, usermeta, roles, capabilities, settings, and feature flags without proper privilege checks.",
                "Plan role comparison and independent read-back for every write path.",
                "before/after state and low-role control",
                ("wp_options_privilege", "side_effect_write"),
            ),
            DomainCheck(
                "wp-local-lab-poc",
                "Local WordPress lab PoC",
                "runtime/evidence",
                "Reproduce promising findings in a local WP lab before report drafting.",
                "Save lab URL, plugin version, role, raw request/response, screenshot, and reset notes.",
                "local lab evidence pack",
                ("wp_local_lab_poc",),
            ),
        ),
    ),
    "onprem": DomainProfile(
        key="onprem",
        name="On-prem/source product depth",
        source_workflow="hunterflowx-domain-profile",
        operating_rule="Load target intel, sandbox installers, extract source/current, rank files, and keep RESTATE-OK one-file artifacts.",
        checks=(
            DomainCheck(
                "onprem-target-intel",
                "Target intel and rules",
                "scope/target-intel",
                "Populate scope, rules, features-by-design, accepted risks, tech stack, docs, and past findings.",
                "Block claims until target-intel citations are available.",
                "target-intel files and citations",
            ),
            DomainCheck(
                "onprem-install-sandbox",
                "Installer sandbox and smoke test",
                "runtime/setup",
                "Install vendor binary only in Docker/Vagrant/lab and capture ports, processes, defaults, and smoke-test results.",
                "Run smoke/config collection and link output to events.",
                "sandbox notes, config dump, and smoke-test evidence",
            ),
            DomainCheck(
                "onprem-source-extract",
                "Source/current extraction and inventory",
                "source/setup",
                "Extract readable source to source/current and preserve raw installers/configs separately.",
                "Run source-verify with queue-missing after extraction.",
                "source root inventory and source completeness review",
            ),
            DomainCheck(
                "onprem-rank-triad",
                "Ranked one-file triad audit",
                "source/depth",
                "Rank high-risk files and audit exactly one file at a time with RESTATE-OK artifacts.",
                "Create source_file_read, source_flow_linked, attack_surface_mapped, and endpoint_angle_planned events.",
                "source-review artifact per file",
                ("onprem_one_file_triad", "source_runtime_diff"),
            ),
            DomainCheck(
                "onprem-config-secret-defaults",
                "Config, secrets, and insecure defaults",
                "config/defaults",
                "Check default credentials, exposed admin settings, unsafe config, tokens, DB strings, and local-only assumptions.",
                "Verify with lab evidence or mark as hardening note if no bounty impact.",
                "redacted config evidence and lab reachability",
                ("onprem_config_defaults", "data_exposure"),
            ),
            DomainCheck(
                "onprem-auth-session",
                "Auth/session and role model",
                "auth/session",
                "Map users, roles, default groups, session storage, token lifetime, CSRF, SSO, and admin boundaries.",
                "Test owned low-role to high-role paths and record controls.",
                "role/session matrix and request evidence",
                ("onprem_auth_session", "authn_session", "authz_role"),
            ),
            DomainCheck(
                "onprem-admin-api-surface",
                "Admin API, service ports, and internal surfaces",
                "mapping/runtime",
                "Map admin endpoints, service ports, management APIs, debug endpoints, and local-only APIs.",
                "Connect runtime routes to source handlers before testing.",
                "route/source/runtime linkage",
                ("onprem_admin_api_surface", "inventory_version_shadow_api"),
            ),
            DomainCheck(
                "onprem-file-system-rce",
                "File system, import/export, plugin, and command surfaces",
                "file/exec",
                "Trace uploads, imports, backups, report generation, templates, deserialization, shell calls, and plugin loading.",
                "Use non-destructive lab payloads and read-back only inside authorized lab.",
                "lab PoC or blocked-by-scope evidence",
                ("onprem_file_exec_surface", "file_or_url_handling"),
            ),
            DomainCheck(
                "onprem-upgrade-diff",
                "Version diff and patch regression",
                "version/diff",
                "Compare source/current to previous versions, CVE patches, changelog claims, and migration scripts.",
                "Turn diffs into focused tests or accepted-gap notes.",
                "diff artifact and mapped test cards",
                ("onprem_upgrade_diff",),
            ),
            DomainCheck(
                "onprem-reportable-lab-proof",
                "Reportable lab proof",
                "evidence/report",
                "Before reporting, prove impact in sandbox with exact version, setup, request, response, and cleanup.",
                "Run evidence-score and judge on the lab evidence package.",
                "judge_reportable evidence package",
            ),
        ),
    ),
    "mobile": DomainProfile(
        key="mobile",
        name="Mobile app depth",
        source_workflow="hunter",
        operating_rule="Treat mobile as a first-class runtime surface: app package, device traffic, exported components, storage, WebView, API, and Frida/Caido evidence.",
        checks=(
            DomainCheck(
                "mobile-scope-app-inventory",
                "Scope and app inventory",
                "scope/app",
                "Record app package, platform, version, hash, store URL, allowed testing device, accounts, and forbidden actions.",
                "Block mobile testing until the app and account boundaries are explicit.",
                "scope note, app hash, version, and account matrix",
            ),
            DomainCheck(
                "mobile-runtime-capture",
                "Device/browser/proxy runtime capture",
                "runtime/proxy",
                "Capture app traffic through Burp/Caido on emulator or owned physical device where allowed.",
                "Save request/response samples and note TLS/pinning state without bypassing policy.",
                "proxy evidence and device notes",
                ("mobile_runtime_capture",),
            ),
            DomainCheck(
                "mobile-static-decompile",
                "Static decompile and manifest inventory",
                "static/source",
                "Decompile APK/IPA where allowed and map manifest, exported components, permissions, receivers, providers, schemes, and libraries.",
                "Create source review artifacts and source-verify the decompiled source tree.",
                "manifest/source review and source completeness result",
                ("mobile_static_manifest",),
            ),
            DomainCheck(
                "mobile-api-endpoint-diff",
                "Mobile-only API and endpoint diff",
                "mapping/api",
                "Extract API endpoints from strings, code, traffic, deep links, GraphQL, gRPC, and WebViews; compare with web API inventory.",
                "Create endpoint_discovered/js_endpoint_extracted/source_flow_linked events for every mobile-only endpoint.",
                "endpoint diff table and runtime reachability evidence",
                ("mobile_api_endpoint_diff", "inventory_version_shadow_api"),
            ),
            DomainCheck(
                "mobile-auth-token-storage",
                "Token/session storage and auth semantics",
                "auth/storage",
                "Check token storage, refresh flows, logout invalidation, device binding, backup behavior, and account switching.",
                "Use owned accounts and read-back evidence; do not dump third-party data.",
                "storage review and auth/session request evidence",
                ("mobile_auth_token_storage", "authn_session"),
            ),
            DomainCheck(
                "mobile-deeplink-exported",
                "Deep links and exported components",
                "ipc/deeplink",
                "Test custom schemes, app links, exported activities/services/receivers/providers, and intent extra trust.",
                "Use harmless controlled intents and record device-visible result.",
                "intent/deeplink command, logcat, and screenshot",
                ("mobile_deeplink_exported", "client_trust_integrity"),
            ),
            DomainCheck(
                "mobile-webview-bridge",
                "WebView and JS bridge",
                "webview",
                "Map WebView origins, addJavascriptInterface bridges, postMessage, file access, mixed content, and deep link handoff.",
                "Prove bridge reachability with safe markers before exploit claims.",
                "WebView source/runtime proof",
                ("mobile_webview_bridge", "cache_cors_redirect"),
            ),
            DomainCheck(
                "mobile-local-data-secrets",
                "Local data, logs, and secret handling",
                "data/local",
                "Review SharedPreferences, SQLite, files, logs, backups, screenshots, clipboard, and keychain/keystore usage.",
                "Evidence must be redacted and tied to realistic attacker capability.",
                "redacted local storage/log evidence",
                ("mobile_local_data_secrets", "data_exposure"),
            ),
            DomainCheck(
                "mobile-frida-runtime-proof",
                "Runtime instrumentation proof",
                "runtime/instrumentation",
                "Use Frida or equivalent only inside authorized owned-device testing to prove reachability, not to bypass scope.",
                "Save script, target function, logs, and exact reason instrumentation was needed.",
                "Frida/device log and scoped justification",
                ("mobile_frida_runtime_proof",),
            ),
            DomainCheck(
                "mobile-reportable-impact",
                "Mobile reportable impact package",
                "evidence/report",
                "Before report, combine device proof, proxy evidence, source/static link, and impact read-back.",
                "Run evidence-score and judge on the mobile evidence package.",
                "judge_reportable mobile evidence package",
            ),
        ),
    ),
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def root_path(path: Path | None) -> Path:
    return path.resolve() if path else Path.cwd().resolve()


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_events(root: Path, events: list[dict[str, Any]]) -> None:
    path = root / "data/events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0)
            start = sum(1 for line in handle.read().splitlines() if line.strip()) + 1
            handle.seek(0, 2)
            for offset, event in enumerate(events):
                event.setdefault("id", f"evt-{start + offset:06d}")
                event.setdefault("ts", now())
                event.setdefault("engagement_id", current_engagement_id(root))
                event.setdefault("actor", "ai")
                event = {key: value for key, value in event.items() if value != ""}
                handle.write(json.dumps(event, separators=(",", ":")) + "\n")
            handle.flush()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def selected_profiles(name: str) -> list[DomainProfile]:
    if name == "all":
        return [PROFILES[key] for key in ("wp", "onprem", "mobile")]
    if name not in PROFILES:
        raise SystemExit(f"unknown domain profile: {name}")
    return [PROFILES[name]]


def build_graph(root: Path) -> None:
    subprocess.run(["python3", str(ROOT / "scripts/build_graph.py"), "--root", str(root)], check=True)


def plan_profile(root: Path, profile: DomainProfile, args: argparse.Namespace) -> tuple[list[dict[str, Any]], str]:
    events: list[dict[str, Any]] = []
    profile_id = f"domain-{profile.key}"
    events.append(
        {
            "type": "domain_profile_loaded",
            "profile_id": profile_id,
            "domain": profile.key,
            "name": profile.name,
            "source_workflow": profile.source_workflow,
            "status": "domain_planned",
            "checks_total": len(profile.checks),
            "operating_rule": profile.operating_rule,
        }
    )

    lines = [
        f"# {profile.name}",
        "",
        f"- Domain: `{profile.key}`",
        f"- Source workflow: `{profile.source_workflow}`",
        f"- Operating rule: {profile.operating_rule}",
        f"- Endpoint: `{args.endpoint_id or '-'}`",
        f"- Generated: {now()}",
        "",
        "| Check | Category | Objective | Evidence | Next Action |",
        "|---|---|---|---|---|",
    ]

    for check in profile.checks:
        events.append(
            {
                "type": "domain_check_planned",
                "profile_id": profile_id,
                "domain": profile.key,
                "check_id": check.check_id,
                "title": check.title,
                "category": check.category,
                "objective": check.objective,
                "next_action": check.next_action,
                "required_evidence": check.evidence,
                "status": "domain_planned",
                "asset_id": args.asset_id or "",
                "endpoint_id": args.endpoint_id or "",
                "method": args.method or "",
                "path": args.path or "",
            }
        )
        for angle in check.angles:
            if args.endpoint_id:
                events.append(
                    {
                        "type": "endpoint_angle_planned",
                        "asset_id": args.asset_id or "",
                        "endpoint_id": args.endpoint_id,
                        "method": args.method or "",
                        "path": args.path or "",
                        "angle": angle,
                        "angle_id": f"angle-{args.endpoint_id}-{angle}".replace("/", "-"),
                        "domain": profile.key,
                        "domain_check_id": check.check_id,
                        "source": f"domain-plan:{profile.key}",
                        "status": "queued",
                        "reason": check.objective,
                    }
                )
        lines.append(
            "| `{}` | {} | {} | {} | {} |".format(
                check.check_id,
                check.category,
                check.objective.replace("|", "/"),
                check.evidence.replace("|", "/"),
                check.next_action.replace("|", "/"),
            )
        )

    lines.extend(
        [
            "",
            "## Completion Rule",
            "",
            "A check is not complete until it has a `domain_check_completed` event or evidence/events linked with `domain_check_id`.",
            "",
            "Example:",
            "",
            "```bash",
            f"../../../bin/bbf event domain_check_completed --domain {profile.key} --check-id {profile.checks[0].check_id} --status domain_complete --evidence-path evidence/...",
            "```",
            "",
            "After completing a batch:",
            "",
            "```bash",
            f"../../../bin/bbf domain-verify --domain {profile.key}",
            "```",
        ]
    )
    return events, "\n".join(lines) + "\n"


def cmd_plan(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    out_dir = root / "domain-depth"
    out_dir.mkdir(parents=True, exist_ok=True)
    all_events: list[dict[str, Any]] = []
    for profile in selected_profiles(args.domain):
        events, text = plan_profile(root, profile, args)
        all_events.extend(events)
        (out_dir / f"{profile.key}-plan.md").write_text(text, encoding="utf-8")
    write_events(root, all_events)
    if not args.no_build:
        build_graph(root)
    print(f"planned {len(all_events)} domain events in {root}")
    return 0


def completion_state(events: list[dict[str, Any]], check: DomainCheck) -> tuple[str, list[str], list[str]]:
    linked = [event for event in events if str(event.get("domain_check_id") or event.get("check_id") or "") == check.check_id]
    completed = [event for event in linked if event.get("type") == "domain_check_completed"]
    evidence = [
        event
        for event in linked
        if event.get("type") in {"evidence_added", "source_file_read", "source_flow_linked", "attack_surface_mapped", "endpoint_angle_tested", "verdict_set"}
    ]
    if completed:
        latest = completed[-1]
        status = str(latest.get("status") or "domain_complete")
        if status in {"domain_complete", "confirmed", "tested_secure", "evidence_sufficient", "judge_reportable"}:
            return "domain_complete", [], [str(latest.get("evidence_path") or latest.get("review_path") or latest.get("id"))]
        if status in {"blocked", "out_of_scope", "by_design"}:
            return "domain_partial", [f"{check.check_id}: blocked or closed as {status}"], []
        return "domain_partial", [f"{check.check_id}: completion event is {status}"], []
    if evidence:
        refs = [str(event.get("evidence_path") or event.get("source_file") or event.get("id")) for event in evidence[:3]]
        return "domain_partial", [f"{check.check_id}: has linked evidence but no domain_check_completed"], refs
    return "domain_incomplete", [f"{check.check_id}: missing completion evidence"], []


def cmd_verify(args: argparse.Namespace) -> int:
    root = root_path(args.root)
    events = read_jsonl(root / "data/events.jsonl")
    out_dir = root / "domain-depth"
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = selected_profiles(args.domain)
    reviews: list[dict[str, Any]] = []
    event_batch: list[dict[str, Any]] = []
    total = complete = partial = missing = 0
    score_sum = 0
    per_domain_score: dict[str, int] = {}

    for profile in selected:
        rows: list[str] = []
        domain_score_sum = 0
        domain_total = domain_complete = domain_partial = domain_missing = 0
        missing_items: list[str] = []
        rows.append(f"# {profile.name} Review")
        rows.append("")
        rows.append("| Check | Status | Evidence Refs | Missing / Next Action |")
        rows.append("|---|---|---|---|")
        for check in profile.checks:
            status, problems, refs = completion_state(events, check)
            points = 100 if status == "domain_complete" else 50 if status == "domain_partial" else 0
            domain_score_sum += points
            score_sum += points
            total += 1
            domain_total += 1
            if status == "domain_complete":
                complete += 1
                domain_complete += 1
            elif status == "domain_partial":
                partial += 1
                domain_partial += 1
            else:
                missing += 1
                domain_missing += 1
            missing_items.extend(problems)
            rows.append(
                "| `{}` | `{}` | {} | {} |".format(
                    check.check_id,
                    status,
                    "<br>".join(refs) or "-",
                    "<br>".join(problems) or check.next_action.replace("|", "/"),
                )
            )
        score = round(domain_score_sum / domain_total) if domain_total else 0
        per_domain_score[profile.key] = score
        overall_status = "domain_complete" if score >= 85 and domain_missing == 0 else "domain_partial" if score >= 45 else "domain_incomplete"
        review_path = out_dir / f"{profile.key}-review.md"
        rows.extend(
            [
                "",
                "## Metrics",
                "",
                f"- Score: {score}",
                f"- Complete: {domain_complete}",
                f"- Partial: {domain_partial}",
                f"- Missing: {domain_missing}",
                f"- Status: `{overall_status}`",
            ]
        )
        review_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        reviews.append(
            {
                "domain": profile.key,
                "score": score,
                "status": overall_status,
                "checks_total": domain_total,
                "checks_complete": domain_complete,
                "checks_partial": domain_partial,
                "checks_missing": domain_missing,
                "review_path": str(review_path.relative_to(root)),
                "missing": missing_items[:20],
            }
        )

    avg_score = round(score_sum / total, 1) if total else 0
    status = "domain_complete" if avg_score >= 85 and missing == 0 else "domain_partial" if avg_score >= 45 else "domain_incomplete"
    data = {
        "generated_at": now(),
        "status": status,
        "score": avg_score,
        "checks_total": total,
        "checks_complete": complete,
        "checks_partial": partial,
        "checks_missing": missing,
        "domain_scores": per_domain_score,
        "reviews": reviews,
    }
    (root / "data/domain_depth.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    summary = out_dir / "domain-depth-review.md"
    summary.write_text(
        "\n".join(
            [
                "# Domain Depth Review",
                "",
                f"- Generated: {data['generated_at']}",
                f"- Status: `{status}`",
                f"- Average score: {avg_score}",
                f"- Checks total: {total}",
                f"- Complete: {complete}",
                f"- Partial: {partial}",
                f"- Missing: {missing}",
                "",
                "| Domain | Score | Status | Missing | Review |",
                "|---|---:|---|---:|---|",
                *[
                    f"| `{review['domain']}` | {review['score']} | `{review['status']}` | {review['checks_missing']} | `{review['review_path']}` |"
                    for review in reviews
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    event_batch.append(
        {
            "type": "domain_depth_reviewed",
            "status": status,
            "score": avg_score,
            "domains": ",".join(profile.key for profile in selected),
            "checks_total": total,
            "checks_complete": complete,
            "checks_partial": partial,
            "checks_missing": missing,
            "domain_wp_score": per_domain_score.get("wp", 0),
            "domain_onprem_score": per_domain_score.get("onprem", 0),
            "domain_mobile_score": per_domain_score.get("mobile", 0),
            "review_path": str(summary.relative_to(root)),
        }
    )
    write_events(root, event_batch)
    if not args.no_build:
        build_graph(root)
    print(f"domain depth {status}: {avg_score}/100 ({complete} complete, {partial} partial, {missing} missing)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan and verify WP/on-prem/mobile domain-specific depth.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan", help="Create domain-specific depth checks.")
    plan.add_argument("domain", choices=["wp", "onprem", "mobile", "all"])
    plan.add_argument("--root", type=Path, default=Path.cwd())
    plan.add_argument("--asset-id", default="")
    plan.add_argument("--endpoint-id", default="")
    plan.add_argument("--method", default="")
    plan.add_argument("--path", default="")
    plan.add_argument("--no-build", action="store_true")
    plan.set_defaults(func=cmd_plan)

    verify = sub.add_parser("verify", help="Score domain-specific depth completion.")
    verify.add_argument("--domain", choices=["wp", "onprem", "mobile", "all"], default="all")
    verify.add_argument("--root", type=Path, default=Path.cwd())
    verify.add_argument("--no-build", action="store_true")
    verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
