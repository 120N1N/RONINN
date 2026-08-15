# Massive Recon Framework Execution Plan

Date: 2026-04-30

This document is the build plan for `docs/massive-recon-framework.md`. The goal
is to turn the design into an effective, testable, program-aware recon system
that produces high-signal data for authorized bug bounty engagements.

This is an execution plan, not a target runbook. It explains what to build, in
what order, which resources and tools are needed, what each module must output,
and how to prove the implementation matches the design.

## How To Use This Plan

Treat this document as the implementation backlog for
`/home/hunterweb/recon-framework/`. Build it in milestone order and do not
advance to the next active-capability milestone until the current milestone's
acceptance gates pass against fixtures.

Execution rules for engineers:

- [ ] Start every milestone by adding or updating schemas and fixtures.
- [ ] Add policy and storage tests before wiring real tools.
- [ ] Preserve raw evidence before writing normalizers.
- [ ] Make every CLI command support dry-run mode before live execution.
- [ ] Keep active network capability behind the policy engine, even in tests.
- [ ] Emit metrics and rejected-object records from the first implementation,
  not as a later cleanup task.
- [ ] Stop a milestone when its acceptance gates pass; defer unrelated
  refinements to later milestones.

The first usable vertical slice is:

```text
init-target
  -> program-kb ingest and validate
  -> classify passive subdomain fixture data
  -> write normalized host objects
  -> generate safe_probe_queue only for in-scope assets
  -> run mocked liveness baseline
  -> write metrics, evidence refs, and recent-state
```

This slice proves the control model before real collectors, crawlers, fuzzers,
or authenticated workflows are connected.

## Build Goals

Build a local framework that can:

```text
ingest a bug bounty program policy
store full program context in program-kb
classify discovered assets against scope and rules
run passive collectors at massive scale
run active baseline probes only when allowed
extract JS, URLs, APIs, GraphQL, WebSocket, mobile, cloud, and workflow data
generate target-specific wordlists
build an attack-surface graph
create policy-safe fuzz queues
run ffuf and specialized fuzz profiles with calibration
score and promote high-signal leads
track evidence through notes -> leads -> primitives -> findings -> reports
rerun continuously and diff changes
prove safety, data quality, and design invariants with tests
```

## Non-Negotiable Safety And Scope Rules

The implementation must enforce these before broad collector coverage:

```text
unknown assets are passive-only
out-of-scope assets are blocked
active requests require in_scope plus allowed action
fuzzing requires explicit profile, calibration, rate limit, and stop conditions
auth testing requires owned-account context
all tool output is preserved raw before normalization
all normalized objects include source_refs, raw_evidence_paths, scope_status,
  testability, confidence, state, and next_action
no scanner-only output can become a finding
```

## Recommended Implementation Stack

Use boring, durable components first. The framework should run locally in
`/home/hunterweb` and should not depend on a remote service for core logic.

```text
language:
  Python 3.12+ for orchestration, normalization, policy engine, adapters,
  schemas, and CLI

CLI:
  Typer or argparse

schema validation:
  Pydantic v2 or dataclasses plus jsonschema

storage:
  JSONL as the canonical append-friendly interchange format
  SQLite for indexed local queries and queue state
  optional DuckDB for large JSONL analytics
  optional NetworkX or SQLite edge tables for graph MVP

tool runners:
  subprocess wrappers with strict allowlists, timeout, rate profile, stdout,
  stderr, exit code, raw output path, and tool version capture

HTTP client:
  httpx Python library or requests with retry/backoff; do not confuse this with
  ProjectDiscovery httpx CLI

browser automation:
  Playwright for screenshots, HAR capture, browser route discovery, and
  authenticated workflow observation

testing:
  pytest
  pytest-cov
  responses/respx for mocked HTTP APIs
  golden JSONL fixtures for collector output

packaging:
  pyproject.toml
  uv or pip-tools for dependency pinning

secrets:
  local files under /home/hunterweb/secrets/
  environment variables for API keys
  never store tokens in notes, reports, or normalized summaries
```

### Developer Setup Commands

Use these commands for the initial implementation workspace:

```bash
cd /home/hunterweb
mkdir -p recon-framework
cd recon-framework
uv init --package
uv add typer pydantic pyyaml httpx rich
uv add --dev pytest pytest-cov respx ruff
```

If `uv` is unavailable, use a Python virtual environment and pinned
`requirements.txt`. Do not block framework design on package-manager choice;
keep dependency versions pinned once implementation starts.

Required first checks:

```bash
uv run pytest
uv run ruff check .
uv run reconfw --help
```

## Repository Layout To Build

Create this implementation layout when moving from documentation to code:

```text
/home/hunterweb/recon-framework/
  pyproject.toml
  README.md
  reconfw/
    __init__.py
    cli.py
    config.py
    paths.py
    models/
      base.py
      program.py
      scope.py
      assets.py
      endpoints.py
      evidence.py
      queues.py
      findings.py
    policy/
      engine.py
      matchers.py
      confidence.py
      decisions.py
    storage/
      jsonl.py
      sqlite.py
      evidence_store.py
      migrations.py
    collectors/
      base.py
      subfinder.py
      amass.py
      crtsh.py
      securitytrails.py
      shodan.py
      censys.py
      fofa.py
      urlscan.py
      commoncrawl.py
      github.py
      virustotal.py
      otx.py
    runners/
      command.py
      rate_limit.py
      wrappers.py
      ffuf.py
      httpx_pd.py
      dnsx.py
      katana.py
      playwright.py
    normalize/
      dns.py
      urls.py
      http.py
      js.py
      api.py
      graphql.py
      mobile.py
      cloud.py
    pipeline/
      phase0_program_kb.py
      phase1_seeds.py
      phase2_passive.py
      phase3_exposure.py
      phase4_dns.py
      phase5_liveness.py
      phase6_js.py
      phase7_endpoints.py
      phase8_api.py
      phase9_mobile.py
      phase10_code_registry.py
      phase11_cloud.py
      phase12_auth.py
      phase13_workflows.py
      phase14_fuzz.py
      phase15_wordlists.py
      phase16_graph.py
      phase17_scoring.py
      phase18_promotion.py
      phase19_diff.py
      phase20_handoff.py
    scoring/
      signals.py
      ranker.py
    graph/
      builder.py
      queries.py
    reports/
      render.py
      templates/
    tests/
      fixtures/
      test_policy_engine.py
      test_scope_invariants.py
      test_normalizers.py
      test_dedupe.py
      test_queue_gates.py
      test_ffuf_calibration.py
      test_promotion_gates.py
```

Target workspaces remain under:

```text
/home/hunterweb/bounty/<program>/<target>/
```

The framework code should create and update those target workspaces using the
layout defined in `docs/massive-recon-framework.md`.

## Execution Strategy

