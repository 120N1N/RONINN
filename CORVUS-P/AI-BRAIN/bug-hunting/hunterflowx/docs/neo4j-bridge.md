# Neo4j Attack Graph Bridge

Neo4j is optional. The workflow still treats the local event ledger and
`data/graph_state.json` as the primary source of truth. Neo4j is used as a
relationship database for deeper attack-path questions.

Canonical chain:

```text
JS File -> API Route -> Param -> Auth Role -> Test Angle -> Chaining -> Evidence -> Finding
```

The `JS File` stage also accepts source files from PHP, Python, Java, mobile
decompile output, or any reviewed source artifact. The key rule is that the
source must be linked to a route before testing claims become reportable.

## Dashboard Endpoints

```text
GET /api/attack-graph?engagement=<program>/<target>
GET /api/neo4j/status
GET /api/neo4j/cypher?engagement=<program>/<target>
GET /api/neo4j/cypher?engagement=<program>/<target>&format=json
```

The dashboard renders the canonical attack chain even when Neo4j is not
configured. Missing stages are visible as `needs_context`,
`needs_chain_review`, `evidence_incomplete`, or `not_reportable_yet`.

## Export Cypher

```bash
python3 scripts/neo4j_sync.py \
  --root engagements/<program>/<target>
```

This writes:

```text
engagements/<program>/<target>/data/neo4j_attack_graph.cypher
```

## Push To Neo4j

Start Neo4j locally, then set credentials:

```bash
export NEO4J_URI=http://127.0.0.1:7474
export NEO4J_USER=neo4j
export NEO4J_PASSWORD='change-me'
export NEO4J_DATABASE=neo4j

python3 scripts/neo4j_sync.py \
  --root engagements/<program>/<target> \
  --push
```

The sync uses `MERGE`, so repeated runs update the same nodes instead of
duplicating them.

## Useful Cypher Queries

Untested or weak chain stages:

```cypher
MATCH p=(s:JsFile)-[:DISCOVERS_ROUTE]->(:ApiRoute)-[:HAS_PARAM]->(:Param)
      -[:REQUIRES_ROLE]->(:AuthRole)-[:TESTED_BY]->(:TestAngle)
      -[:CHAINS_TO]->(c:Chaining)
WHERE c.status = "needs_chain_review"
RETURN p
LIMIT 25;
```

Evidence-incomplete paths:

```cypher
MATCH p=(:TestAngle)-[:CHAINS_TO]->(:Chaining)-[:SUPPORTED_BY]->(e:Evidence)
WHERE e.status = "evidence_incomplete"
RETURN p
LIMIT 25;
```

Reportable candidates:

```cypher
MATCH p=(:JsFile)-[:DISCOVERS_ROUTE]->(:ApiRoute)-[:HAS_PARAM]->(:Param)
      -[:REQUIRES_ROLE]->(:AuthRole)-[:TESTED_BY]->(:TestAngle)
      -[:CHAINS_TO]->(:Chaining)-[:SUPPORTED_BY]->(:Evidence)
      -[:RESULTS_IN]->(f:Finding)
WHERE f.status IN ["finding_candidate", "confirmed"]
RETURN p
LIMIT 25;
```
