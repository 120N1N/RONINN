# Integration Map

Hunterflowx uses two local methodology sources as its core hunting profile:

```text
hunterweb
GPTxOPUS
```

Runtime state and proof still live in Hunterflowx events, evidence, graph files,
and dashboard views.

## hunterweb/recon-framework

Use for:

- policy-gated recon
- program-kb validation
- recursive recon
- safe queues
- coverage and handoff checks
- raw evidence provenance

Import into this workflow as:

- `endpoint_discovered`
- `endpoint_seen_runtime`
- `mapping_gap_found`
- `loop_started`
- `source_runtime_diff_added`

Implemented bridge:

```bash
../../../bin/bbf import-reconfw /path/to/reconfw/workspace
```

## GPTxOPUS

Use for:

- source-grounded A01-A10 baseline
- manual test cards
- evidence pack discipline
- creative/off-checklist leads
- retest and report QA

Import into this workflow as:

- `test_planned`
- `endpoint_angle_planned`
- `creative_hypothesis_added`
- `evidence_reviewed`
- `finding_candidate_reviewed`

Implemented through:

```bash
../../../bin/bbf pentest-card a01 --endpoint-id ep-id --asset-id asset-main --method GET --path /api/example
../../../bin/bbf owasp-plan web --endpoint-id ep-id --asset-id asset-main --method GET --path /api/example
../../../bin/bbf angle-plan full --endpoint-id ep-id --asset-id asset-main --method GET --path /api/example
```

## Rule

No imported methodology output can directly become a finding. It must pass:

```text
event -> evidence -> evidence-score -> judge -> fresh-repro -> report lifecycle
```