Build the framework as a sequence of small, testable control-plane features
before adding broad data-plane coverage. The implementation should become
useful early, but it must remain conservative until policy, evidence, and queue
gates are reliable.

### Milestone Dependency Rules

- [ ] Milestone 0 must create the target workspace exactly once and safely
  update it on repeated runs.
- [ ] Milestones 1 and 2 are prerequisites for every collector and runner.
- [ ] Milestones 3 and 4 may run with missing API keys by marking providers
  unavailable and writing metrics.
- [ ] Milestone 5 is the first milestone allowed to touch in-scope target
  infrastructure.
- [ ] Milestones 6 through 8 may enrich and queue work but must not run fuzzing.
- [ ] Milestone 9 must run only against fixtures until calibration and stop
  monitor tests pass.
- [ ] Milestones 10 through 12 consume evidence-backed objects; they must not
  create direct findings from tool output.

### Per-Milestone Work Pattern

Use the same sequence for every milestone:

```text
1. define or update Pydantic models
2. add golden fixtures
3. add validation and policy tests
4. implement storage and normalization
5. add CLI dry-run behavior
6. add real collector or runner wiring when applicable
7. emit metrics and rejected-object records
8. update recent-state and coverage outputs
9. run acceptance tests
```

### Minimum Pull Request Shape

Each implementation change should include:

- [ ] code for one milestone or one narrow part of a milestone
- [ ] fixtures covering success, blocked, rejected, and stale cases
- [ ] tests for policy gates and schema validation
- [ ] CLI help text or README notes for any new command
- [ ] metric emission for the new phase
- [ ] no secrets, tokens, cookies, or private report material

## Build Milestones

### Milestone 0: Skeleton And Workspace Generator

Deliverables:

```text
reconfw init-target --workspace /home/hunterweb/bounty/<program>/<target>
target workspace directory generator
schema_version and framework_version constants
empty program-kb, assets, queues, metrics, coverage, output directories
runbook template generation
```

Acceptance gates:

```text
all required directories exist
notes/recent-state.md is created
metrics/recon-metrics.json is created
metrics/phase-quality.jsonl is appendable
runbooks are generated
no secrets are written into workspace files
```

### Milestone 1: Program Knowledge Base And Policy Engine

This is the foundation. Do not build active tooling before this works.

Build:

```text
program-kb schema
scope matcher for exact domains, wildcard domains, IP ranges, apps, APIs, repos
exclusion precedence
third-party classification
action allow/block matrix
confidence model
decision-log writer
missing-info writer
manual override model with expiry and revisit condition
```

CLI:

```text
reconfw kb ingest --workspace <path> --policy-url <url>
reconfw kb validate --workspace <path>
reconfw classify asset --workspace <path> --value api.example.com
reconfw classify url --workspace <path> --url https://api.example.com/v1/me
```

Acceptance tests:

```text
unknown asset cannot enter active queues
explicit exclusion beats wildcard include
third-party CNAME becomes needs_review/passive_only unless included
active action without rate profile is blocked
active action without required headers is blocked
stale policy fails active queue generation
```

### Milestone 2: Canonical Models, Storage, And Evidence Store

Build:

```text
BaseObject model
SourceRef model
EvidenceRef model
Asset models: domain, host, ip, service, url, endpoint, js, mobile, cloud
QueueItem model
Decision model
Metric model
Rejection model
JSONL writer with atomic append
SQLite indexer for lookups and dedupe
raw evidence store
rejected object store
```

Required metadata on every object:

```text
id, type, value, normalized_value, source_refs, raw_evidence_paths,
retrieved_at, first_seen, last_seen, freshness, scope_status, testability,
confidence, owner_evidence, third_party_status, business_relevance,
security_boundary_relevance, risk_score, noise_score, dedupe_key, state,
next_action, blocking_reason, schema_version
```

Acceptance tests:

```text
malformed object goes to output/rejected/
object without source_refs cannot be promoted
duplicate endpoint merges source_refs and evidence paths
stale object is historical until revalidated
```

### Milestone 3: Passive Collector Adapters

Build adapters that preserve raw output and normalize into canonical JSONL.

Initial collectors:

```text
subfinder
OWASP Amass passive/intel
crt.sh or CT log adapter
SecurityTrails
VirusTotal domain relationships
AlienVault OTX
urlscan.io search
Common Crawl CDX
GitHub code search
GitLab search
```

CLI:

```text
reconfw collect passive --workspace <path> --root example.com
reconfw collect urls --workspace <path> --root example.com
reconfw collect code --workspace <path> --terms output/wordlists/terms.txt
```

Acceptance gates:

```text
raw output stored before normalization
source_refs include query, tool/API, timestamp, and raw path
unknown results stay passive-only
duplicates merge cleanly
collector API failure does not fail whole run
provider quotas are respected and recorded
```

### Milestone 4: Exposure Provider Adapters

Build:

```text
Shodan adapter
Censys adapter
FOFA adapter
Netlas adapter
optional ZoomEye/BinaryEdge/LeakIX/Criminal IP adapters
```

Normalize:

```text
provider, query, host, ip, port, protocol, title, banner_hash, favicon_hash,
tls_subject, tls_sans, org, asn, country, first_seen, last_seen, technologies,
raw_evidence_path, scope_status, testability, confidence
```

Acceptance gates:

```text
provider last_seen is captured
IP ownership is never assumed from a banner alone
private/reserved ranges are blocked
old exposure hits are downscored
ambiguous IPs become passive_only or needs_review
```

### Milestone 5: DNS, Liveness, And Baselines

Build:

```text
dnsx runner
DNS normalizer
wildcard DNS detector
CNAME third-party classifier
ProjectDiscovery httpx runner
HTTP baseline model
soft-404 detector
auth-redirect detector
WAF/block-page detector
TLS/header/cookie/CSP/CORS extractor
screenshot capture with Playwright
```

CLI:

```text
reconfw resolve --workspace <path>
reconfw baseline --workspace <path> --queue queues/safe-probe.jsonl
```

Acceptance gates:

```text
no liveness probe for unknown/out-of-scope assets
required headers and user-agent are attached by wrapper
out-of-scope redirects are not followed
wildcard DNS is filtered
random-path baseline is captured before path fuzzing
```

### Milestone 6: JavaScript, URL, And Endpoint Extraction

Build:

```text
script inventory collector
JS hash store
source map detector
route extractor
API base URL extractor
GraphQL operation extractor
WebSocket/SSE URL extractor
service worker parser
URL canonicalizer
endpoint template inferencer
parameter extractor
state-changing endpoint detector
```

Inputs:

```text
live pages
httpx responses
Playwright HARs
katana output
urlscan results
Common Crawl pages
mobile/extension JS artifacts
```

Acceptance gates:

```text
third-party scripts are separated
duplicate script hashes are merged
secret candidates are never validated against services
archive-only URLs are historical until live-confirmed
endpoint auth/state hints are marked inferred unless observed live
```

