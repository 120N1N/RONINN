#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

from build_graph import build, read_jsonl


ACTOR = "reconfw-bridge"
ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        if isinstance(raw, dict):
            records.append(raw)
    return records


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def sanitize(value: str, prefix: str, limit: int = 80) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower()).strip("-")
    if not clean:
        clean = sha256(value.encode()).hexdigest()[:16]
    if len(clean) > limit:
        clean = f"{clean[: limit - 17]}-{sha256(value.encode()).hexdigest()[:16]}"
    return f"{prefix}{clean}"


def hash_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts if part is not None)
    return f"{prefix}{sha256(raw.encode()).hexdigest()[:20]}"


def event_id(source_file: str, event_type: str, key: str) -> str:
    return f"evt-reconfw-{sha256(f'{source_file}|{event_type}|{key}'.encode()).hexdigest()[:24]}"


def engagement_id(root: Path) -> str:
    parts = root.resolve().parts
    if "engagements" in parts:
        idx = parts.index("engagements")
        if len(parts) > idx + 2:
            return f"{parts[idx + 1]}-{parts[idx + 2]}"
    return root.name


def host_from_url(value: str) -> str:
    parsed = urlparse(value.replace("wss://", "https://").replace("ws://", "http://"))
    return (parsed.hostname or "").lower().rstrip(".")


def path_from_url(value: str) -> str:
    parsed = urlparse(value.replace("wss://", "https://").replace("ws://", "http://"))
    path = parsed.path or "/"
    return path if path.startswith("/") else f"/{path}"


def query_params(value: str) -> list[str]:
    return sorted({key for key, _ in parse_qsl(urlparse(value).query, keep_blank_values=True)})


def asset_id_for_host(host: str) -> str:
    return sanitize(host, "asset-")


def endpoint_id(method: str, host: str, path: str, transport: str = "http") -> str:
    return hash_id("ep-", transport, method.upper(), host.lower(), path)


def safe_source_refs(record: dict[str, Any]) -> list[dict[str, Any]]:
    refs = record.get("source_refs")
    return refs if isinstance(refs, list) else []


def raw_paths(record: dict[str, Any]) -> list[str]:
    values = record.get("raw_evidence_paths") or record.get("evidence_paths") or []
    if isinstance(values, list):
        return [str(value) for value in values]
    if values:
        return [str(values)]
    return []


def base_event(
    *,
    event_type: str,
    source_workspace: Path,
    source_file: Path,
    record: dict[str, Any],
    key: str,
    engagement: str,
) -> dict[str, Any]:
    source_file_rel = rel(source_file, source_workspace)
    return {
        "id": event_id(source_file_rel, event_type, key),
        "ts": str(record.get("first_seen") or record.get("retrieved_at") or record.get("created_at") or now()),
        "engagement_id": engagement,
        "actor": ACTOR,
        "type": event_type,
        "source": f"reconfw:{source_file_rel}",
        "source_tool": "hunterweb/recon-framework",
        "source_workspace": str(source_workspace),
        "source_file": source_file_rel,
        "source_record_id": record.get("id"),
        "source_dedupe_key": record.get("dedupe_key"),
        "source_refs": safe_source_refs(record),
        "raw_evidence_paths": raw_paths(record),
    }


