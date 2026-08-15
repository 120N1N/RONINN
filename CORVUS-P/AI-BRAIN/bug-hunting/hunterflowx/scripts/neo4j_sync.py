#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from attack_graph import build_attack_graph, cypher_bundle, cypher_text


def post_neo4j(uri: str, user: str, password: str, database: str, statements: list[dict[str, object]], timeout: float) -> dict[str, object]:
    endpoint = f"{uri.rstrip('/')}/db/{database}/tx/commit"
    payload = json.dumps({"statements": statements}).encode("utf-8")
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    request = Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"neo4j http error {exc.code}: {body}") from exc
    except URLError as exc:
        raise SystemExit(f"neo4j connection error: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Export or push the canonical attack-chain graph to Neo4j.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--out", type=Path, help="Write Browser/Cypher-shell friendly Cypher to this file")
    parser.add_argument("--json-out", type=Path, help="Write canonical attack graph JSON to this file")
    parser.add_argument("--push", action="store_true", help="Push statements to Neo4j over the HTTP transactional endpoint")
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "http://127.0.0.1:7474"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", ""))
    parser.add_argument("--database", default=os.environ.get("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    root = args.root.resolve()
    graph = build_attack_graph(root)
    bundle = cypher_bundle(graph)

    out_path = args.out or root / "data" / "neo4j_attack_graph.cypher"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(cypher_text(graph), encoding="utf-8")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    print(f"attack_graph_nodes: {len(graph.get('nodes', []))}")
    print(f"attack_graph_edges: {len(graph.get('edges', []))}")
    print(f"attack_paths: {len(graph.get('paths', []))}")
    print(f"cypher_out: {out_path}")

    if not args.push:
        print("neo4j_push: skipped (use --push with NEO4J_PASSWORD set)")
        return 0

    if not args.password:
        raise SystemExit("missing Neo4j password: set NEO4J_PASSWORD or pass --password")

    result = post_neo4j(args.uri, args.user, args.password, args.database, bundle["statements"], args.timeout)
    errors = result.get("errors") or []
    if errors:
        print(json.dumps(errors, indent=2), file=sys.stderr)
        return 1
    print(f"neo4j_push: ok ({args.uri.rstrip('/')}/browser/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