### Milestone 7: API, GraphQL, WebSocket, Mobile, And Cloud Mapping

Build:

```text
OpenAPI/Swagger parser
Postman collection parser
GraphQL endpoint/schema/operation model
GraphQL suggestions/introspection result parser
WebSocket handshake and message inventory model
mobile artifact metadata parser
browser extension manifest parser
cloud/CDN/storage object model
signed URL workflow model
```

Acceptance gates:

```text
schema claims require evidence
state-changing API tests require owned objects and allowed action
WebSocket observations include auth and role context
mobile-only hosts pass classifier before active probing
storage permission checks are blocked unless policy permits
```

### Milestone 8: Target-Specific Wordlist Generator

Build:

```text
tokenizer
normalizer
source provenance tracker
term ranker
category splitter
stale-term downscorer
dangerous/noisy term filter
```

Wordlist outputs:

```text
output/wordlists/subdomains.txt
output/wordlists/vhosts.txt
output/wordlists/paths.txt
output/wordlists/api-paths.txt
output/wordlists/params.txt
output/wordlists/json-fields.txt
output/wordlists/graphql-paths.txt
output/wordlists/graphql-fields.txt
output/wordlists/headers.txt
output/wordlists/content-types.txt
output/wordlists/cloud-names.txt
```

Acceptance gates:

```text
every generated term has source_refs
generic and target-specific terms remain separate
sensitive terms require review before fuzz use
```

### Milestone 9: Fuzz Queue And ffuf Runner

Build:

```text
fuzz profile schema
ffuf runner
calibration runner
soft-404/auth-redirect/WAF clustering
response clusterer
result normalizer
stop-condition monitor
fuzz anomaly writer
```

Initial ffuf profiles:

```text
subdomain DNS fuzzing
vhost fuzzing
web path fuzzing
API path fuzzing
parameter fuzzing
JSON key fuzzing
server-side parameter pollution fuzzing
content-type fuzzing
method fuzzing
header fuzzing
GraphQL endpoint fuzzing
GraphQL operation fuzzing
GraphQL suggestions fuzzing
GraphQL introspection checks
```

Acceptance gates:

```text
fuzz job cannot run without in_scope, allowed action, rate profile, calibration,
  stop conditions, output path, and payload class
calibration failure blocks the job
baseline-equivalent hits are suppressed
out-of-scope redirects are not followed
findings cannot be created directly from fuzz output
```

### Milestone 10: Attack-Surface Graph And Lead Scoring

Build:

```text
graph node/edge model
graph builder from normalized objects
relationship dedupe
trust-boundary path queries
coverage-gap queries
lead score model
lead explanation model
priority-testing-plan renderer
```

Lead scoring inputs:

```text
business criticality
auth boundary
tenant boundary
role difference
owned object control
sensitive data potential
state-change potential
file/callback surface
legacy/hidden signal
policy restriction
scope uncertainty
third-party risk
rate-limit uncertainty
```

Acceptance gates:

```text
edges require evidence
inferred edges are labeled
unknown-scope nodes cannot unlock active actions
lead requires evidence path, boundary hypothesis, policy status, and next action
scanner-only hits stay notes/candidate
```

### Milestone 11: Continuous Recon And Diffing

Build:

```text
previous/current JSONL state loader
diff engine
policy-change reclassifier
freshness expirer
queue invalidator
new/removed/changed object summarizer
recent-state updater
```

Acceptance gates:

```text
policy changes invalidate affected active queues
stale data expires or becomes historical
added/removed/changed objects are separated
newly in-scope items re-enter passive enrichment before active probing
```

### Milestone 12: Promotion Pipeline And Reporting

Build:

```text
lead template
primitive template
finding template
report template renderer
six-gate validator
novelty/policy checklist
evidence pack builder
redaction helper
```

Acceptance gates:

```text
lead cannot become primitive without reproducible owned-account control
primitive cannot become finding without demonstrated boundary impact
finding cannot become report without exact repro, scope proof, evidence, impact,
  novelty, and policy fit
secrets and unrelated personal data are redacted
```

## CLI Command Plan

The CLI should expose the framework without requiring users to run raw tools
directly. Every command that can touch a target must support `--dry-run` and
must print the policy decision that would allow or block the action.

```text
reconfw init-target --workspace <path>
reconfw kb ingest --workspace <path> --policy-url <url>
reconfw kb validate --workspace <path>
reconfw classify asset --workspace <path> --value <host-or-domain>
reconfw classify url --workspace <path> --url <url>
reconfw collect passive --workspace <path>
reconfw collect exposure --workspace <path>
reconfw resolve --workspace <path>
reconfw baseline --workspace <path>
reconfw crawl --workspace <path>
reconfw extract js --workspace <path>
reconfw inventory api --workspace <path>
reconfw wordlists build --workspace <path>
reconfw fuzz plan --workspace <path>
reconfw fuzz run --workspace <path> --job <job-id>
reconfw graph build --workspace <path>
reconfw leads score --workspace <path>
reconfw diff --workspace <path>
reconfw coverage check --workspace <path>
reconfw handoff --workspace <path>
```

Command behavior rules:

- [ ] `init-target` is idempotent and never overwrites non-generated notes.
- [ ] `kb ingest` writes raw policy evidence before parsing.
- [ ] `kb validate` fails closed when scope, exclusions, rate limits, or
  required headers are missing for active actions.
- [ ] `classify` prints decision, confidence, evidence used, allowed actions,
  blocked actions, and review reason.
- [ ] `collect passive` never sends requests to target infrastructure.
- [ ] `baseline`, `crawl`, `resolve --active`, and `fuzz run` require policy
  authorization and rate profiles.
- [ ] `fuzz plan` creates queue items but does not run them.
- [ ] `handoff` refuses to finish if jobs are still running or safety events are
  unresolved.

## Configuration Files

### `config/collectors.yml`

```yaml
collectors:
  subfinder:
    enabled: true
    mode: passive
    binary: subfinder
    output: jsonl
  amass:
    enabled: true
    mode: passive
  securitytrails:
    enabled: true
    api_key_env: SECURITYTRAILS_API_KEY
  shodan:
    enabled: true
    api_key_env: SHODAN_API_KEY
  censys:
    enabled: true
    api_id_env: CENSYS_API_ID
    api_secret_env: CENSYS_API_SECRET
  fofa:
    enabled: false
    api_key_env: FOFA_API_KEY
  urlscan:
    enabled: true
    api_key_env: URLSCAN_API_KEY
```

### `config/scope-rules.yml`

```yaml
required_headers:
  User-Agent: "program-required-user-agent"
rate_profiles:
  passive_api:
    requests_per_second: 1
  safe_baseline:
    requests_per_second: 0.2
  fuzz_low:
    requests_per_second: 0.1
redirects:
  follow_out_of_scope: false
private_ranges:
  active_probe: blocked
```

