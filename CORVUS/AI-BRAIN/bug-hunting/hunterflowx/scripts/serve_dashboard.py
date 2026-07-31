#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from attack_graph import build_attack_graph, cypher_bundle, cypher_text, neo4j_config
import caido_bridge
import ai_governance
import report_lifecycle
import run_queue
import safety_policy


ROOT = Path(__file__).resolve().parents[1]
ENGAGEMENTS_ROOT = ROOT / "engagements"
ALLOWED_ARTIFACT_DIRS = {"findings", "reports", "evidence", "domain-depth", "source-reviews", "output"}
ARTIFACT_KIND_DIRS = {
    "findings": ("findings",),
    "reports": ("reports",),
    "evidence": ("evidence",),
    "domain": ("domain-depth",),
    "source": ("source-reviews",),
    "output": ("output",),
    "all": tuple(sorted(ALLOWED_ARTIFACT_DIRS)),
}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".http", ".log", ".csv", ".yaml", ".yml", ".py"}
MAX_PREVIEW_BYTES = 250_000


class Handler(BaseHTTPRequestHandler):
    engagement_root = Path.cwd()

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, data: object) -> None:
        self._send(status, json.dumps(data, indent=2).encode("utf-8"), "application/json")

    def _read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        data = self.rfile.read(length)
        try:
            payload = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _rebuild_graph(self, root: Path) -> None:
        subprocess.run([sys.executable, str(ROOT / "scripts/build_graph.py"), "--root", str(root)], check=False)

    def _default_engagement_id(self) -> str:
        root = self.engagement_root.resolve()
        try:
            rel = root.relative_to(ENGAGEMENTS_ROOT.resolve())
        except ValueError:
            return ""
        parts = rel.parts
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        return ""

    def _engagement_graph_path(self, engagement_id: str) -> Path | None:
        parts = [part for part in engagement_id.split("/") if part]
        if len(parts) != 2 or any(part in {".", ".."} for part in parts):
            return None
        return ENGAGEMENTS_ROOT / parts[0] / parts[1] / "data" / "graph_state.json"

    def _engagement_root_path(self, engagement_id: str) -> Path | None:
        parts = [part for part in engagement_id.split("/") if part]
        if len(parts) != 2 or any(part in {".", ".."} for part in parts):
            return None
        return ENGAGEMENTS_ROOT / parts[0] / parts[1]

    def _engagement_root_from_query(self, query: dict[str, list[str]]) -> tuple[str, Path | None]:
        engagement_id = (query.get("engagement") or [""])[0]
        root = self._engagement_root_path(engagement_id) if engagement_id else self.engagement_root
        return engagement_id or self._default_engagement_id(), root

    def _safe_artifact_path(self, root: Path, rel_path: str) -> Path | None:
        if not rel_path:
            return None
        rel = Path(rel_path)
        if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
            return None
        if not rel.parts or rel.parts[0] not in ALLOWED_ARTIFACT_DIRS:
            return None
        try:
            candidate = (root / rel).resolve()
            candidate.relative_to(root.resolve())
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        return candidate

    def _read_text_preview(self, path: Path) -> tuple[str, bool]:
        data = path.read_bytes()[:MAX_PREVIEW_BYTES]
        truncated = path.stat().st_size > MAX_PREVIEW_BYTES
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                return "", truncated
            return text, truncated
        return data.decode("utf-8", errors="replace"), truncated

    def _artifact_title(self, text: str, path: Path) -> str:
        for line in text.splitlines()[:30]:
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                if title:
                    return title
        return path.name

    def _artifact_records(self, root: Path, kind: str = "all") -> list[dict[str, object]]:
        dirs = ARTIFACT_KIND_DIRS.get(kind, ARTIFACT_KIND_DIRS["all"])
        records: list[dict[str, object]] = []
        for dirname in dirs:
            base = root / dirname
            if not base.exists():
                continue
            for path in sorted(base.rglob("*")):
                if not path.is_file() or path.name == ".gitkeep":
                    continue
                rel = path.relative_to(root)
                text, truncated = self._read_text_preview(path)
                status = "file"
                parts = rel.parts
                if len(parts) > 1:
                    if parts[0] == "findings":
                        status = parts[1]
                    elif parts[0] == "reports":
                        status = parts[1]
                    elif parts[0] == "evidence":
                        status = parts[1]
                    else:
                        status = parts[0]
                records.append(
                    {
                        "kind": parts[0],
                        "status": status,
                        "path": str(rel),
                        "name": path.name,
                        "title": self._artifact_title(text, path),
                        "size": path.stat().st_size,
                        "modified": path.stat().st_mtime,
                        "preview": text[:400],
                        "truncated": truncated,
                    }
                )
        return records

    def _events(self, root: Path) -> list[dict[str, object]]:
        events_path = root / "data" / "events.jsonl"
        if not events_path.exists():
            return []
        events: list[dict[str, object]] = []
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    def _search_results(self, root: Path, query_text: str, limit: int) -> list[dict[str, object]]:
        needle = query_text.lower().strip()
        if not needle:
            return []
        results: list[dict[str, object]] = []

        def add(category: str, title: str, haystack: object, **extra: object) -> None:
            text = json.dumps(haystack, ensure_ascii=False, default=str) if not isinstance(haystack, str) else haystack
            lower = text.lower()
            if needle not in lower and needle not in title.lower():
                return
            idx = max(lower.find(needle), 0)
            snippet = text[max(0, idx - 80) : idx + 180].replace("\n", " ")
            results.append({"category": category, "title": title, "snippet": snippet, **extra})

        for event in self._events(root):
            title = str(event.get("type") or "event").replace("_", " ")
            add(
                "event",
                title,
                event,
                id=event.get("id"),
                status=event.get("status"),
                ts=event.get("ts"),
                event_type=event.get("type"),
            )

        graph_path = root / "data" / "graph_state.json"
        if graph_path.exists():
            try:
                graph = json.loads(graph_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                graph = {}
            for node in graph.get("nodes", []):
                add(
                    str(node.get("type") or "node"),
                    str(node.get("label") or node.get("id") or "node"),
                    node,
                    id=node.get("id"),
                    status=node.get("status"),
                    node_type=node.get("type"),
                )

        for artifact in self._artifact_records(root):
            text, _ = self._read_text_preview(root / str(artifact.get("path")))
            add(
                str(artifact.get("kind") or "artifact"),
                str(artifact.get("title") or artifact.get("name") or artifact.get("path")),
                text or artifact,
                path=artifact.get("path"),
                status=artifact.get("status"),
                kind=artifact.get("kind"),
            )
        try:
            attack_graph = build_attack_graph(root)
        except Exception:
            attack_graph = {}
        for node in attack_graph.get("nodes", []):
            add(
                "attack_graph",
                str(node.get("label") or node.get("id") or "attack graph node"),
                node,
                id=node.get("id"),
                status=node.get("status"),
                node_type=node.get("stage"),
            )
        for path_record in attack_graph.get("paths", []):
            add(
                "attack_path",
                str(path_record.get("endpoint_id") or path_record.get("id") or "attack path"),
                path_record,
                id=path_record.get("id"),
                status=path_record.get("status"),
            )
        return results[:limit]

    def _list_engagements(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        if not ENGAGEMENTS_ROOT.exists():
            return items
        for graph_path in sorted(ENGAGEMENTS_ROOT.glob("*/*/data/graph_state.json")):
            target_root = graph_path.parents[1]
            program = target_root.parent.name
            target = target_root.name
            engagement_id = f"{program}/{target}"
            try:
                state = json.loads(graph_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                state = {}
            metrics = state.get("metrics", {}) if isinstance(state, dict) else {}
            items.append(
                {
                    "id": engagement_id,
                    "program": program,
                    "target": target,
                    "path": str(target_root),
                    "generated_at": state.get("generated_at") if isinstance(state, dict) else None,
                    "metrics": {
                        "total_endpoints": metrics.get("total_endpoints", 0),
                        "tested_endpoints": metrics.get("tested_endpoints", 0),
                        "confirmed_findings": metrics.get("confirmed_findings", 0),
                        "finding_candidates": metrics.get("finding_candidates", 0),
                        "source_completeness_avg": metrics.get("source_completeness_avg", 0),
                        "source_files_incomplete": metrics.get("source_files_incomplete", 0),
                        "judge_reportable": metrics.get("judge_reportable", 0),
                        "judge_candidate": metrics.get("judge_candidate", 0),
                        "judge_needs_evidence": metrics.get("judge_needs_evidence", 0),
                        "risk_top_score": metrics.get("risk_top_score", 0),
                        "risk_priority_p0": metrics.get("risk_priority_p0", 0),
                        "risk_priority_p1": metrics.get("risk_priority_p1", 0),
                        "domain_depth_avg": metrics.get("domain_depth_avg", 0),
                        "domain_checks_missing": metrics.get("domain_checks_missing", 0),
                        "domain_wp_score": metrics.get("domain_wp_score", 0),
                        "domain_onprem_score": metrics.get("domain_onprem_score", 0),
                        "domain_mobile_score": metrics.get("domain_mobile_score", 0),
                        "open_gaps": metrics.get("open_gaps", 0),
                        "active_loops": metrics.get("active_loops", 0),
                    },
                }
            )
        return items

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in {"/", "/index.html"}:
            html = (ROOT / "dashboard/index.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return

        if path in {"/neo4j", "/neo4j.html"}:
            html = (ROOT / "dashboard/neo4j.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return

        if path in {"/command", "/command.html", "/command-center"}:
            html = (ROOT / "dashboard/command.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return

        if path == "/styles.css":
            self._send(200, (ROOT / "dashboard/styles.css").read_bytes(), "text/css; charset=utf-8")
            return

        if path == "/app.js":
            self._send(200, (ROOT / "dashboard/app.js").read_bytes(), "application/javascript; charset=utf-8")
            return

        if path == "/neo4j.js":
            self._send(200, (ROOT / "dashboard/neo4j.js").read_bytes(), "application/javascript; charset=utf-8")
            return

        if path == "/command.js":
            self._send(200, (ROOT / "dashboard/command.js").read_bytes(), "application/javascript; charset=utf-8")
            return

        if path == "/api/engagements":
            self._send_json(
                200,
                {
                    "default_engagement": self._default_engagement_id(),
                    "engagements": self._list_engagements(),
                },
            )
            return

        if path in {"/graph_state.json", "/api/graph"}:
            engagement_id = (query.get("engagement") or [""])[0]
            graph = self._engagement_graph_path(engagement_id) if engagement_id else None
            if graph is None:
                graph = self.engagement_root / "data/graph_state.json"
            if not graph.exists():
                self._send_json(404, {"error": "missing graph_state.json"})
                return
            self._send(200, graph.read_bytes(), "application/json")
            return

        if path == "/api/attack-graph":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            self._send_json(200, build_attack_graph(root))
            return

        if path == "/api/neo4j/status":
            self._send_json(200, neo4j_config())
            return

        if path == "/api/neo4j/cypher":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            attack_graph = build_attack_graph(root)
            format_type = (query.get("format") or ["text"])[0]
            if format_type == "json":
                self._send_json(200, cypher_bundle(attack_graph))
            else:
                self._send(200, cypher_text(attack_graph).encode("utf-8"), "text/plain; charset=utf-8")
            return

        if path == "/api/run-queue":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            self._send_json(200, run_queue.load_queue(root))
            return

        if path == "/api/caido/status":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            self._send_json(200, caido_bridge.status(root))
            return

        if path == "/api/safety/status":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            policy, policy_file = safety_policy.load_policy(root)
            self._send_json(200, {"path": str(policy_file), "policy": policy})
            return

        if path == "/api/governance/status":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            self._send_json(200, ai_governance.status(root))
            return

        if path == "/api/reports":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            self._send_json(200, report_lifecycle.summarize(root))
            return

        if path == "/api/events":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            events = self._events(root)
            if not events:
                self._send_json(404, {"error": "missing events.jsonl"})
                return
            limit_raw = (query.get("limit") or ["80"])[0]
            try:
                limit = max(1, min(300, int(limit_raw)))
            except ValueError:
                limit = 80
            self._send_json(
                200,
                {
                    "engagement": engagement_id,
                    "events_total": len(events),
                    "events": events[-limit:],
                },
            )
            return

        if path == "/api/artifacts":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            kind = (query.get("kind") or ["all"])[0]
            self._send_json(
                200,
                {
                    "engagement": engagement_id,
                    "kind": kind,
                    "artifacts": self._artifact_records(root, kind),
                },
            )
            return

        if path == "/api/artifact":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            rel_path = (query.get("path") or [""])[0]
            artifact = self._safe_artifact_path(root, rel_path)
            if artifact is None:
                self._send_json(403, {"error": "invalid artifact path"})
                return
            text, truncated = self._read_text_preview(artifact)
            rel = artifact.relative_to(root)
            self._send_json(
                200,
                {
                    "engagement": engagement_id,
                    "path": str(rel),
                    "name": artifact.name,
                    "size": artifact.stat().st_size,
                    "modified": artifact.stat().st_mtime,
                    "text": text,
                    "truncated": truncated,
                    "is_text": bool(text),
                },
            )
            return

        if path == "/api/search":
            engagement_id, root = self._engagement_root_from_query(query)
            if root is None:
                self._send_json(400, {"error": "invalid engagement"})
                return
            q = (query.get("q") or [""])[0]
            limit_raw = (query.get("limit") or ["25"])[0]
            try:
                limit = max(1, min(100, int(limit_raw)))
            except ValueError:
                limit = 25
            self._send_json(
                200,
                {
                    "engagement": engagement_id,
                    "query": q,
                    "results": self._search_results(root, q, limit),
                },
            )
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        engagement_id, root = self._engagement_root_from_query(query)
        if root is None:
            self._send_json(400, {"error": "invalid engagement"})
            return

        try:
            if path == "/api/run-queue":
                action = str(payload.get("action") or "")
                if action == "seed":
                    result = run_queue.seed_queue(root)
                elif action == "approve":
                    result = run_queue.approve_task(root, str(payload.get("task_id") or ""))
                elif action == "run":
                    result = run_queue.run_task(root, str(payload.get("task_id") or ""))
                    self._rebuild_graph(root)
                elif action == "run-next":
                    result = run_queue.run_next(root) or {"status": "empty", "message": "no runnable task"}
                    self._rebuild_graph(root)
                elif action == "block":
                    result = run_queue.block_task(root, str(payload.get("task_id") or ""), str(payload.get("reason") or "blocked from dashboard"))
                elif action == "add":
                    command = payload.get("command") or []
                    if not isinstance(command, list):
                        self._send_json(400, {"error": "command must be a list"})
                        return
                    result = run_queue.add_task(
                        root,
                        stage=str(payload.get("stage") or "manual"),
                        label=str(payload.get("label") or "Manual task"),
                        command=[str(item) for item in command],
                        active=bool(payload.get("active")),
                        blocked_reason=str(payload.get("blocked_reason") or ""),
                        source="dashboard",
                        meta=payload.get("meta") if isinstance(payload.get("meta"), dict) else {},
                        autonomy_level=str(payload.get("autonomy_level") or ""),
                        agent_role=str(payload.get("agent_role") or ""),
                        validation_gate=str(payload.get("validation_gate") or ""),
                    )
                else:
                    self._send_json(400, {"error": f"unknown run queue action: {action}"})
                    return
                self._send_json(200, result)
                return

            if path == "/api/reports":
                action = str(payload.get("action") or "")
                if action == "draft":
                    result = report_lifecycle.create_draft(root, str(payload.get("test_id") or ""), str(payload.get("title") or ""), str(payload.get("finding_id") or ""))
                elif action == "status":
                    result = report_lifecycle.update_status(
                        root,
                        str(payload.get("report_id") or ""),
                        str(payload.get("status") or ""),
                        str(payload.get("note") or ""),
                        str(payload.get("bounty_value") or ""),
                        str(payload.get("retest_date") or ""),
                    )
                else:
                    self._send_json(400, {"error": f"unknown report action: {action}"})
                    return
                self._rebuild_graph(root)
                self._send_json(200, result)
                return

            if path == "/api/caido/import":
                source = str(payload.get("source") or "caido")
                file_path = Path(str(payload.get("file_path") or ""))
                if source not in {"caido", "burp"} or not file_path.exists():
                    self._send_json(400, {"error": "source must be caido/burp and file_path must exist"})
                    return
                result = caido_bridge.import_history(
                    root,
                    source,
                    file_path,
                    str(payload.get("endpoint_id") or ""),
                    str(payload.get("test_id") or ""),
                    int(payload.get("limit") or 50),
                )
                self._rebuild_graph(root)
                self._send_json(200, result)
                return

            if path == "/api/neo4j/action":
                action = str(payload.get("action") or "")
                node_id = str(payload.get("node_id") or "")
                path_id = str(payload.get("path_id") or "")
                if action == "mark_gap":
                    events = self._events(root)
                    event = {
                        "id": f"evt-{len(events) + 1:06d}",
                        "ts": datetime.now(timezone.utc).astimezone().isoformat(),
                        "engagement_id": engagement_id.replace("/", "-"),
                        "actor": "dashboard",
                        "type": "mapping_gap_found",
                        "status": "blocked",
                        "node_id": node_id,
                        "path_id": path_id,
                        "reason": str(payload.get("reason") or "Marked from Neo4j graph"),
                    }
                    with (root / "data/events.jsonl").open("a", encoding="utf-8") as f:
                        f.write(json.dumps(event, separators=(",", ":")) + "\n")
                    result = event
                elif action == "queue_angle_plan":
                    result = run_queue.add_task(
                        root,
                        stage="angle-plan",
                        label=f"Generate angle plan from graph {node_id or path_id}",
                        command=["bbf", "angle-plan", "full"],
                        blocked_reason="fill endpoint-id/method/path from selected graph node before running",
                        source="neo4j",
                        meta={"node_id": node_id, "path_id": path_id},
                    )
                elif action == "queue_evidence_score":
                    result = run_queue.add_task(
                        root,
                        stage="evidence-score",
                        label=f"Score evidence from graph {node_id or path_id}",
                        command=["bbf", "evidence-score", "--all"],
                        source="neo4j",
                        meta={"node_id": node_id, "path_id": path_id},
                    )
                elif action == "queue_report":
                    result = run_queue.add_task(
                        root,
                        stage="report",
                        label=f"Review report lifecycle from graph {node_id or path_id}",
                        command=["bbf", "report-lifecycle", "list"],
                        source="neo4j",
                        meta={"node_id": node_id, "path_id": path_id},
                    )
                else:
                    self._send_json(400, {"error": f"unknown Neo4j action: {action}"})
                    return
                self._rebuild_graph(root)
                self._send_json(200, result)
                return
        except SystemExit as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})
            return

        self._send(404, b"not found", "text/plain")

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve local dashboard.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    args = parser.parse_args()

    Handler.engagement_root = args.root.resolve()
    server = HTTPServer((args.host, args.port), Handler)
    print(f"dashboard: http://{args.host}:{args.port}")
    print(f"engagement: {Handler.engagement_root}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
