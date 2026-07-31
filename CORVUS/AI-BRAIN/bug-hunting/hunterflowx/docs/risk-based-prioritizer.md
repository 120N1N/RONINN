# Risk-Based Prioritizer

`bbf risk-prioritize` memilih endpoint yang paling worth diuji dulu saat
engagement besar. Ini bukan scanner dan tidak menjalankan traffic. Ia membaca
event log lalu membuat ranked testing queue.

## Jalankan

```bash
cd engagements/<program>/<target>
../../../bin/bbf risk-prioritize --limit 25
```

Profil yang tersedia:

```bash
../../../bin/bbf risk-prioritize --profile balanced
../../../bin/bbf risk-prioritize --profile impact
../../../bin/bbf risk-prioritize --profile coverage
../../../bin/bbf risk-prioritize --profile source
../../../bin/bbf risk-prioritize --profile runtime
```

## Sinyal Skor

Skor 0-100 dibuat dari durable workflow state:

| Signal | Meaning |
|---|---|
| business-impact keywords | admin, billing, invoice, export, token, tenant, upload, webhook, etc. |
| runtime reachability | `endpoint_seen_runtime`, `endpoint_verified_reachable` |
| write capability | POST/PUT/PATCH/DELETE gets higher priority |
| parameters | more inputs usually mean more attack surface |
| source context | `source_flow_linked`, source/runtime diff, mapped source attack surface |
| boundary angles | authn, authz, object/tenant, field-level authorization |
| chaining | `chain_candidate_added`, `attack_path_expanded` |
| coverage gap | planned but untested endpoint angles |

Reducers:

```text
tested_secure
evidence_sufficient
confirmed
out_of_scope
by_design
blocked/gap
```

## Output

```text
priority-testing-plan.md
data/risk_priorities.json
data/events.jsonl       # endpoint_prioritized, risk_prioritization_reviewed
data/graph_state.json   # rebuilt unless --no-build
```

Dashboard metrics:

```text
risk_endpoints_ranked
risk_top_score
risk_avg_score
risk_priority_p0
risk_priority_p1
risk_priority_p2
risk_priority_p3
```

Priority meaning:

```text
P0 = test first when scope and safety allow it
P1 = high-value next queue
P2 = useful but behind stronger signals
P3 = low signal or already mostly handled
```

## Operational Rule

Run this after every major recon/import/source-review batch:

```text
recon/import/source verify -> risk-prioritize -> angle-plan/angle-exec -> evidence-score
```

When time is limited, start with P0/P1 endpoints that have readiness `ready` or
`needs_context`, then unblock high-score endpoints that are blocked only by
missing role/session/source context.
