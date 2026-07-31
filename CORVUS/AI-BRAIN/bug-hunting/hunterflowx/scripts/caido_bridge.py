#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "x-csrf-token", "x-xsrf-token"}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def current_engagement_id(root: Path) -> str:
    parts = root.parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def json_dump(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=True)


def read_events(root: Path) -> list[dict[str, Any]]:
    path = root / "data/events.jsonl"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def write_event(root: Path, event: dict[str, Any]) -> None:
    events = read_events(root)
    event.setdefault("id", f"evt-{len(events) + 1:06d}")
    event.setdefault("ts", now())
    event.setdefault("engagement_id", current_engagement_id(root))
    event.setdefault("actor", "caido")
    with (root / "data/events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json_dump(event) + "\n")


def config_path(root: Path) -> Path:
    return root / ".private" / "caido.json"


def load_config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {
        "ui_listen": "127.0.0.1:18080",
        "proxy_listen": "127.0.0.1:18081",
        "data_path": str(root / ".caido"),
        "graphql_url": "http://127.0.0.1:18080/graphql",
    }


def save_config(root: Path, config: dict[str, Any]) -> Path:
    path = config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    config["updated_at"] = now()
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def caido_binary() -> str:
    return shutil.which("caido-cli") or shutil.which("caido") or ""


def status(root: Path) -> dict[str, Any]:
    config = load_config(root)
    binary = caido_binary()
    version = ""
    if binary:
        try:
            proc = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=5)
            version = (proc.stdout or proc.stderr).strip()
        except Exception:
            version = "unknown"
    return {
        "installed": bool(binary),
        "binary": binary,
        "version": version,
        "config": config,
        "launch_command": launch_command(root, config, binary or "caido-cli"),
        "mode": "native_cli_available" if binary else "proxy_only_until_caido_cli_installed",
    }


def launch_command(root: Path, config: dict[str, Any], binary: str = "caido-cli") -> list[str]:
    return [
        binary,
        "--ui-listen",
        str(config.get("ui_listen") or "127.0.0.1:18080"),
        "--proxy-listen",
        str(config.get("proxy_listen") or "127.0.0.1:18081"),
        "--data-path",
        str(config.get("data_path") or (root / ".caido")),
        "--no-open",
    ]


def slugify(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() or ch in "._-" else "-" for ch in value.strip())
    while "--" in clean:
        clean = clean.replace("--", "-")
    return clean.strip("-") or "item"


def redact_headers(headers: Any) -> dict[str, str]:
    if not isinstance(headers, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in headers.items():
        out[str(key)] = "[redacted]" if str(key).lower() in SENSITIVE_HEADERS else str(value)
    return out


def request_response_from_har(entry: dict[str, Any]) -> dict[str, Any]:
    request = entry.get("request") or {}
    response = entry.get("response") or {}
    url = str(request.get("url") or "")
    parsed = urlparse(url)
    method = str(request.get("method") or "GET").upper()
    req_headers = {str(h.get("name")): str(h.get("value")) for h in request.get("headers") or [] if isinstance(h, dict)}
    res_headers = {str(h.get("name")): str(h.get("value")) for h in response.get("headers") or [] if isinstance(h, dict)}
    body = ""
    post = request.get("postData") or {}
    if isinstance(post, dict):
        body = str(post.get("text") or "")
    res_body = ""
    content = response.get("content") or {}
    if isinstance(content, dict):
        res_body = str(content.get("text") or "")
    return {
        "method": method,
        "url": url,
        "path": parsed.path or "/",
        "request_headers": req_headers,
        "request_body": body,
        "response_status": response.get("status"),
        "response_headers": res_headers,
        "response_body": res_body,
    }


def normalize_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and "log" in data and isinstance(data["log"], dict):
        return [request_response_from_har(entry) for entry in data["log"].get("entries") or [] if isinstance(entry, dict)]
    if isinstance(data, dict) and isinstance(data.get("requests"), list):
        data = data["requests"]
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        data = data["items"]
    if not isinstance(data, list):
        raise SystemExit("import file must be HAR or a JSON list/object with requests/items")
    out: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("target") or item.get("request_url") or "")
        parsed = urlparse(url)
        out.append(
            {
                "method": str(item.get("method") or "GET").upper(),
                "url": url,
                "path": str(item.get("path") or parsed.path or "/"),
                "request_headers": item.get("request_headers") or item.get("headers") or {},
                "request_body": str(item.get("request_body") or item.get("body") or ""),
                "response_status": item.get("response_status") or item.get("status"),
                "response_headers": item.get("response_headers") or {},
                "response_body": str(item.get("response_body") or item.get("response") or ""),
                "source_id": item.get("id") or item.get("request_id") or "",
            }
        )
    return out


