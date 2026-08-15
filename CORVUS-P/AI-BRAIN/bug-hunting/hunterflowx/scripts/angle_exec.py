#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener

import safety_policy


ROOT = Path(__file__).resolve().parents[1]
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
REJECT_STATUSES = {401, 403, 404, 405, 407}
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "x-csrf-token", "x-xsrf-token"}


@dataclass
class Case:
    name: str
    method: str
    url: str
    headers: dict[str, str]
    body: bytes | None
    intent: str


@dataclass
class Result:
    case: Case
    status: int | None
    headers: dict[str, str]
    body: bytes
    error: str
    evidence_path: str


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


def parse_header(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise SystemExit(f"header must be 'Name: value': {value}")
    name, header_value = value.split(":", 1)
    return name.strip(), header_value.strip()


def load_headers(args: argparse.Namespace) -> dict[str, str]:
    headers: dict[str, str] = {}
    if args.headers_file:
        data = json.loads(args.headers_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit("--headers-file must contain a JSON object")
        headers.update({str(k): str(v) for k, v in data.items()})
    for item in args.header or []:
        name, value = parse_header(item)
        headers[name] = value
    return headers


def load_alt_headers(args: argparse.Namespace) -> dict[str, str]:
    if not args.alt_headers_file:
        return {}
    data = json.loads(args.alt_headers_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("--alt-headers-file must contain a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def load_body(args: argparse.Namespace) -> bytes | None:
    if args.body_file:
        return args.body_file.read_bytes()
    if args.body:
        return args.body.encode("utf-8")
    return None


def strip_auth(headers: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in {"authorization", "cookie", "x-api-key", "x-csrf-token", "x-xsrf-token"}}


def has_auth(headers: dict[str, str]) -> bool:
    return any(k.lower() in {"authorization", "cookie", "x-api-key"} for k in headers)


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            redacted[key] = "[redacted]"
        else:
            redacted[key] = value
    return redacted


def body_preview(body: bytes | None, limit: int) -> str:
    if not body:
        return ""
    return body[:limit].decode("utf-8", errors="replace")


def add_query(url: str, pairs: dict[str, str]) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update(pairs)
    return urlunparse(parsed._replace(query=urlencode(query)))


def apply_replacements(value: str, replacements: list[str]) -> str:
    out = value
    for item in replacements:
        if "=" not in item:
            raise SystemExit(f"--replace must be OLD=NEW: {item}")
        old, new = item.split("=", 1)
        out = out.replace(old, new)
    return out


def make_url(base_url: str, path: str, target: str, explicit_url: str) -> str:
    if explicit_url:
        return explicit_url
    if target and target.startswith(("http://", "https://")):
        return target
    if not base_url:
        raise SystemExit("--base-url or --url is required for active execution")
    return urljoin(base_url.rstrip("/") + "/", (path or target or "/").lstrip("/"))


def planned_angles(events: list[dict[str, Any]], endpoint_id: str, angle_filter: str, rerun: bool) -> list[dict[str, Any]]:
    tested = {
        str(event.get("angle_id") or "")
        for event in events
        if event.get("type") == "endpoint_angle_tested" and event.get("status") not in {"queued", "not_tested"}
    }
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in events:
        if event.get("type") != "endpoint_angle_planned":
            continue
        if endpoint_id and str(event.get("endpoint_id") or "") != endpoint_id:
            continue
        if angle_filter and str(event.get("angle") or "") != angle_filter:
            continue
        angle_id = str(event.get("angle_id") or f"angle-{event.get('endpoint_id')}-{event.get('angle')}")
        if angle_id in seen:
            continue
        if angle_id in tested and not rerun:
            continue
        seen.add(angle_id)
        out.append(event)
    return out


def build_cases(
    *,
    angle: str,
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    replacements: list[str],
    alt_headers: dict[str, str],
    callback_url: str,
    variant_url: str,
    variant_body: bytes | None,
) -> tuple[list[Case], str]:
    cases = [Case("baseline", method, url, headers, body, "baseline control request")]
    blocked = ""
    marker = f"bbf-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:8]}"

    if variant_url:
        cases.append(Case("operator_variant", method, variant_url, headers, variant_body if variant_body is not None else body, "operator-supplied variant URL/body"))
        return cases, blocked

    if replacements:
        changed_url = apply_replacements(url, replacements)
        changed_body = apply_replacements(body.decode("utf-8", errors="replace"), replacements).encode("utf-8") if body else body
        cases.append(Case("replacement_variant", method, changed_url, headers, changed_body, "operator-supplied replacement variant"))
        return cases, blocked

    if angle == "authn_session":
        if has_auth(headers):
            cases.append(Case("no_auth", method, url, strip_auth(headers), body, "same request with auth material stripped"))
        else:
            blocked = "authn_session requires auth headers or cookies to test no-auth boundary"
    elif angle in {"authz_role", "field_level_authorization"}:
        if alt_headers:
            cases.append(Case("alt_role", method, url, alt_headers, body, "same request using alternate role/account headers"))
        else:
            blocked = f"{angle} requires --alt-headers-file or --replace to compare another role/account"
    elif angle == "object_tenant_boundary":
        blocked = "object_tenant_boundary requires --replace OLD=NEW for owned object/tenant/account identifiers"
    elif angle in {"input_validation", "error_oracle", "search_filter_sort_pagination"}:
        cases.append(Case("safe_probe_query", method, add_query(url, {"_bbf_probe": marker}), headers, body, "safe marker query parameter"))
    elif angle in {"data_exposure", "inventory_version_shadow_api"}:
        cases.append(Case("field_expand_probe", method, add_query(url, {"fields": "*", "_bbf_probe": marker}), headers, body, "safe field expansion/inventory probe"))
    elif angle == "cache_cors_redirect":
        variant_headers = dict(headers)
        variant_headers.setdefault("Origin", "https://bbf.invalid")
        cases.append(Case("origin_probe", method, url, variant_headers, body, "controlled Origin header probe"))
    elif angle == "method_content_type_variance":
        variant_headers = dict(headers)
        variant_headers.setdefault("Content-Type", "application/json")
        variant_method = "HEAD" if method == "GET" else method
        cases.append(Case("method_content_type_probe", variant_method, url, variant_headers, body, "safe method/content-type variance"))
    elif angle in {"file_or_url_handling", "notification_webhook_callback"}:
        if callback_url:
            cases.append(Case("callback_url_probe", method, add_query(url, {"url": callback_url}), headers, body, "controlled callback URL probe"))
        else:
            blocked = f"{angle} requires --callback-url for safe external interaction proof"
    else:
        blocked = f"{angle} needs a target-specific manual variant; baseline will be captured only"

    return cases, blocked


def opener_for(proxy: str, insecure: bool):
    handlers = []
    if proxy:
        handlers.append(ProxyHandler({"http": proxy, "https": proxy}))
    if insecure:
        handlers.append(HTTPSHandler(context=ssl._create_unverified_context()))
    return build_opener(*handlers)


def send_http(case: Case, *, proxy: str, insecure: bool, timeout: int, max_body: int) -> tuple[int | None, dict[str, str], bytes, str]:
    request = Request(case.url, data=case.body, headers=case.headers, method=case.method)
    opener = opener_for(proxy, insecure)
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read(max_body), ""
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read(max_body), ""
    except URLError as exc:
        return None, {}, b"", str(exc)
    except TimeoutError as exc:
        return None, {}, b"", str(exc)


def send_browser(case: Case, *, proxy: str, timeout: int, max_body: int, screenshot_path: Path | None) -> tuple[int | None, dict[str, str], bytes, str]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - optional dependency
        return None, {}, b"", f"playwright is not installed or unavailable: {exc}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": proxy} if proxy else None,
            )
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.set_default_timeout(timeout * 1000)
            if case.method == "GET":
                response = page.goto(case.url, wait_until="networkidle")
                body = page.content().encode("utf-8")[:max_body]
                status = response.status if response else None
                headers = response.headers if response else {}
            else:
                origin = f"{urlparse(case.url).scheme}://{urlparse(case.url).netloc}/"
                page.goto(origin, wait_until="domcontentloaded")
                result = page.evaluate(
                    """async ({url, method, headers, body}) => {
                      const res = await fetch(url, {method, headers, body, credentials: 'include'});
                      return {status: res.status, headers: Object.fromEntries(res.headers.entries()), body: await res.text()};
                    }""",
                    {
                        "url": case.url,
                        "method": case.method,
                        "headers": case.headers,
                        "body": case.body.decode("utf-8", errors="replace") if case.body else None,
                    },
                )
                status = int(result["status"])
                headers = {str(k): str(v) for k, v in result["headers"].items()}
                body = str(result["body"]).encode("utf-8")[:max_body]
            if screenshot_path:
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()
            return status, headers, body, ""
    except Exception as exc:  # pragma: no cover - runtime browser failures
        return None, {}, b"", str(exc)


def write_evidence(root: Path, run_id: str, case: Case, status: int | None, headers: dict[str, str], body: bytes, error: str, transport: str, max_body: int) -> str:
    evidence_dir = root / "evidence/responses"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"{run_id}-{case.name}.http.txt"
    text = [
        f"# {run_id} {case.name}",
        "",
        "## Request",
        "",
        f"{case.method} {case.url}",
        "",
        "Headers:",
        json.dumps(redact_headers(case.headers), indent=2),
        "",
        "Body:",
        body_preview(case.body, max_body) or "-",
        "",
        "## Response",
        "",
        f"Transport: {transport}",
        f"Status: {status if status is not None else '-'}",
        f"Error: {error or '-'}",
        "",
        "Headers:",
        json.dumps(redact_headers(headers), indent=2),
        "",
        "Body preview:",
        body_preview(body, max_body) or "-",
        "",
    ]
    path.write_text("\n".join(text), encoding="utf-8")
    return str(path.relative_to(root))


def write_proxy_note(root: Path, run_id: str, transport: str, proxy: str, results: list[Result]) -> str:
    folder = "burp" if transport == "burp" else "caido"
    evidence_dir = root / f"evidence/{folder}"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"{run_id}-proxy-note.md"
    rows = "\n".join(f"- {result.case.name}: {result.case.method} {result.case.url} -> {result.status or result.error}" for result in results)
    path.write_text(
        f"# {transport.title()} Proxy Evidence Note\n\n"
        f"Run ID: `{run_id}`\n\n"
        f"Proxy: `{proxy}`\n\n"
        "The executor sent these requests through the configured proxy, so they should be visible in the proxy history:\n\n"
        f"{rows}\n",
        encoding="utf-8",
    )
    return str(path.relative_to(root))


def classify(angle: str, results: list[Result], blocked: str, auth_headers_present: bool) -> tuple[str, str]:
    if not results:
        return "blocked", blocked or "no request was executed"
    if all(result.error.startswith("safety policy blocked:") for result in results if result.error):
        return "blocked", "safety policy blocked every attempted request"
    if any(result.error for result in results):
        return "inconclusive", "one or more requests failed at transport level"
    baseline = results[0]
    variant = results[1] if len(results) > 1 else None
    if blocked and not variant:
        return "blocked", blocked
    if not variant:
        return "inconclusive", "baseline captured but no safe automatic variant was available"
    if baseline.status is None or variant.status is None:
        return "inconclusive", "missing HTTP status"
    baseline_ok = 200 <= baseline.status < 400
    variant_rejected = variant.status in REJECT_STATUSES or variant.status in {429}
    variant_ok = 200 <= variant.status < 400

    if angle == "authn_session":
        if auth_headers_present and baseline_ok and variant_rejected:
            return "tested_secure", "authenticated baseline succeeded and stripped-auth variant was rejected"
        if auth_headers_present and baseline_ok and variant_ok:
            return "finding_candidate", "stripped-auth variant still returned a successful response; review impact manually"
        return "inconclusive", "authn behavior did not produce a clear accept/reject boundary"

    if angle in {"authz_role", "object_tenant_boundary", "field_level_authorization"}:
        if baseline_ok and variant_rejected:
            return "tested_secure", "control succeeded and authorization/object variant was rejected"
        if baseline_ok and variant_ok:
            return "finding_candidate", "authorization/object variant succeeded; verify ownership and impact manually"
        return "inconclusive", "authorization variant did not produce a clear result"

    if variant.status >= 500:
        return "inconclusive", "safe variant produced server error; needs manual repeatability and impact review"
    return "test_attempted", "baseline and safe variant captured for manual review"


def append_test_ledger(root: Path, run_id: str, angle: str, endpoint_id: str, method: str, url: str, status: str, reason: str, results: list[Result]) -> None:
    path = root / "test-ledger.md"
    if not path.exists():
        path.write_text("# Test Ledger\n\n", encoding="utf-8")
    evidence_lines = "\n".join(f"- {result.case.name}: `{result.evidence_path}` ({result.status or result.error})" for result in results)
    with path.open("a", encoding="utf-8") as f:
        f.write(
            f"\n## {run_id} - {angle} - {endpoint_id}\n\n"
            f"- Method/URL: `{method} {url}`\n"
            f"- Executor verdict: `{status}`\n"
            f"- Reason: {reason}\n"
            f"- Evidence:\n{evidence_lines or '- none'}\n"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute queued endpoint angles through HTTP/browser/Burp/Caido and write evidence-backed events.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--endpoint-id", default="")
    parser.add_argument("--angle", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--method", default="")
    parser.add_argument("--path", default="")
    parser.add_argument("--target", default="")
    parser.add_argument("--transport", choices=["http", "browser", "burp", "caido"], default="burp")
    parser.add_argument("--proxy", default="", help="Proxy URL. Burp/Caido default to http://127.0.0.1:8080")
    parser.add_argument("--header", action="append", help="Header as 'Name: value'. Repeatable.")
    parser.add_argument("--headers-file", type=Path, help="JSON object of headers for the baseline session.")
    parser.add_argument("--alt-headers-file", type=Path, help="JSON object of headers for alternate role/account.")
    parser.add_argument("--body", default="")
    parser.add_argument("--body-file", type=Path)
    parser.add_argument("--variant-url", default="")
    parser.add_argument("--variant-body", default="")
    parser.add_argument("--readback-url", default="", help="Optional read-back URL to verify state or visible result.")
    parser.add_argument("--readback-method", default="GET")
    parser.add_argument("--replace", action="append", default=[], help="Replace OLD=NEW in URL/body for owned object/tenant tests.")
    parser.add_argument("--callback-url", default="", help="Controlled callback URL for URL/webhook angles.")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="Execute all matching queued angles.")
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--allow-active", action="store_true", help="Required to send network traffic.")
    parser.add_argument("--allow-state-change", action="store_true", help="Allow non-GET/HEAD/OPTIONS requests.")
    parser.add_argument("--policy-mode", choices=["enforce", "warn", "off"], default="enforce", help="Apply data/safety_policy.json before sending requests.")
    parser.add_argument("--verify-tls", action="store_true", help="Verify TLS even through local intercepting proxy.")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--max-body", type=int, default=65536)
    parser.add_argument("--actor", default="ai")
    parser.add_argument("--no-auto-verdict", dest="auto_verdict", action="store_false", help="Skip automatic non-confirmed verdict_set event.")
    parser.set_defaults(auto_verdict=True)
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args(argv)

    if not args.allow_active:
        raise SystemExit("refusing active execution without --allow-active")

    root = args.root.resolve()
    events_path = root / "data/events.jsonl"
    events = read_events(events_path)
    engagement_id = current_engagement_id(root)
    headers = load_headers(args)
    alt_headers = load_alt_headers(args)
    body = load_body(args)
    variant_body = args.variant_body.encode("utf-8") if args.variant_body else None
    proxy = args.proxy or ("http://127.0.0.1:8080" if args.transport in {"burp", "caido"} else "")
    insecure = not args.verify_tls and args.transport in {"burp", "caido", "browser"}
    candidates = planned_angles(events, args.endpoint_id, args.angle, args.rerun)
    if not candidates:
        raise SystemExit("no matching queued endpoint_angle_planned events found")
    if not args.all:
        candidates = candidates[: max(1, args.limit)]

    next_num = len(events) + 1
    executed = 0
    for planned in candidates:
        angle = str(planned.get("angle") or args.angle or "angle")
        angle_id = str(planned.get("angle_id") or f"angle-{planned.get('endpoint_id')}-{angle}")
        endpoint_id = str(planned.get("endpoint_id") or args.endpoint_id)
        method = (args.method or str(planned.get("method") or "GET")).upper()
        path = args.path or str(planned.get("path") or "")
        target = args.target or str(planned.get("target") or "")
        url = make_url(args.base_url, path, target, args.url)
        ts = now()
        run_digest = hashlib.sha1(f"{ts}|{engagement_id}|{endpoint_id}|{angle_id}|{url}".encode("utf-8")).hexdigest()[:8]
        run_id = f"angle-{slugify(endpoint_id)}-{slugify(angle)}-{run_digest}"
        test_id = f"test-{run_id}"

        write_event(
            events_path,
            {
                "id": f"evt-{next_num:06d}",
                "ts": ts,
                "engagement_id": engagement_id,
                "actor": args.actor,
                "type": "test_started",
                "status": "test_attempted",
                "test_id": test_id,
                "endpoint_id": endpoint_id,
                "angle_id": angle_id,
                "angle": angle,
                "method": method,
                "path": path,
                "target": target or url,
                "transport": args.transport,
                "proxy": proxy,
                "executor": "bbf angle-exec",
            },
        )
        next_num += 1

        results: list[Result] = []
        blocked = ""
        if method not in SAFE_METHODS and not args.allow_state_change:
            blocked = f"{method} may change state; rerun with --allow-state-change only if scope allows it"
            cases: list[Case] = []
        else:
            cases, blocked = build_cases(
                angle=angle,
                method=method,
                url=url,
                headers=headers,
                body=body,
                replacements=args.replace,
                alt_headers=alt_headers,
                callback_url=args.callback_url,
                variant_url=args.variant_url,
                variant_body=variant_body,
            )
            readback_method = args.readback_method.upper()
            if args.readback_url:
                if readback_method not in SAFE_METHODS and not args.allow_state_change:
                    blocked = "read-back method may change state; rerun with --allow-state-change only if scope allows it"
                else:
                    cases.append(Case("read_back", readback_method, args.readback_url, headers, None, "operator-supplied read-back proof"))

        for index, case in enumerate(cases):
            screenshot = root / "evidence/screenshots" / f"{run_id}-{case.name}.png" if args.transport == "browser" and index == 0 else None
            policy_warning = ""
            if args.policy_mode != "off":
                decision = safety_policy.check_request(root, case.method, case.url)
                if not decision.allowed and args.policy_mode == "enforce":
                    status, response_headers, response_body, error = None, {}, b"", f"safety policy blocked: {decision.reason}"
                else:
                    policy_warning = "; ".join(([decision.reason] if not decision.allowed else []) + decision.warnings)
                    safety_policy.throttle(decision.max_rps)
                    if args.transport == "browser":
                        status, response_headers, response_body, error = send_browser(case, proxy=proxy, timeout=args.timeout, max_body=args.max_body, screenshot_path=screenshot)
                    else:
                        status, response_headers, response_body, error = send_http(case, proxy=proxy, insecure=insecure, timeout=args.timeout, max_body=args.max_body)
            else:
                if args.transport == "browser":
                    status, response_headers, response_body, error = send_browser(case, proxy=proxy, timeout=args.timeout, max_body=args.max_body, screenshot_path=screenshot)
                else:
                    status, response_headers, response_body, error = send_http(case, proxy=proxy, insecure=insecure, timeout=args.timeout, max_body=args.max_body)
            evidence_path = write_evidence(root, run_id, case, status, response_headers, response_body, error, args.transport, args.max_body)
            result = Result(case=case, status=status, headers=response_headers, body=response_body, error=error, evidence_path=evidence_path)
            results.append(result)

            event_type = "control_request_sent" if index == 0 else "payload_attempted"
            write_event(
                events_path,
                {
                    "id": f"evt-{next_num:06d}",
                    "ts": now(),
                    "engagement_id": engagement_id,
                    "actor": args.actor,
                    "type": event_type,
                    "status": "test_attempted" if not error else "inconclusive",
                    "test_id": test_id,
                    "endpoint_id": endpoint_id,
                    "angle_id": angle_id,
                    "angle": angle,
                    "method": case.method,
                    "target": case.url,
                    "case": case.name,
                    "response_status": status,
                    "transport_error": error,
                    "policy_mode": args.policy_mode,
                    "policy_warning": policy_warning,
                    "evidence_path": evidence_path,
                },
            )
            next_num += 1

            write_event(
                events_path,
                {
                    "id": f"evt-{next_num:06d}",
                    "ts": now(),
                    "engagement_id": engagement_id,
                    "actor": args.actor,
                    "type": "evidence_added",
                    "status": "saved",
                    "test_id": test_id,
                    "endpoint_id": endpoint_id,
                    "angle_id": angle_id,
                    "angle": angle,
                    "evidence_id": f"ev-{run_id}-{case.name}",
                    "evidence_path": evidence_path,
                    "evidence_type": f"{args.transport}_http_response",
                    "response_status": status,
                },
            )
            next_num += 1

            if screenshot:
                screenshot_rel = str(screenshot.relative_to(root))
                write_event(
                    events_path,
                    {
                        "id": f"evt-{next_num:06d}",
                        "ts": now(),
                        "engagement_id": engagement_id,
                        "actor": args.actor,
                        "type": "evidence_added",
                        "status": "saved",
                        "test_id": test_id,
                        "endpoint_id": endpoint_id,
                        "angle_id": angle_id,
                        "angle": angle,
                        "evidence_id": f"ev-{run_id}-screenshot",
                        "evidence_path": screenshot_rel,
                        "evidence_type": "browser_screenshot",
                    },
                )
                next_num += 1

        if args.transport in {"burp", "caido"} and results:
            note = write_proxy_note(root, run_id, args.transport, proxy, results)
            write_event(
                events_path,
                {
                    "id": f"evt-{next_num:06d}",
                    "ts": now(),
                    "engagement_id": engagement_id,
                    "actor": args.actor,
                    "type": "evidence_added",
                    "status": "saved",
                    "test_id": test_id,
                    "endpoint_id": endpoint_id,
                    "angle_id": angle_id,
                    "angle": angle,
                    "evidence_id": f"ev-{run_id}-{args.transport}-note",
                    "evidence_path": note,
                    "evidence_type": f"{args.transport}_proxy_note",
                },
            )
            next_num += 1

        if not results:
            log_dir = root / "evidence/logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"{run_id}-blocked.md"
            log_path.write_text(f"# Blocked Angle Execution\n\nReason: {blocked}\n", encoding="utf-8")
            evidence_path = str(log_path.relative_to(root))
            write_event(
                events_path,
                {
                    "id": f"evt-{next_num:06d}",
                    "ts": now(),
                    "engagement_id": engagement_id,
                    "actor": args.actor,
                    "type": "evidence_added",
                    "status": "saved",
                    "test_id": test_id,
                    "endpoint_id": endpoint_id,
                    "angle_id": angle_id,
                    "angle": angle,
                    "evidence_id": f"ev-{run_id}-blocked",
                    "evidence_path": evidence_path,
                    "evidence_type": "blocked_execution_log",
                },
            )
            next_num += 1

        final_status, reason = classify(angle, results, blocked, has_auth(headers))
        evidence_paths = [result.evidence_path for result in results]
        write_event(
            events_path,
            {
                "id": f"evt-{next_num:06d}",
                "ts": now(),
                "engagement_id": engagement_id,
                "actor": args.actor,
                "type": "endpoint_angle_tested",
                "status": final_status,
                "test_id": test_id,
                "endpoint_id": endpoint_id,
                "angle_id": angle_id,
                "angle": angle,
                "method": method,
                "path": path,
                "target": url,
                "transport": args.transport,
                "proxy": proxy,
                "baseline_status": results[0].status if results else None,
                "variant_status": results[1].status if len(results) > 1 else None,
                "evidence_paths": evidence_paths,
                "reason": reason,
            },
        )
        next_num += 1

        if args.auto_verdict:
            write_event(
                events_path,
                {
                    "id": f"evt-{next_num:06d}",
                    "ts": now(),
                    "engagement_id": engagement_id,
                    "actor": args.actor,
                    "type": "verdict_set",
                    "status": final_status if final_status in {"tested_secure", "finding_candidate", "inconclusive", "blocked"} else "inconclusive",
                    "test_id": test_id,
                    "endpoint_id": endpoint_id,
                    "angle_id": angle_id,
                    "angle": angle,
                    "reason": reason,
                    "note": "auto verdict is never confirmed; manual evidence review is required before reporting",
                },
            )
            next_num += 1

        append_test_ledger(root, run_id, angle, endpoint_id, method, url, final_status, reason, results)
        executed += 1
        print(f"{angle_id}: {final_status} - {reason}")

    if not args.no_build:
        build_graph(root)
    print(f"executed {executed} angle(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
