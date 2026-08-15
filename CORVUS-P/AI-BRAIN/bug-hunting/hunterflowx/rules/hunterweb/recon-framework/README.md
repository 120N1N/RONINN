# Recon Framework

Policy-gated local framework for authorized Web2 bug bounty reconnaissance.

The framework is designed to collect and normalize high-signal recon data while
failing closed on scope, policy, rate-limit, header, account, and evidence
requirements. It is not a scanner-first system: active target-touching work is
kept behind the program knowledge base and every promoted object must preserve
source and raw-evidence provenance.

## Current Capabilities

Implemented local milestones:

- Milestone 0: workspace generator and durable target scaffold.
- Milestone 1: program-kb ingestion, validation, policy classification, and
  manual override support.
- Milestone 2: canonical models, JSONL storage, SQLite indexes, raw evidence,
  and rejection stores.
- Milestone 3: passive collectors for domains, URLs, and code search with
  provider preflight and live provider modes, including `subfinder`,
  `amass`, and `bbot` subdomain enumeration adapters.
- Milestone 4: exposure provider adapters with old-hit downscoring and
  ambiguous IP handling.
- Milestone 5: DNS normalization, wildcard filtering, DNS/TLS/CNAME baseline
  objects, safe liveness baselines, wrapper artifact ingestion, soft-404
  detection, redirect blocking, and live HTTP baseline evidence.
- Milestone 6: JavaScript/importmap inventory, URL, endpoint, GraphQL,
  WebSocket, SSE, and secret candidate extraction.
- Milestone 7: API, OpenAPI/JSON/YAML schema, GraphQL, WebSocket, browser
  extension, cloud, and signed URL mapping from saved evidence.
- Milestone 8: target-specific wordlist generation with provenance and
  sensitive-term review.
- Milestone 9: policy-gated fuzz queue and saved ffuf result
  normalization.
- Milestone 10: attack-surface graph, coverage gaps, and lead scoring.
- Milestone 11: continuous state diffing and active queue invalidation.
- Milestone 12: promotion checks, report rendering, evidence packs, and
  redaction.
- Coverage and handoff audit: split workspace, real-live, blocker,
  endpoint, API, graph, collector, freshness, and auth readiness gates with
  blocker/warning/accepted-gap summaries.
- Recursive recon: bounded, policy-gated loops that collect passive data,
  classify new assets, queue only safe root probes, refresh derived artifacts,
  and choose the next roots with entropy, tenant-cluster, and evidence-aware
  scoring.

## Commands

Core setup and policy:

```bash
reconfw init-target --workspace "$HUNTERWEB_HOME/bounty/<program>/<target>"
reconfw kb ingest --workspace <path> --policy-url <local-policy.yml>
reconfw kb validate --workspace <path>
reconfw classify asset --workspace <path> --value api.example.com
reconfw classify url --workspace <path> --url https://api.example.com/v1/me
```

Collection and normalization:

```bash
reconfw collect passive --workspace <path> --root example.com
reconfw collect preflight --workspace <path> --kind domains
reconfw collect passive --workspace <path> --root example.com --collectors subfinder,amass,bbot
reconfw collect urls --workspace <path> --root example.com
reconfw collect code --workspace <path> --terms <terms-file>
reconfw collect exposure --workspace <path> --query <provider-query>
reconfw recurse run --workspace <path> --root example.com --collectors subfinder,amass,bbot
reconfw resolve --workspace <path>
reconfw network-baseline --workspace <path>
reconfw baseline --workspace <path> --queue queues/safe-probe.jsonl
reconfw baseline ingest-wrapper --workspace <path> --artifact-root <path>
reconfw extract js-importmaps --workspace <path>
reconfw extract endpoints --workspace <path>
reconfw map apis --workspace <path>
reconfw map openapi --workspace <path> --schema <openapi.yaml>
reconfw wordlists generate --workspace <path>
reconfw fuzz queue --workspace <path> --target <url> --profile <profile.json> --wordlist <wordlist>
reconfw fuzz run --workspace <path> --evidence <ffuf-results.jsonl>
reconfw graph build --workspace <path>
reconfw diff state --workspace <path> --previous <jsonl-or-dir> --current <jsonl-or-dir>
reconfw promote report --workspace <path> --evidence <promotion-candidates.jsonl>
```

Quality gates and handoff:

```bash
reconfw coverage check --workspace <path>
reconfw coverage check --workspace <path> --fail-on-blockers
reconfw handoff --workspace <path>
```

## Safety Model

- Unknown and out-of-scope assets cannot enter active queues.
- Internal-looking in-scope names require manual review before active queueing
  unless explicitly allowed by program-kb configuration or manual override.
- HTTP baselines send live low-impact GET/HEAD requests by default for
  active-allowed safe-probe queue items.
- Active actions require `in_scope`, an allowed safe action, configured rate
  profile, and required headers/user-agent where applicable.
- Authenticated and state-changing work requires owned-account and owned-object
  context.
- Passive and exposure provider calls are enabled in the CLI by default, while
  missing binaries, missing API keys, timeouts, and zero-yield runs are recorded
  as collector health warnings or accepted gaps.
- Fuzzing requires a valid profile, calibration, stop conditions, rate limits,
  and policy permission.
- Secret candidates are redacted and never validated against real services.
- Live baseline coverage requires `output/live-probes/baselines.jsonl` records
  from framework HTTP or wrapper ingestion.
- Wrapper ingestion records cookie/header metadata only; cookie values, bearer
  tokens, CSRF tokens, and session identifiers must stay out of notes and
  normalized records.
- Scanner or tool output cannot directly become a finding; promotion follows
  `notes -> leads -> primitives -> findings -> reports`.

## Workspace Scaffold

`reconfw init-target` creates the program-kb, normalized data directories,
metrics, coverage outputs, notes, promotion folders, report templates, and the
full recon deliverable set required by the local workflow:

```text
scope.md
sources.md
business.md
technical-business.md
architecture.md
assets.md
notes/rules.md
notes/recon.md
notes/recent-state.md
notes/live-probing.md
notes/traffic-map.md
notes/loop/queue.md
notes/loop/log.md
security-model.md
features/
attack-surface.md
coverage-matrix.md
unknowns.md
priority-testing-plan.md
leads/
primitives/
findings/
reports/
output/live-probes/
```

Existing user-authored notes are preserved. Generated files are only written
when missing.

## Development Checks

```bash
uv run pytest
uv run ruff check .
uv run reconfw --help
```