### `config/fuzz-profiles.yml`

```yaml
profiles:
  web_paths_low:
    tool: ffuf
    methods: ["GET"]
    requires:
      - in_scope
      - safe_baseline
      - soft_404_calibration
    status_interest: [200, 204, 301, 302, 307, 308, 401, 403]
    stop_on: [429, 5xx_spike, waf_block, out_of_scope_redirect]
```

### `program-kb/program.json`

```json
{
  "schema_version": "1.0",
  "program": {
    "platform": "hackerone|bugcrowd|intigriti|other",
    "name": "example",
    "program_id": "external-id",
    "policy_url": "https://example.invalid/policy",
    "policy_retrieved_at": "2026-04-30T00:00:00Z"
  },
  "automation": {
    "required_user_agent": "program-required-agent",
    "required_headers": {},
    "max_concurrency": 1,
    "default_rate_profile": "safe_baseline",
    "allowed_windows_utc": []
  },
  "accounts": {
    "owned_account_context_required": true,
    "auth_material_paths": [
      "/home/hunterweb/secrets/recon/example/account-a.env",
      "/home/hunterweb/secrets/recon/example/account-b.env"
    ]
  }
}
```

### `program-kb/scope.json`

```json
{
  "schema_version": "1.0",
  "in_scope": [
    {
      "id": "SCOPE-001",
      "type": "wildcard_domain",
      "value": "*.example.com",
      "allowed_actions": ["dns", "http_head", "http_get_root", "js_inventory"],
      "fuzz_profiles": ["web_paths_low"],
      "source_ref": "program-policy-2026-04-30"
    }
  ],
  "out_of_scope": [
    {
      "id": "EXCL-001",
      "type": "hostname",
      "value": "admin.example.com",
      "blocked_actions": ["active_testing", "fuzzing"],
      "source_ref": "program-policy-2026-04-30"
    }
  ],
  "third_party_rules": {
    "default": "passive_only",
    "included_vendors": [],
    "review_required_for_cname": true
  }
}
```

### `program-kb/rate-limits.json`

```json
{
  "schema_version": "1.0",
  "profiles": {
    "passive_api": {
      "requests_per_second": 1,
      "concurrency": 1,
      "burst": 1
    },
    "safe_baseline": {
      "requests_per_second": 0.2,
      "concurrency": 1,
      "burst": 1
    },
    "fuzz_low": {
      "requests_per_second": 0.1,
      "concurrency": 1,
      "burst": 1,
      "max_requests_per_job": 500
    }
  }
}
```

### `program-kb/safe-actions.json`

```json
{
  "schema_version": "1.0",
  "actions": {
    "passive_collection": {
      "requires_in_scope": false,
      "allowed_for_unknown": true,
      "requires_rate_profile": false
    },
    "http_get_root": {
      "requires_in_scope": true,
      "allowed_for_unknown": false,
      "requires_rate_profile": true,
      "requires_headers": true,
      "state_changing": false
    },
    "crawl_low_rate": {
      "requires_in_scope": true,
      "allowed_for_unknown": false,
      "requires_rate_profile": true,
      "requires_headers": true,
      "state_changing": false,
      "max_depth_default": 2
    },
    "ffuf_path_low": {
      "requires_in_scope": true,
      "allowed_for_unknown": false,
      "requires_rate_profile": true,
      "requires_headers": true,
      "requires_fuzz_profile": true,
      "requires_calibration": true,
      "requires_stop_conditions": true,
      "state_changing": false
    },
    "authz_diff_owned": {
      "requires_in_scope": true,
      "requires_owned_account_context": true,
      "requires_owned_objects": true,
      "requires_rate_profile": true,
      "state_changing": "profile_dependent"
    }
  },
  "blocked_by_default": [
    "high_volume_scan",
    "brute_force",
    "password_attack",
    "destructive_state_change",
    "billing_action",
    "spam",
    "real_user_data_access",
    "third_party_testing",
    "credential_validation"
  ]
}
```

### `config/target.env.example`

```bash
# Program identity
RECON_PROGRAM_NAME=example
RECON_TARGET_NAME=example-main
RECON_WORKSPACE=/home/hunterweb/bounty/example/example-main

# Optional passive and exposure providers
SHODAN_API_KEY_FILE=/home/hunterweb/secrets/recon/shodan_api_key
CENSYS_API_ID_FILE=/home/hunterweb/secrets/recon/censys_api_id
CENSYS_API_SECRET_FILE=/home/hunterweb/secrets/recon/censys_api_secret
SECURITYTRAILS_API_KEY_FILE=/home/hunterweb/secrets/recon/securitytrails_api_key
VIRUSTOTAL_API_KEY_FILE=/home/hunterweb/secrets/recon/virustotal_api_key
URLSCAN_API_KEY_FILE=/home/hunterweb/secrets/recon/urlscan_api_key
FOFA_API_KEY_FILE=/home/hunterweb/secrets/recon/fofa_api_key
NETLAS_API_KEY_FILE=/home/hunterweb/secrets/recon/netlas_api_key
GITHUB_TOKEN_FILE=/home/hunterweb/secrets/recon/github_token
GITLAB_TOKEN_FILE=/home/hunterweb/secrets/recon/gitlab_token

# Owned-account auth material paths. Values live in these files, not here.
OWNED_ACCOUNT_A_ENV=/home/hunterweb/secrets/recon/example/account-a.env
OWNED_ACCOUNT_B_ENV=/home/hunterweb/secrets/recon/example/account-b.env
CALLBACK_SERVER_ENV=/home/hunterweb/secrets/recon/example/callback.env
```

## Data Schemas And Storage Approach

The implementation should use Pydantic models as the validation boundary,
append-only JSONL as the durable interchange format, and SQLite indexes for
queue state, dedupe, graph traversal, and fast lookups. Raw output is always
written before parsing. Normalized objects are derived artifacts that can be
rebuilt from raw evidence plus program-kb decisions.

### Canonical Storage Rules

- [ ] Store raw collector and runner output under `output/raw/<phase>/<source>/`.
- [ ] Store normalized records under `output/normalized/<phase>/<type>.jsonl`.
- [ ] Store rejected records under `output/rejected/<phase>/<reason>.jsonl`.
- [ ] Store active request/response evidence under `output/evidence/<phase>/<object-id>/`.
- [ ] Store queue state in JSONL and mirror it into SQLite for locking and retry state.
- [ ] Preserve `source_refs`, `raw_evidence_paths`, `schema_version`, and `decision_id` on every normalized object.
- [ ] Treat JSONL files as append-only; use compaction jobs to write deduped snapshots.
- [ ] Keep SQLite rebuildable from JSONL and raw evidence.

### Core Tables