class Importer:
    def __init__(self, source: Path, root: Path, *, dry_run: bool = False) -> None:
        self.source = source.resolve()
        self.root = root.resolve()
        self.engagement = engagement_id(self.root)
        self.dry_run = dry_run
        self.events_path = self.root / "data" / "events.jsonl"
        self.existing_ids = self._existing_event_ids()
        self.events: list[dict[str, Any]] = []
        self.counts: dict[str, int] = {}

    def _existing_event_ids(self) -> set[str]:
        if not self.events_path.exists():
            return set()
        return {str(item.get("id")) for item in read_records(self.events_path) if item.get("id")}

    def emit(self, event: dict[str, Any]) -> None:
        if event["id"] in self.existing_ids:
            self.counts["skipped_existing"] = self.counts.get("skipped_existing", 0) + 1
            return
        self.events.append(event)
        self.existing_ids.add(event["id"])
        self.counts[event["type"]] = self.counts.get(event["type"], 0) + 1

    def emit_host_asset(self, host: str, source_file: Path, record: dict[str, Any], reason: str = "host") -> str:
        host = host.lower().rstrip(".")
        asset_id = asset_id_for_host(host)
        event = base_event(
            event_type="asset_added",
            source_workspace=self.source,
            source_file=source_file,
            record=record,
            key=f"host:{host}:{reason}",
            engagement=self.engagement,
        )
        event.update(
            {
                "asset_id": asset_id,
                "asset_type": "host",
                "host": host,
                "scope_status": record.get("scope_status"),
                "testability": record.get("testability"),
                "reconfw_state": record.get("state"),
                "next_action": record.get("next_action"),
                "blocking_reason": record.get("blocking_reason"),
            }
        )
        self.emit(event)
        return asset_id

    def import_hosts(self) -> None:
        for path in [
            self.source / "assets" / "hosts.jsonl",
            self.source / "assets" / "services.jsonl",
            self.source / "assets" / "cloud.jsonl",
            self.source / "assets" / "mobile.jsonl",
        ]:
            for record in read_records(path):
                kind = str(record.get("type") or path.stem)
                value = str(record.get("normalized_value") or record.get("value") or record.get("host") or "")
                host = str(record.get("host") or value).lower().rstrip(".")
                if kind in {"cloud", "mobile", "service"}:
                    host = host_from_url(value) or str(record.get("host") or value)
                if not host:
                    continue
                event = base_event(
                    event_type="asset_added",
                    source_workspace=self.source,
                    source_file=path,
                    record=record,
                    key=f"{kind}:{record.get('dedupe_key') or value}",
                    engagement=self.engagement,
                )
                event.update(
                    {
                        "asset_id": asset_id_for_host(host),
                        "asset_type": kind,
                        "host": host,
                        "asset": value,
                        "scope_status": record.get("scope_status"),
                        "testability": record.get("testability"),
                        "reconfw_state": record.get("state"),
                        "next_action": record.get("next_action"),
                        "blocking_reason": record.get("blocking_reason"),
                    }
                )
                self.emit(event)

    def import_urls(self) -> None:
        path = self.source / "assets" / "urls.jsonl"
        for record in read_records(path):
            url = str(record.get("normalized_value") or record.get("value") or "")
            if not url:
                continue
            method = str(record.get("method") or "GET").upper()
            host = host_from_url(url)
            if not host:
                continue
            endpoint_path = path_from_url(url)
            asset_id = self.emit_host_asset(host, path, record, "url-host")
            self._emit_endpoint_event(
                source_file=path,
                record=record,
                event_type="endpoint_discovered",
                key=f"url:{method}:{url}",
                asset_id=asset_id,
                host=host,
                method=method,
                path=endpoint_path,
                url=url,
                transport="http",
                parameters=query_params(url),
                source_kind="url_asset",
            )

    def import_endpoints(self) -> None:
        path = self.source / "assets" / "endpoints.jsonl"
        for record in read_records(path):
            host = str(record.get("host") or "").lower().rstrip(".")
            method = str(record.get("method") or "GET").upper()
            endpoint_path = str(record.get("path_template") or path_from_url(str(record.get("normalized_value") or "")) or "/")
            transport = str(record.get("transport") or "http")
            if not host:
                host = host_from_url(str(record.get("api_base_url") or record.get("normalized_value") or ""))
            if not host:
                continue
            asset_id = self.emit_host_asset(host, path, record, "endpoint-host")
            event_type = "graphql_operation_imported" if transport == "graphql" else "endpoint_discovered"
            self._emit_endpoint_event(
                source_file=path,
                record=record,
                event_type=event_type,
                key=f"endpoint:{transport}:{method}:{host}:{endpoint_path}",
                asset_id=asset_id,
                host=host,
                method=method,
                path=endpoint_path,
                url=record.get("api_base_url"),
                transport=transport,
                parameters=[str(p) for p in record.get("parameters", []) if p],
                source_kind="endpoint_asset",
            )

    def _emit_endpoint_event(
        self,
        *,
        source_file: Path,
        record: dict[str, Any],
        event_type: str,
        key: str,
        asset_id: str,
        host: str,
        method: str,
        path: str,
        url: object,
        transport: str,
        parameters: list[str],
        source_kind: str,
    ) -> str:
        ep_id = endpoint_id(method, host, path, transport)
        event = base_event(
            event_type=event_type,
            source_workspace=self.source,
            source_file=source_file,
            record=record,
            key=key,
            engagement=self.engagement,
        )
        event.update(
            {
                "asset_id": asset_id,
                "endpoint_id": ep_id,
                "host": host,
                "method": method,
                "path": path,
                "url": url,
                "transport": transport,
                "parameters": parameters,
                "source_kind": source_kind,
                "scope_status": record.get("scope_status"),
                "testability": record.get("testability"),
                "auth_requirement": record.get("auth_requirement"),
                "state_changing": record.get("state_changing"),
                "reconfw_state": record.get("state"),
                "next_action": record.get("next_action"),
            }
        )
        self.emit(event)
        for param in parameters:
            param_event = base_event(
                event_type="param_discovered",
                source_workspace=self.source,
                source_file=source_file,
                record=record,
                key=f"param:{ep_id}:{param}",
                engagement=self.engagement,
            )
            param_event.update(
                {
                    "asset_id": asset_id,
                    "endpoint_id": ep_id,
                    "param_id": sanitize(f"{ep_id}-{param}", "param-"),
                    "param": param,
                    "param_location": "unknown",
                    "source_kind": source_kind,
                }
            )
            self.emit(param_event)
        return ep_id

    def import_js(self) -> None:
        path = self.source / "assets" / "js.jsonl"
        for record in read_records(path):
            script_url = str(record.get("script_url") or record.get("normalized_value") or record.get("value") or "")
            if not script_url:
                continue
            host = host_from_url(script_url)
            asset_id = self.emit_host_asset(host, path, record, "js-host") if host else ""
            event = base_event(
                event_type="js_endpoint_extracted",
                source_workspace=self.source,
                source_file=path,
                record=record,
                key=f"js:{record.get('sha256') or script_url}",
                engagement=self.engagement,
            )
            event.update(
                {
                    "asset_id": asset_id,
                    "js_id": hash_id("js-", script_url, record.get("sha256")),
                    "script_url": script_url,
                    "page_url": record.get("page_url"),
                    "sha256": record.get("sha256"),
                    "source_map_url": record.get("source_map_url"),
                    "archive_only": record.get("archive_only"),
                    "scope_status": record.get("scope_status"),
                    "testability": record.get("testability"),
                    "third_party_status": record.get("third_party_status"),
                }
            )
            self.emit(event)

    def import_runtime_baselines(self) -> None:
        path = self.source / "output" / "live-probes" / "baselines.jsonl"
        for record in read_records(path):
            url = str(record.get("url") or record.get("final_url") or "")
            host = str(record.get("asset") or host_from_url(url)).lower().rstrip(".")
            if not host:
                continue
            method = str(record.get("method") or "GET").upper()
            endpoint_path = path_from_url(url) if url else "/"
            asset_id = self.emit_host_asset(host, path, record, "runtime-host")
            ep_id = self._emit_endpoint_event(
                source_file=path,
                record=record,
                event_type="endpoint_verified_reachable",
                key=f"runtime:{method}:{url or host}",
                asset_id=asset_id,
                host=host,
                method=method,
                path=endpoint_path,
                url=url,
                transport="http",
                parameters=query_params(url),
                source_kind="live_baseline",
            )
            for evidence_path in raw_paths(record):
                ev = base_event(
                    event_type="evidence_added",
                    source_workspace=self.source,
                    source_file=path,
                    record=record,
                    key=f"evidence:{ep_id}:{evidence_path}",
                    engagement=self.engagement,
                )
                ev.update(
                    {
                        "endpoint_id": ep_id,
                        "evidence_id": hash_id("ev-", evidence_path),
                        "evidence_path": evidence_path,
                        "evidence_type": "reconfw_live_baseline",
                    }
                )
                self.emit(ev)

    def import_mapping_outputs(self) -> None:
        graphql_path = self.source / "output" / "mapping" / "graphql.jsonl"
        for record in read_records(graphql_path):
            endpoint = str(record.get("endpoint") or "")
            host = host_from_url(endpoint)
            if not host:
                continue
            asset_id = self.emit_host_asset(host, graphql_path, record, "graphql-host")
            self._emit_endpoint_event(
                source_file=graphql_path,
                record=record,
                event_type="graphql_operation_imported",
                key=f"graphql:{endpoint}:{','.join(map(str, record.get('operations', [])))}",
                asset_id=asset_id,
                host=host,
                method="POST",
                path=path_from_url(endpoint),
                url=endpoint,
                transport="graphql",
                parameters=["operationName"],
                source_kind="graphql_mapping",
            )

        websocket_path = self.source / "output" / "mapping" / "websockets.jsonl"
        for record in read_records(websocket_path):
            url = str(record.get("url") or "")
            host = host_from_url(url)
            if not host:
                continue
            asset_id = self.emit_host_asset(host, websocket_path, record, "websocket-host")
            self._emit_endpoint_event(
                source_file=websocket_path,
                record=record,
                event_type="endpoint_discovered",
                key=f"websocket:{url}",
                asset_id=asset_id,
                host=host,
                method="GET",
                path=path_from_url(url),
                url=url,
                transport="websocket",
                parameters=[],
                source_kind="websocket_mapping",
            )

        signed_url_path = self.source / "output" / "mapping" / "signed-url-workflows.jsonl"
        for record in read_records(signed_url_path):
            event = base_event(
                event_type="attack_path_expanded",
                source_workspace=self.source,
                source_file=signed_url_path,
                record=record,
                key=f"signed-url:{record.get('name') or record.get('url') or record.get('id')}",
                engagement=self.engagement,
            )
            event.update(
                {
                    "attack_path_id": hash_id("path-", signed_url_path, record.get("name"), record.get("url")),
                    "path_type": "signed_url_workflow",
                    "label": record.get("name") or record.get("url") or "signed URL workflow",
                    "next_action": "manual_validate_signed_url_boundary",
                }
            )
            self.emit(event)

    def import_graph_outputs(self) -> None:
        gaps_path = self.source / "output" / "graph" / "coverage-gaps.jsonl"
        for record in read_records(gaps_path):
            host = str(record.get("host") or "")
            event = base_event(
                event_type="mapping_gap_found",
                source_workspace=self.source,
                source_file=gaps_path,
                record=record,
                key=f"gap:{host}:{record.get('gap')}",
                engagement=self.engagement,
            )
            event.update(
                {
                    "asset_id": asset_id_for_host(host) if host else "",
                    "host": host,
                    "gap_id": hash_id("gap-", host, record.get("gap")),
                    "reason": record.get("gap") or "reconfw coverage gap",
                    "next_action": "map_missing_url_or_endpoint",
                }
            )
            self.emit(event)

        leads_path = self.source / "leads" / "scored-leads.jsonl"
        for record in read_records(leads_path):
            event = base_event(
                event_type="attack_path_expanded",
                source_workspace=self.source,
                source_file=leads_path,
                record=record,
                key=f"lead:{record.get('id') or record.get('subject_id')}",
                engagement=self.engagement,
            )
            event.update(
                {
                    "attack_path_id": str(record.get("id") or hash_id("path-", record.get("subject_id"))),
                    "subject_id": record.get("subject_id"),
                    "priority": record.get("priority"),
                    "score": record.get("score"),
                    "explanation": record.get("explanation"),
                    "boundary_hypothesis": record.get("boundary_hypothesis"),
                    "policy_status": record.get("policy_status"),
                    "next_action": record.get("next_action"),
                }
            )
            self.emit(event)

    def import_queues_and_diff(self) -> None:
        for path in sorted((self.source / "queues").glob("*.jsonl")):
            for record in read_records(path):
                subject = str(record.get("subject") or record.get("target") or record.get("url") or "")
                event = base_event(
                    event_type="loop_started",
                    source_workspace=self.source,
                    source_file=path,
                    record=record,
                    key=f"queue:{path.name}:{record.get('id') or subject}",
                    engagement=self.engagement,
                )
                event.update(
                    {
                        "loop_id": hash_id("loop-", path.name, record.get("id") or subject),
                        "loop_state": "queued" if record.get("state") != "done" else "closed_tested_secure",
                        "subject": subject,
                        "queue": path.stem,
                        "action": record.get("action"),
                        "decision": record.get("decision"),
                        "next_action": record.get("next_action") or "review_queue_item",
                    }
                )
                self.emit(event)

        for path in sorted((self.source / "output" / "diff").glob("*.jsonl")):
            for record in read_records(path):
                event = base_event(
                    event_type="source_runtime_diff_added",
                    source_workspace=self.source,
                    source_file=path,
                    record=record,
                    key=f"diff:{path.name}:{record.get('key') or record.get('id') or record}",
                    engagement=self.engagement,
                )
                event.update(
                    {
                        "diff_id": hash_id("diff-", path.name, record.get("key") or json.dumps(record, sort_keys=True)),
                        "diff_type": path.stem,
                        "key": record.get("key"),
                        "reason": record.get("reason"),
                        "next_action": "review_reconfw_diff",
                    }
                )
                self.emit(event)

    def import_coverage(self) -> None:
        for path in [
            self.source / "coverage" / "audit-findings.jsonl",
            self.source / "coverage" / "accepted-operational-gaps.jsonl",
            self.source / "output" / "collector-health.jsonl",
        ]:
            for record in read_records(path):
                status = str(record.get("status") or record.get("severity") or "review")
                event_type = "gap_found" if status in {"blocker", "blocked", "warning"} else "coverage_reviewed"
                event = base_event(
                    event_type=event_type,
                    source_workspace=self.source,
                    source_file=path,
                    record=record,
                    key=f"coverage:{path.name}:{record.get('gate') or record.get('id') or record}",
                    engagement=self.engagement,
                )
                event.update(
                    {
                        "gap_id": hash_id("gap-", path.name, record.get("gate") or record.get("id") or json.dumps(record, sort_keys=True)),
                        "gate": record.get("gate"),
                        "reason": record.get("reason") or record.get("message") or record.get("status"),
                        "next_action": record.get("next_action") or "review_reconfw_coverage",
                    }
                )
                if event_type == "gap_found":
                    event["status"] = "blocked"
                self.emit(event)

    def run(self) -> dict[str, int]:
        if not self.source.exists():
            raise SystemExit(f"missing recon-framework workspace: {self.source}")
        if not self.root.exists():
            raise SystemExit(f"missing engagement root: {self.root}")

        self.import_hosts()
        self.import_urls()
        self.import_endpoints()
        self.import_js()
        self.import_runtime_baselines()
        self.import_mapping_outputs()
        self.import_graph_outputs()
        self.import_queues_and_diff()
        self.import_coverage()

        if self.events:
            summary = base_event(
                event_type="operator_note_added",
                source_workspace=self.source,
                source_file=self.source,
                record={},
                key=f"summary:{sha256('|'.join(event['id'] for event in self.events).encode()).hexdigest()[:16]}",
                engagement=self.engagement,
            )
            summary.update(
                {
                    "notes": "Imported recon-framework workspace into final workflow event ledger.",
                    "import_counts": dict(sorted(self.counts.items())),
                }
            )
            self.emit(summary)

        if not self.dry_run:
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            with self.events_path.open("a", encoding="utf-8") as out:
                for event in self.events:
                    out.write(json.dumps(event, separators=(",", ":")) + "\n")
        self.counts["events_written"] = len(self.events) if not self.dry_run else 0
        self.counts["events_planned"] = len(self.events)
        return dict(sorted(self.counts.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Import hunterweb/recon-framework outputs into this engagement.")
    parser.add_argument("workspace", type=Path, help="Recon-framework workspace root")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Final workflow engagement root")
    parser.add_argument("--dry-run", action="store_true", help="Parse and summarize without writing events")
    parser.add_argument("--no-build", action="store_true", help="Do not rebuild data/graph_state.json after import")
    args = parser.parse_args()

    importer = Importer(args.workspace, args.root, dry_run=args.dry_run)
    counts = importer.run()
    for key, value in counts.items():
        print(f"{key}: {value}")

    if not args.dry_run and not args.no_build:
        root = args.root.resolve()
        state = build(read_jsonl(root / "data/events.jsonl"), root)
        out_path = root / "data/graph_state.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        print(f"graph_built: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
