#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_POLICY = {
    "version": "1.0.0",
    "mode": "enforce",
    "max_rps": 10,
    "allow_hosts": [],
    "allow_schemes": ["https", "http"],
    "allow_methods": ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    "forbidden_path_patterns": [
        "*/logout*",
        "*/delete-account*",
        "*/billing/charge*",
        "*/payments/capture*",
        "*/admin/destroy*",
    ],
    "active_testing_requires_approval": True,
    "notes": [
        "Fill allow_hosts before live testing.",
        "Keep max_rps at or below the program rules.",
        "Use owned accounts and non-destructive payloads only.",
    ],
}

_LAST_REQUEST_AT = 0.0


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    warnings: list[str]
    policy_path: str
    max_rps: float


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def policy_path(root: Path) -> Path:
    return root / "data" / "safety_policy.json"


def write_default_policy(root: Path, force: bool = False) -> Path:
    path = policy_path(root)
    if force or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(DEFAULT_POLICY)
        data["generated_at"] = now()
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def load_policy(root: Path) -> tuple[dict[str, Any], Path]:
    path = policy_path(root)
    if not path.exists():
        path = write_default_policy(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid safety policy JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: safety policy must be a JSON object")
    merged = dict(DEFAULT_POLICY)
    merged.update(data)
    return merged, path


def normalize_host(host: str) -> str:
    return host.strip().lower().split(":")[0]


def host_allowed(host: str, allow_hosts: list[str]) -> bool:
    clean = normalize_host(host)
    for pattern in allow_hosts:
        item = normalize_host(str(pattern))
        if not item:
            continue
        if fnmatch.fnmatch(clean, item):
            return True
        if item.startswith("*.") and clean.endswith(item[1:]):
            return True
    return False


def check_request(root: Path, method: str, url: str) -> PolicyDecision:
    policy, path = load_policy(root)
    warnings: list[str] = []
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = parsed.hostname or ""
    method_upper = method.upper()
    max_rps = float(policy.get("max_rps") or 0)

    if not parsed.scheme or not parsed.netloc:
        return PolicyDecision(False, "request URL must be absolute for safety enforcement", warnings, str(path), max_rps)

    allow_hosts = [str(item) for item in policy.get("allow_hosts") or []]
    if not allow_hosts:
        return PolicyDecision(False, "safety policy has no allow_hosts; fill data/safety_policy.json before active testing", warnings, str(path), max_rps)
    if not host_allowed(host, allow_hosts):
        return PolicyDecision(False, f"host `{host}` is outside allow_hosts", warnings, str(path), max_rps)

    allow_schemes = {str(item).lower() for item in policy.get("allow_schemes") or []}
    if scheme not in allow_schemes:
        return PolicyDecision(False, f"scheme `{scheme}` is not allowed", warnings, str(path), max_rps)

    allow_methods = {str(item).upper() for item in policy.get("allow_methods") or []}
    if method_upper not in allow_methods:
        return PolicyDecision(False, f"method `{method_upper}` is not allowed by safety policy", warnings, str(path), max_rps)

    path_value = parsed.path or "/"
    for pattern in policy.get("forbidden_path_patterns") or []:
        if fnmatch.fnmatch(path_value.lower(), str(pattern).lower()):
            return PolicyDecision(False, f"path `{path_value}` matches forbidden pattern `{pattern}`", warnings, str(path), max_rps)

    if max_rps <= 0:
        warnings.append("max_rps is disabled or invalid")
    elif max_rps > 10:
        warnings.append("max_rps is above the recommended default of 10")

    return PolicyDecision(True, "allowed by safety policy", warnings, str(path), max_rps)


def throttle(max_rps: float) -> None:
    global _LAST_REQUEST_AT
    if max_rps <= 0:
        return
    min_interval = 1.0 / max_rps
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _LAST_REQUEST_AT = time.monotonic()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage engagement safety policy gates.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="Create data/safety_policy.json if missing.")
    init.add_argument("--root", type=Path, default=Path.cwd())
    init.add_argument("--force", action="store_true")

    status = sub.add_parser("status", help="Print current safety policy.")
    status.add_argument("--root", type=Path, default=Path.cwd())

    check = sub.add_parser("check", help="Check one request against policy.")
    check.add_argument("--root", type=Path, default=Path.cwd())
    check.add_argument("--method", default="GET")
    check.add_argument("url")

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "init":
        path = write_default_policy(root, force=args.force)
        print(path)
        return 0
    if args.cmd == "status":
        policy, path = load_policy(root)
        print(json.dumps({"path": str(path), "policy": policy}, indent=2))
        return 0
    if args.cmd == "check":
        decision = check_request(root, args.method, args.url)
        print(json.dumps(decision.__dict__, indent=2))
        return 0 if decision.allowed else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