```text
objects:
  id, type, value, normalized_value, dedupe_key, scope_status, testability,
  confidence, state, first_seen, last_seen, freshness, risk_score, noise_score

source_refs:
  id, object_id, source_type, source_name, source_query, retrieved_at,
  raw_evidence_path, auth_context_id

decisions:
  id, object_id, decision, confidence, policy_rules_used, evidence_used,
  allowed_actions, blocked_actions, review_reason, created_at

queue_items:
  item_id, queue_name, source_object_ids, required_preconditions,
  allowed_actions, blocked_actions, rate_profile, auth_context, expected_output,
  stop_conditions, state, created_at, expires_at

jobs:
  job_id, queue_item_id, runner, command_template, started_at, finished_at,
  exit_code, timeout_seconds, raw_stdout_path, raw_stderr_path, raw_output_path

metrics:
  run_id, phase, metric_name, metric_value, timestamp

graph_edges:
  edge_id, source_id, edge_type, target_id, confidence, evidence_refs,
  inferred, freshness, created_at
```

### Canonical Object Schema

```json
{
  "schema_version": "1.0",
  "id": "host:api.example.com",
  "type": "host",
  "value": "api.example.com",
  "normalized_value": "api.example.com",
  "source_refs": ["src:subfinder:20260430:1"],
  "raw_evidence_paths": ["output/raw/passive/subfinder/20260430T000000.jsonl"],
  "retrieved_at": "2026-04-30T00:00:00Z",
  "first_seen": "2026-04-30T00:00:00Z",
  "last_seen": "2026-04-30T00:00:00Z",
  "freshness": "fresh",
  "scope_status": "in_scope",
  "testability": "safe_baseline_allowed",
  "confidence": 0.95,
  "owner_evidence": ["program-policy"],
  "third_party_status": "none",
  "business_relevance": "api",
  "security_boundary_relevance": ["auth", "tenant"],
  "risk_score": 7.2,
  "noise_score": 0.1,
  "dedupe_key": "host:api.example.com",
  "state": "classified",
  "next_action": "queue_safe_baseline",
  "blocking_reason": null
}
```

## Policy Engine Design

The policy engine is the framework's hard safety boundary. It should be a pure
decision module with no network side effects: input object plus program-kb plus
requested action goes in, an explainable allow/block/review decision comes out.

### Decision Order

- [ ] Normalize the input value into domain, host, IP, URL, service, endpoint,
  workflow, or account context.
- [ ] Apply hard network blocks for loopback, link-local, private, reserved,
  metadata, and unsupported schemes unless explicitly included.
- [ ] Apply explicit exclusions before wildcard or inferred inclusions.
- [ ] Apply exact in-scope rules.
- [ ] Apply wildcard, app, repo, mobile, API, and IP-range rules.
- [ ] Classify CNAME, redirect, script, API, storage, and vendor dependencies
  using `third-parties.json`.
- [ ] Compute confidence from policy match, ownership evidence, source count,
  freshness, and third-party status.
- [ ] Check requested action against `safe-actions.json`.
- [ ] Check required headers, user-agent, rate profile, account context, payload
  class, and stop conditions.
- [ ] Emit a decision object and append `program-kb/decision-log.jsonl`.

### Decision Matrix

```text
unknown_do_not_touch:
  passive_collection allowed
  active requests blocked
  fuzzing blocked

out_of_scope:
  passive references may be retained for audit
  active requests blocked
  promotion blocked

third_party:
  passive_collection allowed
  active requests blocked unless explicitly included
  needs_review if wildcard scope and vendor CNAME conflict

in_scope:
  active requests allowed only for listed safe actions and configured rate
  fuzzing allowed only for explicit fuzz profile with calibration
  authenticated testing allowed only with owned-account context
```

### Required Policy APIs

```python
class PolicyEngine:
    def classify_asset(self, value: str) -> Decision: ...
    def classify_url(self, url: str) -> Decision: ...
    def authorize_action(self, object_id: str, action: str, context: ActionContext) -> Decision: ...
    def authorize_queue_item(self, item: QueueItem) -> Decision: ...
    def explain(self, decision_id: str) -> DecisionExplanation: ...
```

### Policy Acceptance Checklist

- [ ] Unknown assets can never be placed into `safe_probe_queue`, `crawl_queue`,
  `api_inventory_queue`, or `fuzz_queue`.
- [ ] Out-of-scope assets are blocked even when a passive source reports a live service.
- [ ] Exclusions beat wildcard includes.
- [ ] Third-party CNAMEs are passive-only or review unless explicitly included.
- [ ] Active actions require `scope_status == in_scope` and an allowed action.
- [ ] Authenticated actions require `auth_context.owned_account == true`.
- [ ] Fuzz actions require `fuzz_profile`, calibration plan, rate profile, and stop conditions.
- [ ] Scanner-only output is never eligible for `finding` state.

## Collector Architecture

Collectors acquire data. They must not decide impact or create findings. Every
collector has the same lifecycle: prepare query, run source, preserve raw
output, parse records, normalize, classify, dedupe, emit metrics, and quarantine
bad records.

### Collector Interface

```python
class Collector:
    name: str
    mode: Literal["passive", "active_low", "authenticated"]
    required_secrets: list[str]
    output_types: list[str]

    def preflight(self, workspace: Path, config: CollectorConfig) -> PreflightResult: ...
    def collect(self, job: CollectorJob) -> RawEvidenceRef: ...
    def parse(self, evidence: RawEvidenceRef) -> Iterable[RawRecord]: ...
    def normalize(self, record: RawRecord) -> CanonicalObject: ...
```

### Collector Rules

- [ ] Passive collectors may query third-party APIs and public datasets but must
  not touch target infrastructure.
- [ ] Active collectors must call `PolicyEngine.authorize_action` per target.
- [ ] Collectors must record API quota usage and provider errors.
- [ ] Provider disagreement lowers confidence and adds review context; it does
  not discard either source.
- [ ] A collector outage marks data stale or unavailable; it does not imply an
  asset disappeared.
- [ ] API keys are optional unless the user enables that collector as required.
- [ ] Every collector emits `objects_collected`, `objects_normalized`,
  `objects_rejected`, `provider_errors`, and `quota_remaining` where available.

### Initial Collector Build Order

- [ ] `subfinder` passive subdomains.
- [ ] `amass` passive/intel subdomains.
- [ ] Certificate transparency and `crt.sh`.
- [ ] `SecurityTrails`, `VirusTotal`, `AlienVault OTX`, `urlscan.io`, and
  `Common Crawl`.
- [ ] `Shodan`, `Censys`, `FOFA`, and `Netlas` exposure providers.
- [ ] `GitHub` and `GitLab` public code search.
- [ ] Playwright/Katana browser and crawl collectors after active safety gates work.

## Tool Runner Architecture