def write_imported_evidence(root: Path, source: str, record: dict[str, Any], endpoint_id: str, test_id: str, index: int) -> str:
    folder = root / "evidence" / source / "imported"
    folder.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(str(record.get("url") or ""))
    stem = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{index:03d}-{slugify(record.get('method', 'GET'))}-{slugify(parsed.path or 'request')}"
    path = folder / f"{stem}.http.txt"
    path.write_text(
        "# Imported Proxy History Evidence\n\n"
        f"- Source: `{source}`\n"
        f"- Endpoint: `{endpoint_id or '-'}`\n"
        f"- Test ID: `{test_id or '-'}`\n"
        f"- Imported at: `{now()}`\n\n"
        "## Request\n\n"
        f"{record.get('method', 'GET')} {record.get('url', '')}\n\n"
        "Headers:\n"
        f"{json.dumps(redact_headers(record.get('request_headers') or {}), indent=2)}\n\n"
        "Body:\n"
        f"{record.get('request_body') or '-'}\n\n"
        "## Response\n\n"
        f"Status: {record.get('response_status') or '-'}\n\n"
        "Headers:\n"
        f"{json.dumps(redact_headers(record.get('response_headers') or {}), indent=2)}\n\n"
        "Body preview:\n"
        f"{str(record.get('response_body') or '-')[:120000]}\n",
        encoding="utf-8",
    )
    return str(path.relative_to(root))


def import_history(root: Path, source: str, file_path: Path, endpoint_id: str, test_id: str, limit: int) -> dict[str, Any]:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    records = normalize_records(data)[:limit]
    imported = []
    for index, record in enumerate(records, 1):
        evidence_path = write_imported_evidence(root, source, record, endpoint_id, test_id, index)
        event = {
            "type": "proxy_history_imported",
            "status": "saved",
            "source": source,
            "source_request_id": record.get("source_id") or "",
            "endpoint_id": endpoint_id,
            "test_id": test_id,
            "method": record.get("method"),
            "target": record.get("url"),
            "path": record.get("path"),
            "response_status": record.get("response_status"),
            "evidence_path": evidence_path,
        }
        write_event(root, event)
        write_event(
            root,
            {
                "type": "evidence_added",
                "status": "saved",
                "source": source,
                "endpoint_id": endpoint_id,
                "test_id": test_id,
                "method": record.get("method"),
                "target": record.get("url"),
                "path": record.get("path"),
                "response_status": record.get("response_status"),
                "evidence_path": evidence_path,
                "evidence_type": f"{source}_proxy_history",
            },
        )
        if endpoint_id:
            write_event(
                root,
                {
                    "type": "endpoint_seen_runtime",
                    "status": "mapped_runtime",
                    "source": source,
                    "endpoint_id": endpoint_id,
                    "method": record.get("method"),
                    "path": record.get("path"),
                    "target": record.get("url"),
                },
            )
        imported.append({"path": evidence_path, "method": record.get("method"), "url": record.get("url")})
    return {"imported": len(imported), "records": imported}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Caido CLI/native import bridge.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ["status", "command", "init"]:
        p = sub.add_parser(name)
        p.add_argument("--root", type=Path, default=Path.cwd())
        p.add_argument("--ui-listen", default="")
        p.add_argument("--proxy-listen", default="")
        p.add_argument("--data-path", default="")
    imp = sub.add_parser("import", help="Import Caido/Burp exported history JSON or HAR into evidence.")
    imp.add_argument("--root", type=Path, default=Path.cwd())
    imp.add_argument("--source", choices=["caido", "burp"], default="caido")
    imp.add_argument("--file", type=Path, required=True)
    imp.add_argument("--endpoint-id", default="")
    imp.add_argument("--test-id", default="")
    imp.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "init":
        config = load_config(root)
        if args.ui_listen:
            config["ui_listen"] = args.ui_listen
        if args.proxy_listen:
            config["proxy_listen"] = args.proxy_listen
        if args.data_path:
            config["data_path"] = args.data_path
        path = save_config(root, config)
        print(path)
    elif args.cmd == "status":
        print(json.dumps(status(root), indent=2))
    elif args.cmd == "command":
        config = load_config(root)
        binary = caido_binary() or "caido-cli"
        print(" ".join(launch_command(root, config, binary)))
    elif args.cmd == "import":
        print(json.dumps(import_history(root, args.source, args.file, args.endpoint_id, args.test_id, args.limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
