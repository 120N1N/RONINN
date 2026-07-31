#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CHAIN_STAGES: list[dict[str, str]] = [
    {"key": "js_file", "label": "JS File"},
    {"key": "api_route", "label": "API Route"},
    {"key": "param", "label": "Param"},
    {"key": "auth_role", "label": "Auth Role"},
    {"key": "test_angle", "label": "Test Angle"},
    {"key": "chaining", "label": "Chaining"},
    {"key": "evidence", "label": "Evidence"},
    {"key": "finding", "label": "Finding"},
]

STAGE_LABELS = {stage["key"]: stage["label"] for stage in CHAIN_STAGES}
STAGE_NEO4J_LABELS = {
    "js_file": "JsFile",
    "api_route": "ApiRoute",
    "param": "Param",
    "auth_role": "AuthRole",
    "test_angle": "TestAngle",
    "chaining": "Chaining",
    "evidence": "Evidence",
    "finding": "Finding",
}

EDGE_TYPES = {
    ("js_file", "api_route"): ("DISCOVERS_ROUTE", "discovers route"),
    ("api_route", "param"): ("HAS_PARAM", "has param"),
    ("param", "auth_role"): ("REQUIRES_ROLE", "requires role"),
    ("auth_role", "test_angle"): ("TESTED_BY", "tested by"),
    ("test_angle", "chaining"): ("CHAINS_TO", "chains to"),
    ("chaining", "evidence"): ("SUPPORTED_BY", "supported by"),
    ("evidence", "finding"): ("RESULTS_IN", "results in"),
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def load_graph_state(root: Path) -> dict[str, Any]:
    path = root / "data" / "graph_state.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part or "") for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def clean_label(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text if text else fallback


def latest_by(events: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for event in events:
        value = str(event.get(key) or "")
        if value:
            result[value] = event
    return result


def compact_props(data: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            props[key] = value
        elif isinstance(value, list):
            if all(isinstance(item, (str, int, float, bool)) for item in value):
                props[key] = value
            else:
                props[key] = json.dumps(value, ensure_ascii=False, default=str)
        elif isinstance(value, dict):
            props[key] = json.dumps(value, ensure_ascii=False, default=str)
        else:
            props[key] = str(value)
    return props


@dataclass
class ChainPath:
    endpoint_id: str
    angle_id: str
    test_id: str
    source_id: str = ""
    endpoint_label: str = ""
    source_label: str = ""
    param_id: str = ""
    auth_role_id: str = ""
    chain_id: str = ""
    finding_id: str = ""
    status: str = "mapped_only"


class AttackGraphBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.state = load_graph_state(root)
        self.events = read_jsonl(root / "data" / "events.jsonl")
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}

    def add_node(self, node_id: str, stage: str, label: str, status: str = "mapped_only", **props: Any) -> str:
        if not node_id:
            return ""
        existing = self.nodes.get(node_id, {})
        merged_props = dict(existing.get("properties") or {})
        merged_props.update(compact_props(props))
        merged_status = status or existing.get("status") or "mapped_only"
        self.nodes[node_id] = {
            "id": node_id,
            "stage": stage,
            "stage_label": STAGE_LABELS.get(stage, stage),
            "label": label,
            "status": merged_status,
            "properties": merged_props,
        }
        return node_id

    def add_edge(self, source: str, target: str, source_stage: str, target_stage: str, label: str = "") -> None:
        if not source or not target:
            return
        edge_type, default_label = EDGE_TYPES.get((source_stage, target_stage), ("RELATED_TO", "related to"))
        edge_id = f"edge-{edge_type}-{source}-{target}"
        self.edges[edge_id] = {
            "id": edge_id,
            "source": source,
            "target": target,
            "type": edge_type,
            "label": label or default_label,
        }

    def event_source_nodes(self) -> dict[str, dict[str, str]]:
        sources: dict[str, dict[str, str]] = {}
        for event in self.events:
            source_id = str(event.get("source_id") or event.get("js_id") or "")
            source_file = str(event.get("source_file") or event.get("script_url") or "")
            if not source_id and source_file:
                source_id = stable_id("src", source_file)
            if not source_id:
                continue
            sources[source_id] = {
                "id": source_id,
                "label": clean_label(source_file or event.get("page_url"), source_id),
                "status": str(event.get("status") or "mapped_static"),
                "kind": "js" if event.get("type") == "js_endpoint_extracted" or source_file.endswith(".js") else "source",
            }
        for node in self.state.get("nodes", []):
            if node.get("type") not in {"js", "source"}:
                continue
            sources[str(node.get("id"))] = {
                "id": str(node.get("id")),
                "label": clean_label(node.get("label"), str(node.get("id"))),
                "status": str(node.get("status") or "mapped_static"),
                "kind": str(node.get("type") or "source"),
            }
        return sources

    def endpoint_nodes(self) -> dict[str, dict[str, str]]:
        endpoints: dict[str, dict[str, str]] = {}
        for event in self.events:
            endpoint_id = str(event.get("endpoint_id") or "")
            if not endpoint_id:
                continue
            method = str(event.get("method") or "")
            route = str(event.get("path") or event.get("target") or endpoint_id)
            label = f"{method} {route}".strip()
            endpoints[endpoint_id] = {
                "id": endpoint_id,
                "label": clean_label(label, endpoint_id),
                "status": str(event.get("status") or "mapped_only"),
            }
        for node in self.state.get("nodes", []):
            if node.get("type") != "endpoint":
                continue
            endpoints[str(node.get("id"))] = {
                "id": str(node.get("id")),
                "label": clean_label(node.get("label"), str(node.get("id"))),
                "status": str(node.get("status") or "mapped_only"),
            }
        return endpoints

    def build_chain_paths(self) -> list[ChainPath]:
        endpoints = self.endpoint_nodes()
        source_by_endpoint: dict[str, tuple[str, str]] = {}
        angle_id_by_test: dict[str, str] = {}
        angle_id_by_endpoint_angle: dict[tuple[str, str], str] = {}
        for event in self.events:
            endpoint_id = str(event.get("endpoint_id") or "")
            source_id = str(event.get("source_id") or event.get("js_id") or "")
            source_file = str(event.get("source_file") or event.get("script_url") or "")
            if endpoint_id and source_id:
                source_by_endpoint[endpoint_id] = (source_id, clean_label(source_file, source_id))
            angle_id = str(event.get("angle_id") or "")
            angle = str(event.get("angle") or event.get("bug_class") or "")
            test_id = str(event.get("test_id") or "")
            if angle_id and test_id:
                angle_id_by_test[test_id] = angle_id
            if endpoint_id and angle and angle_id:
                angle_id_by_endpoint_angle[(endpoint_id, angle)] = angle_id

        paths: dict[tuple[str, str], ChainPath] = {}
        for event in self.events:
            endpoint_id = str(event.get("endpoint_id") or "")
            if not endpoint_id:
                continue
            angle = str(event.get("angle") or event.get("bug_class") or "")
            angle_id = str(event.get("angle_id") or "")
            test_id = str(event.get("test_id") or "")
            if not angle_id and test_id:
                angle_id = angle_id_by_test.get(test_id, "")
            if not angle_id and angle:
                angle_id = angle_id_by_endpoint_angle.get((endpoint_id, angle), "")
            if not angle_id and angle:
                angle_id = f"angle-{endpoint_id}-{angle}".replace("/", "-")
            if not angle_id and not test_id:
                continue
            key = (endpoint_id, angle_id or test_id)
            source_id, source_label = source_by_endpoint.get(endpoint_id, ("", ""))
            endpoint_label = endpoints.get(endpoint_id, {}).get("label", endpoint_id)
            item = paths.get(key) or ChainPath(
                endpoint_id=endpoint_id,
                angle_id=angle_id,
                test_id=test_id,
                source_id=source_id,
                source_label=source_label,
                endpoint_label=endpoint_label,
            )
            if test_id:
                item.test_id = test_id
            if angle_id:
                item.angle_id = angle_id
            item.status = str(event.get("status") or item.status or "mapped_only")
            paths[key] = item

        for event in self.events:
            if event.get("type") not in {"chain_candidate_added", "attack_path_expanded"}:
                continue
            endpoint_id = str(event.get("endpoint_id") or "")
            angle_id = str(event.get("angle_id") or "")
            test_id = str(event.get("test_id") or "")
            path_id = str(event.get("attack_path_id") or f"path-{event.get('id')}")
            for item in paths.values():
                if endpoint_id and item.endpoint_id != endpoint_id:
                    continue
                if angle_id and item.angle_id != angle_id:
                    continue
                if test_id and item.test_id != test_id:
                    continue
                item.chain_id = path_id
                item.status = str(event.get("status") or "test_attempted")

        for event in self.events:
            if event.get("type") != "verdict_set":
                continue
            if event.get("status") not in {"confirmed", "finding_candidate"}:
                continue
            test_id = str(event.get("test_id") or "")
            finding_id = str(event.get("finding_id") or f"finding-{test_id}")
            for item in paths.values():
                if item.test_id == test_id:
                    item.finding_id = finding_id
                    item.status = str(event.get("status") or item.status)

        if not paths:
            for endpoint_id, endpoint in endpoints.items():
                source_id, source_label = source_by_endpoint.get(endpoint_id, ("", ""))
                paths[(endpoint_id, "")] = ChainPath(
                    endpoint_id=endpoint_id,
                    angle_id="",
                    test_id="",
                    source_id=source_id,
                    source_label=source_label,
                    endpoint_label=endpoint["label"],
                    status=endpoint["status"],
                )
        return list(paths.values())

    def build(self) -> dict[str, Any]:
        sources = self.event_source_nodes()
        endpoints = self.endpoint_nodes()
        endpoint_params: dict[str, list[dict[str, str]]] = {}
        endpoint_roles: dict[str, list[dict[str, str]]] = {}
        test_evidence: dict[str, list[dict[str, str]]] = {}

        for event in self.events:
            endpoint_id = str(event.get("endpoint_id") or "")
            if event.get("type") == "param_discovered" and endpoint_id:
                name = str(event.get("param") or event.get("name") or "param")
                endpoint_params.setdefault(endpoint_id, []).append(
                    {
                        "id": str(event.get("param_id") or stable_id("param", endpoint_id, name)),
                        "label": name,
                        "status": str(event.get("status") or "mapped_only"),
                    }
                )
            role = str(event.get("auth_role") or event.get("role") or event.get("account_role") or "")
            if endpoint_id and role:
                endpoint_roles.setdefault(endpoint_id, []).append(
                    {
                        "id": stable_id("role", endpoint_id, role),
                        "label": role,
                        "status": str(event.get("status") or "mapped_only"),
                    }
                )
            if event.get("type") == "evidence_added":
                test_id = str(event.get("test_id") or "")
                if test_id:
                    test_evidence.setdefault(test_id, []).append(
                        {
                            "id": str(event.get("evidence_id") or stable_id("ev", event.get("evidence_path"), event.get("case"))),
                            "label": clean_label(event.get("case") or event.get("evidence_path"), "evidence"),
                            "status": str(event.get("status") or "saved"),
                            "path": str(event.get("evidence_path") or ""),
                        }
                    )

        paths = self.build_chain_paths()
        path_records: list[dict[str, Any]] = []
        for item in paths:
            source_id = item.source_id or stable_id("src-unknown", item.endpoint_id)
            source = sources.get(source_id, {"label": item.source_label or "source/js not linked", "status": "source_incomplete"})
            endpoint = endpoints.get(item.endpoint_id, {"label": item.endpoint_label or item.endpoint_id, "status": "mapped_only"})
            params = endpoint_params.get(item.endpoint_id) or [
                {
                    "id": stable_id("param", item.endpoint_id, "request-object"),
                    "label": "request object / route params",
                    "status": "inferred",
                }
            ]
            roles = endpoint_roles.get(item.endpoint_id) or [
                {
                    "id": stable_id("role", item.endpoint_id, "owned-account-role-tbd"),
                    "label": "owned account / role TBD",
                    "status": "needs_context",
                }
            ]
            angle_id = item.angle_id or stable_id("angle", item.endpoint_id, "multi-angle-needed")
            angle_label = "multi-angle test pending"
            for event in self.events:
                if str(event.get("angle_id") or "") == angle_id:
                    angle_label = clean_label(event.get("angle"), angle_id)
            chain_id = item.chain_id or stable_id("chain", item.endpoint_id, angle_id, "chain-assessment")
            chain_label = "chain assessment pending"
            if item.chain_id:
                chain_label = item.chain_id
            evidences = test_evidence.get(item.test_id) or []
            if not evidences:
                evidences = [
                    {
                        "id": stable_id("evidence", item.endpoint_id, angle_id, "missing"),
                        "label": "evidence missing",
                        "status": "evidence_incomplete",
                        "path": "",
                    }
                ]
            finding_id = item.finding_id or stable_id("finding", item.endpoint_id, angle_id, "not-yet")
            finding_label = item.finding_id or "finding not established"
            finding_status = item.status if item.finding_id else "not_reportable_yet"

            self.add_node(source_id, "js_file", source["label"], source.get("status", "mapped_static"), endpoint_id=item.endpoint_id)
            self.add_node(item.endpoint_id, "api_route", endpoint["label"], endpoint.get("status", "mapped_only"))
            self.add_edge(source_id, item.endpoint_id, "js_file", "api_route")

            path_nodes: dict[str, str] = {
                "js_file": source_id,
                "api_route": item.endpoint_id,
                "test_angle": angle_id,
                "chaining": chain_id,
                "finding": finding_id,
            }
            for param in params:
                self.add_node(param["id"], "param", param["label"], param.get("status", "mapped_only"), endpoint_id=item.endpoint_id)
                self.add_edge(item.endpoint_id, param["id"], "api_route", "param")
            first_param = params[0]["id"]
            path_nodes["param"] = first_param

            for role in roles:
                self.add_node(role["id"], "auth_role", role["label"], role.get("status", "needs_context"), endpoint_id=item.endpoint_id)
                self.add_edge(first_param, role["id"], "param", "auth_role")
            first_role = roles[0]["id"]
            path_nodes["auth_role"] = first_role

            self.add_node(angle_id, "test_angle", angle_label, item.status or "queued", endpoint_id=item.endpoint_id, test_id=item.test_id)
            self.add_edge(first_role, angle_id, "auth_role", "test_angle")

            self.add_node(chain_id, "chaining", chain_label, "test_attempted" if item.chain_id else "needs_chain_review", endpoint_id=item.endpoint_id, angle_id=angle_id)
            self.add_edge(angle_id, chain_id, "test_angle", "chaining")

            for evidence in evidences:
                self.add_node(evidence["id"], "evidence", evidence["label"], evidence["status"], path=evidence.get("path", ""), test_id=item.test_id)
                self.add_edge(chain_id, evidence["id"], "chaining", "evidence")
            first_evidence = evidences[0]["id"]
            path_nodes["evidence"] = first_evidence

            self.add_node(finding_id, "finding", finding_label, finding_status, endpoint_id=item.endpoint_id, angle_id=angle_id, test_id=item.test_id)
            for evidence in evidences:
                self.add_edge(evidence["id"], finding_id, "evidence", "finding")

            missing = [
                stage["key"]
                for stage in CHAIN_STAGES
                if self.nodes.get(path_nodes.get(stage["key"], ""), {}).get("status") in {"source_incomplete", "needs_context", "needs_chain_review", "evidence_incomplete", "not_reportable_yet"}
            ]
            completeness = round(((len(CHAIN_STAGES) - len(missing)) / len(CHAIN_STAGES)) * 100, 1)
            path_records.append(
                {
                    "id": stable_id("attack-path", item.endpoint_id, angle_id, item.test_id),
                    "endpoint_id": item.endpoint_id,
                    "angle_id": angle_id,
                    "test_id": item.test_id,
                    "status": item.status,
                    "completeness": completeness,
                    "missing_stages": missing,
                    "nodes": path_nodes,
                }
            )

        return {
            "version": "1.0.0",
            "engagement_id": self.state.get("engagement_id") or self.root.name,
            "chain": "JS File -> API Route -> Param -> Auth Role -> Test Angle -> Chaining -> Evidence -> Finding",
            "stages": CHAIN_STAGES,
            "nodes": list(self.nodes.values()),
            "edges": list(self.edges.values()),
            "paths": path_records,
            "metrics": {
                "attack_graph_nodes": len(self.nodes),
                "attack_graph_edges": len(self.edges),
                "attack_paths": len(path_records),
                "complete_paths": sum(1 for path in path_records if path["completeness"] >= 100),
                "needs_chain_review": sum(1 for node in self.nodes.values() if node["status"] == "needs_chain_review"),
                "needs_evidence": sum(1 for node in self.nodes.values() if node["status"] == "evidence_incomplete"),
                "needs_auth_context": sum(1 for node in self.nodes.values() if node["status"] == "needs_context"),
            },
            "neo4j": neo4j_config(),
        }


def build_attack_graph(root: Path) -> dict[str, Any]:
    return AttackGraphBuilder(root).build()


def neo4j_config() -> dict[str, Any]:
    uri = os.environ.get("NEO4J_URI", "").rstrip("/")
    user = os.environ.get("NEO4J_USER", "")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    return {
        "configured": bool(uri and user and os.environ.get("NEO4J_PASSWORD")),
        "uri": uri,
        "user": user,
        "database": database,
        "password_set": bool(os.environ.get("NEO4J_PASSWORD")),
    }


def cypher_bundle(attack_graph: dict[str, Any]) -> dict[str, Any]:
    engagement_id = str(attack_graph.get("engagement_id") or "unknown")
    statements: list[dict[str, Any]] = [
        {
            "statement": "CREATE CONSTRAINT attack_node_id IF NOT EXISTS FOR (n:AttackNode) REQUIRE n.id IS UNIQUE",
            "parameters": {},
        }
    ]
    for node in attack_graph.get("nodes", []):
        stage = str(node.get("stage") or "unknown")
        label = STAGE_NEO4J_LABELS.get(stage, "UnknownStage")
        props = compact_props(
            {
                **(node.get("properties") or {}),
                "id": node.get("id"),
                "engagement_id": engagement_id,
                "stage": stage,
                "stage_label": node.get("stage_label"),
                "label": node.get("label"),
                "status": node.get("status"),
            }
        )
        statements.append(
            {
                "statement": f"MERGE (n:AttackNode:{label} {{id: $id}}) SET n += $props",
                "parameters": {"id": node.get("id"), "props": props},
            }
        )
    for edge in attack_graph.get("edges", []):
        edge_type = str(edge.get("type") or "RELATED_TO")
        if not edge_type.replace("_", "").isalnum():
            edge_type = "RELATED_TO"
        statements.append(
            {
                "statement": (
                    f"MATCH (a:AttackNode {{id: $source}}), (b:AttackNode {{id: $target}}) "
                    f"MERGE (a)-[r:{edge_type} {{engagement_id: $engagement_id}}]->(b) "
                    "SET r.label = $label"
                ),
                "parameters": {
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "engagement_id": engagement_id,
                    "label": edge.get("label") or edge_type,
                },
            }
        )
    return {"statements": statements}


def cypher_text(attack_graph: dict[str, Any]) -> str:
    lines = [
        "// Neo4j import for AI Bug Bounty canonical attack chain",
        f"// Engagement: {attack_graph.get('engagement_id')}",
        f"// Chain: {attack_graph.get('chain')}",
        "CREATE CONSTRAINT attack_node_id IF NOT EXISTS FOR (n:AttackNode) REQUIRE n.id IS UNIQUE;",
        "",
    ]
    for statement in cypher_bundle(attack_graph)["statements"][1:]:
        params = statement["parameters"]
        lines.append(f":params {json.dumps(params, ensure_ascii=False)};")
        lines.append(statement["statement"] + ";")
        lines.append("")
    return "\n".join(lines)