Tool runners execute local binaries or scripted clients. They are separate from
collectors so the same safety wrapper, command logging, timeout handling, and
rate limiting are reused by `dnsx`, `httpx`, `katana`, `naabu`, `ffuf`,
Playwright, ZAP, and custom HTTP/WebSocket scripts.

### Runner Contract

```text
input:
  queue item, policy decision, command template, environment allowlist,
  rate profile, timeout, output paths, stop conditions

preflight:
  binary exists, version captured, policy allows action, rate profile exists,
  output path writable, secrets available by path/env only

execution:
  wrapper injects required headers/user-agent, limits concurrency, streams raw
  stdout/stderr, tracks request counters when possible, monitors stop triggers

output:
  job record, raw stdout/stderr paths, raw tool output path, parsed objects,
  metrics, rejection records, safety events
```

### Runner Checklist

- [ ] Use command allowlists; never execute arbitrary strings from config.
- [ ] Capture `tool --version` or equivalent at job start.
- [ ] Redact secret values from command logs while preserving secret source names.
- [ ] Write stdout, stderr, exit code, timeout, and resource usage.
- [ ] Abort on configured stop conditions and mark sibling jobs when necessary.
- [ ] Refuse redirect following to out-of-scope hosts unless the policy explicitly allows it.
- [ ] Keep raw output even when parsing fails.
- [ ] Do not convert runner findings directly into `finding` objects.

### Active Tool Profiles

```text
dnsx:
  allowed actions: dns_resolve, dns_active_bruteforce where policy allows
  required controls: wildcard detection, resolver record, private-range block

ProjectDiscovery httpx:
  allowed actions: http_head, http_get_root, headers, tech_detect, screenshot
  required controls: request wrapper, redirect classifier, baseline capture

Katana:
  allowed actions: crawl_low_rate, js_inventory, form_inventory
  required controls: scope-bound crawl, max depth, max duration, rate profile

Naabu:
  allowed actions: port_probe_low where explicitly allowed
  required controls: explicit port list/profile, low rate, in-scope host/IP

ffuf:
  allowed actions: profile-specific fuzz actions
  required controls: calibration, rate, stop conditions, payload class allowlist

Playwright:
  allowed actions: screenshot, HAR capture, owned-account workflow observation
  required controls: owned auth context for authenticated sessions, redaction

OWASP ZAP:
  allowed actions: passive scan and narrowly scoped active checks if permitted
  required controls: automation plan review, scope include/exclude, rate limits
```

## Fuzzing Implementation Plan

Fuzzing should be implemented after policy, baselines, endpoint inventory,
wordlists, and runner controls are working. The first version should support
only low-risk profiles and fixture-driven calibration. Add higher-risk profiles
only after the safety gates are proven.

### Fuzz Job Lifecycle

- [ ] Generate candidates from endpoints, JS routes, OpenAPI, GraphQL, mobile
  strings, docs, archives, and workflow maps.
- [ ] Attach one explicit profile to each candidate.
- [ ] Run `PolicyEngine.authorize_queue_item`.
- [ ] Build calibration requests for random path, known missing path, known
  valid path where available, unauth/auth baselines where applicable, WAF page,
  and auth redirect.
- [ ] Abort if calibration cannot identify baseline clusters.
- [ ] Run the low-rate fuzz job with request wrapper and stop monitor.
- [ ] Normalize ffuf/custom runner output into `fuzzing/results.jsonl`.
- [ ] Cluster responses by status, length, words, content type, body hash,
  redirect target, and auth state.
- [ ] Suppress baseline-equivalent, soft-404, wildcard, WAF, and auth-redirect hits.
- [ ] Emit `fuzzing/anomalies.jsonl` only for calibrated differences.
- [ ] Create leads only after a human-readable boundary hypothesis and next
  reproduction action are attached.

### Initial Profiles To Implement

- [ ] `subdomain_dns_low`
- [ ] `vhost_low`
- [ ] `web_paths_low`
- [ ] `api_paths_low`
- [ ] `query_params_low`
- [ ] `json_fields_low`
- [ ] `sspp_query_low`
- [ ] `content_types_low`
- [ ] `methods_readonly`
- [ ] `headers_medium_review`
- [ ] `graphql_endpoint_low`
- [ ] `graphql_suggestions_low`
- [ ] `graphql_introspection_review`
- [ ] `authz_diff_owned`
- [ ] `websocket_message_owned`
- [ ] `file_workflow_owned_review`
- [ ] `callback_fetcher_owned_review`

### Fuzz Stop Monitor

```text
inputs:
  live counters, response classifications, auth/session health, redirect
  classifications, account lock signals, WAF/block signatures, response sizes

actions:
  stop current job, stop sibling jobs for same host/workflow when needed,
  preserve raw evidence, write safety event, move queue item to blocked/review,
  update notes/recent-state.md
```

### Fuzz Acceptance Checklist

- [ ] Jobs without `in_scope` decision are blocked.
- [ ] Jobs without profile, calibration, rate limit, payload class, output path,
  and stop conditions are blocked.
- [ ] Jobs requiring authentication fail closed without owned-account context.
- [ ] Soft-404 fixtures produce zero anomalies.
- [ ] Real-hit fixtures produce deterministic anomalies.
- [ ] Out-of-scope redirects stop the job.
- [ ] Scanner-only fuzz output cannot become a finding.

## Evidence Storage Plan

Evidence is the audit trail for every object, queue item, lead, primitive, and
finding. It should be complete enough to reproduce decisions but minimized and
redacted enough to avoid storing unnecessary sensitive data.

### Evidence Directory Contract

```text
output/evidence/<phase>/<object-id>/
  request.txt
  response.txt
  response.headers.json
  response.body.hash
  screenshot.png
  har.redacted.har
  metadata.json
  decision.json
  redaction-log.jsonl
```

### Evidence Metadata

```json
{
  "schema_version": "1.0",
  "evidence_id": "ev:phase5:host-api-example-com:0001",
  "object_id": "host:api.example.com",
  "phase": "phase5_liveness",
  "collected_at": "2026-04-30T00:00:00Z",
  "collector_or_runner": "httpx_pd",
  "auth_context": "unauthenticated|owned_account_a|owned_account_b",
  "policy_decision_id": "decision:0001",
  "request_summary": {
    "method": "GET",
    "url_redacted": "https://api.example.com/",
    "headers_redacted": true
  },
  "paths": {
    "raw_request": "output/evidence/phase5/host-api-example-com/request.txt",
    "raw_response": "output/evidence/phase5/host-api-example-com/response.txt"
  },
  "redactions": ["Authorization", "Cookie", "Set-Cookie", "csrf"]
}
```

### Evidence Rules

- [ ] Keep raw evidence for reproducibility, but redact summaries by default.
- [ ] Store authenticated HARs with restricted permissions where possible.
- [ ] Store secret file paths and environment variable names, never secret values.
- [ ] Use owned-account data for screenshots and report evidence.
- [ ] Do not store unnecessary real-user data.
- [ ] Keep report-ready evidence packs separate from raw workspace evidence.
- [ ] Every lead, primitive, and finding must link back to evidence paths.

## Metrics And Quality Gates

Metrics are phase-level controls, not vanity counters. Every phase must emit a
quality record to `metrics/phase-quality.jsonl`, and every run must update
`metrics/recon-metrics.json`.

### Phase Quality Record

```json
{
  "schema_version": "1.0",
  "run_id": "20260430T000000Z",
  "phase": "phase5_liveness",
  "started_at": "2026-04-30T00:00:00Z",
  "finished_at": "2026-04-30T00:05:00Z",
  "inputs": 100,
  "raw_objects_collected": 100,
  "objects_normalized": 95,
  "objects_rejected": 5,
  "objects_promoted": 40,
  "blocked": 10,
  "accepted_gaps": 2,
  "quality_failures": [],
  "safety_events": [],
  "top_rejection_reasons": ["soft_404", "out_of_scope_redirect"]
}
```

### Global Metrics Checklist

- [ ] `raw_objects_collected`
- [ ] `objects_normalized`
- [ ] `objects_rejected`
- [ ] `unique_assets`
- [ ] `in_scope_assets`
- [ ] `unknown_assets`
- [ ] `blocked_assets`
- [ ] `live_baselines_completed`
- [ ] `js_files_analyzed`
- [ ] `endpoints_extracted`
- [ ] `api_endpoints_classified`
- [ ] `fuzz_jobs_queued`
- [ ] `fuzz_jobs_run`
- [ ] `fuzz_hits_after_calibration`
- [ ] `leads_created`
- [ ] `primitives_created`
- [ ] `findings_created`
- [ ] `accepted_gaps`
- [ ] `top_blocking_reasons`
- [ ] `top_noise_reasons`

### Quality Gates

- [ ] Raw evidence gate: no promotion without source, timestamp, and raw path.
- [ ] Schema gate: malformed records go to `output/rejected/`.
- [ ] Scope gate: active actions require `in_scope` plus explicit allowed action.
- [ ] Freshness gate: stale sources are historical or revalidated.
- [ ] Dedupe gate: duplicate values merge `source_refs` and evidence paths.
- [ ] Baseline gate: fuzz/anomaly claims require baseline comparison.
- [ ] Impact gate: leads require plausible boundary, data, state, or business impact.
- [ ] Reproduction gate: primitives require deterministic owned-account reproduction.
- [ ] Report gate: findings require exact repro, impact, evidence, scope proof,
  novelty check, and policy fit.
- [ ] Safety invariant gate: any invariant violation stops the run, quarantines
  affected output, and writes `notes/recent-state.md` plus `metrics/phase-quality.jsonl`.

## Acceptance Test Suite

Build test fixtures before connecting real tools.

Fixtures:

```text
fixtures/programs/exact-scope/
fixtures/programs/wildcard-with-exclusion/
fixtures/programs/third-party-cname/
fixtures/collectors/subfinder.jsonl
fixtures/collectors/httpx.jsonl
fixtures/collectors/ffuf-soft404.json
fixtures/collectors/ffuf-real-hits.json
fixtures/js/nextjs-bundle.js
fixtures/js/sourcemap-reference.js
fixtures/api/openapi.json
fixtures/graphql/introspection.json
fixtures/hars/owned-account-a.har
fixtures/hars/owned-account-b.har
```

Required tests:

```text
scope deny test
exclusion precedence test
third-party passive-only test
rate-limit missing test
required-header missing test
stale evidence test
wildcard DNS test
soft-404 calibration test
dedupe merge test
promotion gate test
owned-account authz-diff precondition test
report gate test
queue invalidation after scope change
secret redaction test
```

Definition of done for the implementation:

```text
all tests pass
coverage matrix generated
dry-run target completes phases 0-5 without active unsafe actions
ffuf calibration fixture suppresses soft-404 noise
lead scoring fixture produces deterministic ranked leads
scope-change fixture invalidates old active queues
```

## Resource Inventory

Use official documentation or repositories where possible. Recheck these URLs
before pinning versions in code.

### Core Recon Tools

```text
ProjectDiscovery Subfinder:
  purpose: passive subdomain enumeration
  docs: https://docs.projectdiscovery.io/opensource/subfinder/overview
  repo: https://github.com/projectdiscovery/subfinder

OWASP Amass:
  purpose: attack-surface intelligence, subdomains, OSINT mapping
  docs: https://owasp-amass.github.io/docs/
  project: https://owasp.org/www-project-amass/

ProjectDiscovery dnsx:
  purpose: DNS resolution, brute force where allowed, wildcard filtering
  docs: https://docs.projectdiscovery.io/opensource/dnsx/overview
  repo: https://github.com/projectdiscovery/dnsx

ProjectDiscovery httpx:
  purpose: HTTP liveness, headers, TLS, tech probes, JSONL output
  docs: https://docs.projectdiscovery.io/opensource/httpx/overview
  repo: https://github.com/projectdiscovery/httpx

ProjectDiscovery Katana:
  purpose: crawling, JS crawling/parsing, form extraction, JSON output
  docs: https://docs.projectdiscovery.io/opensource/katana/overview
  repo: https://github.com/projectdiscovery/katana

ProjectDiscovery Naabu:
  purpose: port discovery where policy allows
  docs: https://docs.projectdiscovery.io/opensource/naabu/overview
  repo: https://github.com/projectdiscovery/naabu

ffuf:
  purpose: web/API/VHost/path/parameter fuzzing
  repo: https://github.com/ffuf/ffuf
  wiki: https://github.com/ffuf/ffuf/wiki

OWASP ZAP Automation Framework:
  purpose: optional passive/controlled DAST automation and API-assisted analysis
  project: https://www.zaproxy.org/
  docs: https://www.zaproxy.org/docs/automate/automation-framework/
```

### Passive And Exposure Data Providers

```text
Shodan:
  purpose: internet-exposed service/banner/search data
  docs: https://book.shodan.io/developer-apis/shodan-api/

Censys:
  purpose: internet host, certificate, service, and historical context
  docs: https://docs.censys.com/
  legacy search API: https://docs.censys.com/docs/ls-api

FOFA:
  purpose: internet exposure search
  docs: https://fofa.so/api/

SecurityTrails:
  purpose: DNS, subdomains, historical DNS
  subdomain API: https://docs.securitytrails.com/reference/list-subdomains-old-1

urlscan.io:
  purpose: historical scans, page requests, screenshots, host/domain search
  docs: https://urlscan.io/docs/api/
  OpenAPI: https://docs.urlscan.io/apis/urlscan-openapi

Common Crawl:
  purpose: web archive URL and host discovery
  site: https://commoncrawl.org/
  index: https://index.commoncrawl.org/

VirusTotal API v3:
  purpose: domain/IP/URL relationship and reputation context
  docs: https://docs.virustotal.com/reference/overview
  domains: https://docs.virustotal.com/reference/domains-object

AlienVault OTX:
  purpose: passive DNS and threat-intel context
  API: https://otx.alienvault.com/api

Netlas:
  purpose: internet scan/exposure data, response search, DNS/WHOIS/cert context
  docs: https://docs.netlas.io/
  API: https://docs.netlas.io/automation/search_tools_api/
```

### Code, Package, And Registry Sources

```text
GitHub REST API:
  purpose: code search, repos, orgs, public references
  docs: https://docs.github.com/rest

GitHub GraphQL API:
  purpose: optional richer GitHub querying
  docs: https://docs.github.com/graphql

GitLab REST API:
  purpose: public project/group/code search when relevant
  docs: https://docs.gitlab.com/api/

npm Registry:
  purpose: package metadata and public SDK discovery
  docs: https://docs.npmjs.com/cli/v10/using-npm/registry

Docker Hub:
  purpose: public container image discovery
  docs: https://docs.docker.com/docker-hub/
```

### Browser, Traffic, API, And GraphQL Tools

```text
Playwright:
  purpose: screenshots, browser navigation, HAR capture, authenticated workflow
  docs: https://playwright.dev/docs/intro
  screenshots: https://playwright.dev/docs/screenshots

mitmproxy:
  purpose: traffic capture, replay, scripted HTTP/WebSocket processing
  docs: https://docs.mitmproxy.org/stable/
  addons: https://docs.mitmproxy.org/stable/addons/overview/

GraphQL Voyager:
  purpose: GraphQL schema visualization
  repo: https://github.com/graphql-kit/graphql-voyager

InQL:
  purpose: Burp extension for GraphQL schema/query analysis
  repo: https://github.com/doyensec/inql

GraphQL Cop:
  purpose: focused GraphQL security checks where policy allows
  repo: https://github.com/dolevf/graphql-cop
```

### Methodology References

```text
Massive Recon Framework Design:
  local: docs/massive-recon-framework.md

Local Web2 Bounty Operating Plan:
  local: docs/web2-bounty-agent-operating-plan.md

Local Bug Bounty Operator Guide:
  local: docs/bug-bounty-operator-guide.md

Local Operator Prompts:
  local: docs/operator-prompts.md

Local Hunter Profile:
  local: docs/hunter-profile-from-intigriti.md

OWASP WSTG Information Gathering:
  https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/

OWASP API Security Top 10 2023:
  https://owasp.org/API-Security/editions/2023/en/0x11-t10/

PortSwigger API Testing:
  https://portswigger.net/web-security/learning-paths/api-testing

PortSwigger GraphQL:
  https://portswigger.net/web-security/graphql

PortSwigger WebSockets:
  https://portswigger.net/web-security/websockets

Bugcrowd Vulnerability Rating Taxonomy:
  https://bugcrowd.com/vulnerability-rating-taxonomy/

Bugcrowd Recon and Discovery:
  https://www.bugcrowd.com/resources/levelup/recon-discovery/

HackerOne Quality Reports:
  https://docs.hackerone.com/en/articles/8475116-quality-reports

HackerOne Code of Conduct:
  https://www.hackerone.com/policies/code-of-conduct

Intigriti Triage Standards:
  https://kb.intigriti.com/en/articles/10335710-intigriti-triage-standards

Intigriti Report Writing:
  https://www.intigriti.com/researchers/blog/hacking-tools/writing-effective-bug-bounty-reports
```

## API Keys And Secret Files Needed

Optional providers should degrade gracefully when keys are missing.

```text
/home/hunterweb/secrets/recon/
  shodan_api_key
  censys_api_id
  censys_api_secret
  securitytrails_api_key
  virustotal_api_key
  urlscan_api_key
  fofa_api_key
  netlas_api_key
  github_token
  gitlab_token
```

Environment variable equivalents:

```text
SHODAN_API_KEY
CENSYS_API_ID
CENSYS_API_SECRET
SECURITYTRAILS_API_KEY
VIRUSTOTAL_API_KEY
URLSCAN_API_KEY
FOFA_API_KEY
NETLAS_API_KEY
GITHUB_TOKEN
GITLAB_TOKEN
```

Secrets policy:

```text
do not print secrets
do not store secrets in target notes
do not include secrets in raw command logs
store only secret file paths or env var names in config
redact auth headers and cookies from summaries
```

## Implementation Preflight Checklist

Before writing framework code, confirm the local environment and project inputs
are ready:

- [ ] `/home/hunterweb/docs/massive-recon-framework.md` is available and has
  been read for architecture and safety invariants.
- [ ] `/home/hunterweb/docs/web2-bounty-agent-operating-plan.md` is available
  for the notes -> leads -> primitives -> findings -> reports workflow.
- [ ] `/home/hunterweb/recon-framework/` exists or can be created.
- [ ] `/home/hunterweb/secrets/recon/` exists with restrictive permissions.
- [ ] Python 3.12+ is available.
- [ ] `pytest` can run an empty test suite.
- [ ] Tool binaries are treated as optional until their runner milestone starts.
- [ ] Missing provider API keys are handled as `provider_unavailable`, not as
  framework failures.
- [ ] No active target request can run until `program-kb`, `safe-actions.json`,
  and `rate-limits.json` validate.

## Build Order Summary

Recommended strict order:

```text
1. workspace generator
2. schemas and JSONL/SQLite storage
3. program-kb and policy engine
4. design acceptance tests
5. passive collectors
6. exposure collectors
7. DNS/liveness baselines
8. JS/URL/endpoint extraction
9. API/mobile/cloud mapping
10. wordlist generator
11. ffuf fuzz queue and runner
12. graph and lead scoring
13. diffing and continuous recon
14. promotion/reporting pipeline
15. integration docs and operator runbooks
```

Do not start with tool orchestration. Start with policy, schemas, storage,
evidence, and tests. Tool output is only useful after the framework can decide
what is in scope, what is safe, what is stale, what is duplicate, and what is
actionable.

## Implementation Definition Of Done

The build is effective enough to use on real authorized programs when:

```text
all design acceptance tests pass
all phase pipeline tests pass
program-kb can enforce exact, wildcard, exclusion, and third-party rules
unknown and out-of-scope assets cannot enter active queues
all collectors preserve raw evidence and normalize source_refs
all active runners require wrappers, rate limits, and allowed actions
ffuf jobs cannot run without calibration and stop conditions
soft-404 and wildcard DNS fixtures are suppressed
scope changes invalidate affected queues
lead scoring is deterministic and explainable
promotion gates prevent scanner-only findings
secrets are redacted from notes, reports, and summaries
coverage matrix can be generated for a dry-run target
handoff writes recent-state, metrics, blockers, accepted gaps, and next actions
```
