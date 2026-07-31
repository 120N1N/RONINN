# Massive Authorized Bug Bounty Recon Framework

Date: 2026-04-30

This document defines a wide-scope, deep-recon framework for authorized Web2 bug
bounty programs in `/home/hunterweb`. It is designed for maximum breadth and
depth while remaining bounded by explicit program authorization, policy rules,
rate limits, account limits, exclusions, and owned-account safety.

The framework is not a scanner-first system. It is a program-aware asset
intelligence and testing system. It stores the full program context, uses that
context to classify every discovered asset and endpoint, then runs passive
collection, enrichment, live baselining, fuzzing, workflow mapping, and lead
promotion only where the program knowledge base allows it.

## Operating Principle

Recon depth is unbounded. Authorization is not.

The system should be massive in data collection, recursive in enrichment, and
deep in analysis. It must still refuse to actively test assets, endpoints,
accounts, workflows, and payload classes that are unknown, out of scope,
third-party restricted, excluded, rate-limit unsafe, or not covered by owned
test accounts.

Every automated decision must be explainable and reversible:

```text
asset:
decision:
confidence:
policy_rules_used:
evidence_used:
allowed_actions:
blocked_actions:
review_reason:
```

## Design Invariants

These invariants define correctness for the framework. If any invariant is
violated, the run must stop, quarantine the affected output, and write a blocker
to `notes/recent-state.md` and `metrics/phase-quality.jsonl`.

### Authorization Invariants

```text
no active request without an in_scope decision
no active request without an allowed action from program-kb
no authenticated request without owned-account context
no fuzzing without explicit fuzz profile, baseline calibration, rate limit, and
  stop conditions
no state-changing action outside owned objects and policy-approved workflows
no third-party active testing unless explicitly included by the program
no credential, token, or secret validation against real services unless the
  program explicitly allows it
```

### Data Invariants

```text
no normalized object without raw evidence or source reference
no promoted object without scope_status and confidence
no lead without evidence path, boundary hypothesis, next action, and policy
  status
no primitive without reproducible owned-account control
no finding without exact repro, scope proof, demonstrated impact, and novelty
  check
no duplicate work item when dedupe_key and endpoint shape already exist
no stale evidence driving active testing without revalidation
```

### Safety Invariants

```text
rate limit must be configured before active probing
required headers and user-agent tags must be attached by wrapper
out-of-scope redirects must not be followed by active tooling
private, reserved, loopback, link-local, and metadata targets are blocked by
  default
high-volume scans, destructive actions, spam, billing effects, and availability
  testing are blocked unless policy and user approval explicitly allow them
```

### Quality Invariants

```text
every phase emits metrics
every blocker has a reason and reprocess condition
every accepted gap has owner, reason, date, and revisit trigger
every high-priority item has a concrete next action
every coverage row is covered, blocked, or accepted_gap
every source older than its freshness window is historical or revalidated
```

## Design Acceptance Tests

Before using the framework on a real target, run these dry-run checks against a
toy program-kb and a small synthetic dataset.

```text
scope deny test:
  unknown.example.com must remain passive_only and cannot enter active queues

exclusion precedence test:
  admin.example.com matching both wildcard scope and explicit exclusion must be
  blocked

third-party test:
  help.example.com with vendor CNAME must become needs_review or passive_only
  unless third-party testing is explicitly included

rate-limit test:
  any active job without rate profile must be blocked

header test:
  any active job without required program headers must be blocked

stale evidence test:
  archive-only URL older than freshness window must not become fuzz_queued
  without live confirmation

wildcard DNS test:
  random labels resolving to same response cluster must be filtered from
  subdomain results

soft-404 test:
  random paths with same status/body cluster as fuzz hits must suppress those
  hits

dedupe test:
  duplicate endpoints from JS, archive, and crawler must merge source_refs into
  one endpoint object

promotion test:
  a scanner signature without reproduction must stay notes/candidate and cannot
  become finding

owned-account test:
  authz_diff jobs require account A and account B object ownership metadata

report gate test:
  a finding missing impact, scope proof, or reproducible steps must fail
  promotion
```

Passing these tests is the minimum design check for a new implementation or
major framework change.

## Target Architecture

```text
program ingestion
  -> program knowledge base
  -> seed expansion
  -> passive collectors
  -> exposure collectors
  -> DNS and host normalization
  -> scope and policy classifier
  -> safe active discovery queue
  -> live baseline probes
  -> URL, JS, API, mobile, and cloud extraction
  -> fuzz candidate queue
  -> policy-gated fuzz runners
  -> evidence store
  -> attack-surface graph
  -> lead scoring
  -> primitives and chain construction
  -> findings and reports
  -> continuous monitoring and diffs
```

The methodology workspace is the control plane. Tool orchestration is the data
plane.

## External Benchmark

The framework is benchmarked against these trusted public sources and should be
rechecked when any source changes materially:

```text
OWASP WSTG information gathering:
  search discovery, fingerprinting, webserver metafiles, attack surface
  identification, page-content review, entry-point identification, execution
  path mapping, framework fingerprinting, application fingerprinting, and
  architecture mapping

OWASP API Security Top 10 2023:
  BOLA, broken auth, object property authorization, resource consumption,
  function-level authorization, sensitive business flows, SSRF, security
  misconfiguration, improper inventory management, and unsafe third-party API
  consumption

HackerOne platform guidance:
  asset discovery should inventory subdomains, endpoints, ports, technologies,
  and timestamps; automated or AI-assisted testing must respect scope, policy,
  request volume, and rate limits; reports need clear repro and impact

Bugcrowd guidance and VRT:
  recon should combine multiple subdomain techniques; priority depends on
  objective vulnerability type, exploitability, and impact, not raw tool output

Intigriti methodology and triage guidance:
  wide-scope programs require mapping subsidiaries and subdomains; product docs,
  changelogs, JavaScript, non-standard HTTP ports, notes, scope proof, working
  PoCs, and clear impact materially affect validity and payout

PortSwigger Web Security Academy:
  API testing should include docs discovery, hidden endpoints, supported
  methods, content types, hidden parameters, mass assignment, and server-side
  parameter pollution; GraphQL testing should include endpoint discovery,
  schema/introspection/suggestions behavior, and authorization; WebSocket
  testing should treat message and handshake traffic as first-class attack
  surface

ProjectDiscovery tooling:
  subfinder provides multi-source passive subdomain enumeration; katana supports
  scoped crawling, JavaScript crawling, form extraction, technology detection,
  and JSON output; nuclei-style template checks are useful only when scoped,
  rate-limited, and triaged for real impact
```

### Benchmark Gap Rules

When the framework is reviewed against external sources, gaps must be patched
into the document and target templates as concrete controls, not as vague
reminders. Each gap should produce one or more of:

```text
new program-kb field
new collector
new schema field
new coverage-matrix row
new fuzz profile
new lead-scoring signal
new completion gate
new safety gate
```

## High-Signal Design Requirements

Massive recon is only useful when the output is relevant, explainable, and
ranked. The system must suppress low-confidence noise and highlight attackable
boundary crossings.

### High-Signal Data Rules

```text
preserve provenance for every result
separate passive evidence from active evidence
require scope classification before active testing
prefer target-specific wordlists over generic volume
deduplicate by normalized host, canonical URL, content hash, and endpoint shape
calibrate soft-404, wildcard DNS, CDN default pages, and auth redirects
require baseline comparison before calling a fuzz result interesting
promote route-existence signals only when status, content type, body shape, or
  auth behavior differs from baseline
score business-critical, authz, tenant, role, file, callback, billing, and admin
  surfaces above static marketing assets
record why a result is actionable, blocked, duplicate, stale, or low confidence
```

### Noise Suppression Gates

```text
drop or downscore parked domains
drop or downscore vendor default pages unless explicitly in scope
drop archive-only URLs with no live confirmation
drop hosts with only stale certificate evidence unless another source confirms
downscore hosts with no business, auth, API, file, callback, or admin surface
downscore path fuzz hits that match soft-404 fingerprints
downscore scanner signatures without reproduction and impact
merge duplicate endpoints with the same path shape and response behavior
tag findings from version banners as informational until exploitability is
  reproduced in scope
```

### High-Signal Output Objects

The main output of recon is not a giant host list. It is a ranked set of
actionable objects:

```text
confirmed in-scope assets with live evidence
candidate high-value apps and APIs
hidden or legacy endpoints with route-existence evidence
role/tenant boundary maps
owned-object request pairs for authorization testing
file, import, export, webhook, and callback workflows
GraphQL and WebSocket operation inventories
technology/version risks with exploitability notes
policy-safe fuzz queues
reproducible anomalies promoted to leads
```

## Data Pipeline Contract

Every recon phase must follow the same data pipeline contract so results are
high quality, replayable, explainable, and useful for later hunting.

### Pipeline Stages

```text
ingest:
  collect raw data from policy, platform API, official docs, passive sources,
  exposure providers, live baselines, tools, browser traffic, or owned-account
  workflows

preserve:
  store raw evidence before normalization, including command/API query, source,
  timestamp, auth context, scope decision at collection time, and raw output path

normalize:
  convert data into canonical JSONL objects with stable identifiers,
  normalized hostnames, canonical URLs, endpoint shapes, hashes, and source refs

classify:
  apply program-kb scope rules, confidence model, ownership evidence,
  third-party rules, and testability policy

enrich:
  add DNS, TLS, HTTP, tech, business, role, tenant, API, JS, cloud, mobile,
  and historical context where policy allows

dedupe:
  merge exact and semantic duplicates while preserving all sources and evidence

score:
  rank by confidence, freshness, business relevance, security-boundary
  relevance, exploitability likelihood, and policy safety

gate:
  decide one of: promote, queue_for_safe_probe, passive_only, blocked,
  needs_review, accepted_gap

emit:
  write normalized objects, summaries, coverage updates, lead candidates,
  fuzz queues, and recent-state updates

diff:
  compare with previous run and highlight newly added, removed, changed,
  newly in-scope, newly blocked, and newly high-risk objects
```

### Required Metadata On Every Object

```text
id:
type:
value:
normalized_value:
source_refs:
raw_evidence_paths:
retrieved_at:
first_seen:
last_seen:
freshness:
scope_status:
testability:
confidence:
owner_evidence:
third_party_status:
business_relevance:
security_boundary_relevance:
risk_score:
noise_score:
dedupe_key:
state:
next_action:
blocking_reason:
```

### Canonical States

```text
raw:
  collected but not normalized

normalized:
  parsed into canonical schema

classified:
  scope and testability decision assigned

enriched:
  additional context attached

candidate:
  potentially useful, not yet actionable

safe_probe_queued:
  eligible for allowed low-impact probing

fuzz_queued:
  eligible for a specific policy-approved fuzz profile

lead:
  interesting anomaly or high-value surface requiring reproduction

primitive:
  reproducible attacker-controlled behavior

finding:
  six-gate security issue with demonstrated impact

blocked:
  prohibited, out of scope, unknown, stale, unsafe, duplicate, or too noisy

accepted_gap:
  known missing coverage with documented reason
```

### Quality Dimensions

Every pipeline output must be measurable on these dimensions:

```text
validity:
  can the data be parsed, normalized, and traced to raw evidence?

scope confidence:
  does the program-kb justify the current action?

freshness:
  is the evidence current enough for the phase?

uniqueness:
  is this a new object, a duplicate, or a changed object?

actionability:
  does it suggest a concrete next step?

impact relevance:
  does it touch auth, tenant, role, data, money, files, callbacks, admin,
  support, identity, or business-critical workflows?

noise:
  does it match wildcard DNS, soft-404, CDN default, parked domain, stale
  archive, scanner-only, or vendor-default patterns?

safety:
  can the next action run without violating policy, scope, account, or rate
  constraints?
```

### Data Quality Gates

```text
raw evidence gate:
  no object can be promoted without source, timestamp, and raw evidence path

schema gate:
  malformed objects are quarantined under output/normalized/rejected/

scope gate:
  active actions require in_scope plus explicit allowed action

freshness gate:
  stale sources are downscored or revalidated before driving active testing

dedupe gate:
  duplicate values merge source_refs instead of creating duplicate work

baseline gate:
  fuzz and anomaly claims require baseline comparison

impact gate:
  leads require a plausible boundary, data, state, or business impact

reproduction gate:
  primitives require deterministic owned-account reproduction

report gate:
  findings require exact repro, impact, evidence, scope proof, and novelty check
```

### Artifact Naming

Use predictable file names so every phase can be rerun and audited:

```text
output/raw/<phase>/<collector>/<timestamp>.<ext>
output/normalized/<phase>/<object-type>.jsonl
output/evidence/<phase>/<object-id>/
output/rejected/<phase>/<reason>.jsonl
coverage/<framework-area>.md
notes/recent-state.md
```

### Pipeline Metrics

Every campaign should maintain a small metrics file:

```text
metrics/recon-metrics.json
```

Track:

```text
raw_objects_collected
objects_normalized
objects_rejected
unique_assets
in_scope_assets
unknown_assets
blocked_assets
live_baselines_completed
js_files_analyzed
endpoints_extracted
api_endpoints_classified
fuzz_jobs_queued
fuzz_jobs_run
fuzz_hits_after_calibration
leads_created
primitives_created
findings_created
accepted_gaps
top_blocking_reasons
top_noise_reasons
```

High-quality recon should trend toward fewer duplicate/noisy objects and more
classified, actionable, evidence-backed objects over time.

### Rejection And Quarantine Pipeline

Rejected data is still useful for auditability and tuning. Do not silently drop
collector output.

```text
rejection reasons:
  malformed
  unsupported_encoding
  missing_source
  missing_timestamp
  duplicate_exact
  duplicate_semantic
  wildcard_dns
  soft_404
  parked_domain
  vendor_default
  stale_only
  out_of_scope
  unknown_scope
  third_party_blocked
  policy_blocked
  rate_limit_blocked
  unsafe_action
  no_impact_path
```

For each rejection, store:

```text
object_ref:
phase:
collector:
reason:
evidence_path:
timestamp:
can_be_reprocessed:
reprocess_condition:
```

### Feedback Loops

Each phase should feed later phases and improve earlier phases:

```text
live baselines -> soft-404 and auth-redirect fingerprints for fuzz calibration
JS routes -> endpoint inventory and target-specific wordlists
API schemas -> hidden field and mass-assignment dictionaries
mobile strings -> passive host searches and API inventories
fuzz anomalies -> lead scoring and new baseline fingerprints
role diffs -> workflow maps and authz test sets
reports/primitives -> scoring model and future priority rules
blocked decisions -> program-kb missing-info and scope questions
continuous diffs -> stale data expiration and new priority queues
```

### Minimum Effective Data Product Per Phase

Every phase must produce at least one of these durable outputs before it is
considered effective:

```text
new normalized objects
updated scope/testability decisions
updated coverage row
new or improved baselines
new target-specific wordlist terms
new fuzz candidates
new leads
new accepted gaps
new blocking questions
new evidence-backed priority changes
```

### Object Identity And Dedupe Rules

Stable identities prevent duplicate work and make diffs meaningful.

```text
domain_id:
  lower(root_domain)

host_id:
  lower(fqdn_without_trailing_dot)

service_id:
  host_id + ":" + port + "/" + protocol

url_id:
  scheme + host + normalized_port + normalized_path + sorted_query_key_names

endpoint_id:
  method + api_base + path_template + content_type_family

js_id:
  script_url canonicalized plus content_hash

workflow_id:
  product + role + workflow_name + object_type

object_id:
  object_type + tenant_id + owner_account_id + stable_identifier

lead_id:
  boundary_type + affected_asset + normalized_behavior + first_evidence_hash
```

Deduplication must preserve:

```text
all source_refs
all first_seen and last_seen timestamps
highest confidence and latest freshness
all raw evidence paths
all distinct auth states and role observations
```

### Freshness Windows

Use freshness windows to avoid stale recon driving active testing.

```text
program policy:
  recheck every session

scope rules:
  recheck every session

DNS and CT:
  fresh for 7 days during active hunt

exposure providers:
  fresh for 7-14 days depending on provider last_seen

live HTTP baseline:
  fresh for 72 hours during active testing

JavaScript bundles:
  fresh until content hash changes, otherwise recheck weekly

API docs and product docs:
  fresh for 14 days or until changelog indicates related changes

mobile and extension metadata:
  fresh until version changes, otherwise recheck weekly

owned-account workflow observations:
  fresh for 72 hours or until role/account/config changes

fuzz calibration:
  valid only for the specific run, host, auth state, and response baseline
```

Expired evidence can remain useful as historical context, but it cannot by
itself authorize active testing, fuzzing, or finding promotion.

### Priority Queue Semantics

Queues must be deterministic and auditable.

```text
safe_probe_queue:
  in-scope assets eligible for allowed low-impact baseline probes

crawl_queue:
  in-scope apps with scope-bound crawl settings and rate profile

api_inventory_queue:
  API bases/endpoints needing method, schema, auth, and role mapping

fuzz_queue:
  endpoints with selected profile, calibration plan, auth context, rate limit,
  stop conditions, and allowed payload class

lead_queue:
  anomalies with evidence, boundary hypothesis, impact hypothesis, and next
  reproduction step

review_queue:
  conflicting or ambiguous items needing scope/policy clarification

blocked_queue:
  prohibited or unsafe items with reprocess condition
```

Each queue item must include:

```text
item_id:
source_object_ids:
reason:
required_preconditions:
allowed_actions:
blocked_actions:
rate_profile:
auth_context:
expected_output:
stop_conditions:
created_at:
expires_at:
owner:
```

## Required Workspace Layout

For a concrete target, create or extend:

```text
/home/hunterweb/bounty/<program>/<target>/
  program-kb/
    program.json
    policy.md
    scope.json
    rules.json
    source-benchmark.json
    assets.jsonl
    organizations.json
    brands.json
    subsidiaries.json
    third-parties.json
    accounts.json
    rate-limits.json
    exclusions.json
    safe-actions.json
    decision-log.jsonl
    confidence-model.json
  config/
    target.env
    target.env.example
    collectors.yml
    fuzz-profiles.yml
    scope-rules.yml
  notes/
    rules.md
    recon.md
    recent-state.md
    live-probing.md
    traffic-map.md
    missing-info.md
    execution-checklist.md
    loop/
      queue.md
      log.md
  sources/
    program.md
    official-docs.md
    product.md
    changelog.md
    app-stores.md
    code-registries.md
    search-indexes.md
  assets/
    roots.jsonl
    domains.jsonl
    subdomains.jsonl
    hosts.jsonl
    ips.jsonl
    services.jsonl
    urls.jsonl
    endpoints.jsonl
    js.jsonl
    mobile.jsonl
    cloud.jsonl
    third-party.jsonl
  surfaces/
    web.md
    api.md
    graphql.md
    websocket.md
    mobile.md
    auth.md
    sso.md
    files.md
    webhooks.md
    billing.md
    admin.md
    support.md
    integrations.md
  fuzzing/
    queue.jsonl
    jobs.jsonl
    results.jsonl
    anomalies.jsonl
  queues/
    safe-probe.jsonl
    crawl.jsonl
    api-inventory.jsonl
    fuzz.jsonl
    leads.jsonl
    review.jsonl
    blocked.jsonl
  graph/
    assets.graph.json
    attack-surface.graph.json
  leads/
  primitives/
  findings/
  reports/
  output/
    raw/
    normalized/
    evidence/
    screenshots/
    har/
    js/
    ffuf/
    http/
    dns/
    tls/
  metrics/
    recon-metrics.json
    phase-quality.jsonl
  runbooks/
    start-session.md
    scope-change.md
    active-probing.md
    fuzzing.md
    incident-stop.md
    handoff.md
  coverage/
    wstg.md
    api-top-10.md
    portswigger-api.md
    platform-rules.md
```

## Phase Pipeline Matrix

Each phase must update `metrics/phase-quality.jsonl` with counts, rejected
objects, quality failures, and promoted outputs.

### Phase 0 Pipeline: Program Knowledge Base

```text
inputs:
  program policy, platform API output, scope text, user-supplied rules, account
  rules, required headers, rate limits, exclusions

process:
  parse rules, extract assets, encode scope matchers, encode action rules,
  encode exclusions, define confidence model, define safe-action matrix

outputs:
  program-kb/program.json, scope.json, rules.json, exclusions.json,
  safe-actions.json, rate-limits.json, confidence-model.json

quality gates:
  policy source timestamped; in-scope and out-of-scope rules present; active
  actions mapped to allowed/blocked states; missing rules written to
  notes/missing-info.md

promotion:
  only emit active collector queues when scope and rate rules are enforceable
```

### Phase 1 Pipeline: Seed Expansion

```text
inputs:
  program-kb, official sources, docs, product pages, app listings, org names,
  brands, subsidiaries, platform asset exports

process:
  extract root domains, brand terms, product terms, docs links, API docs,
  app identifiers, repo/package names, business workflows

outputs:
  sources/*.md, assets/roots.jsonl, program-kb/brands.json,
  program-kb/subsidiaries.json, target-specific seed wordlists

quality gates:
  every seed has source_url, retrieved_at, confidence, and scope relevance;
  historical brand terms marked as historical; unknown seeds passive-only

promotion:
  official roots and explicit program assets feed passive collectors; derived
  terms feed wordlist generation with lower confidence
```

### Phase 2 Pipeline: Passive Asset Intelligence

```text
inputs:
  roots, brands, terms, API keys, passive source configs

process:
  run passive subdomain, DNS, URL, archive, code-reference, and search-index
  collectors; preserve raw source output; normalize values

outputs:
  assets/subdomains.jsonl, assets/domains.jsonl, assets/urls.jsonl,
  assets/endpoints.jsonl candidates, output/raw/passive/

quality gates:
  source_refs preserved; stale/historical records flagged; duplicate hostnames
  merged; wildcard and parked candidates downscored; no active requests to
  target infrastructure in passive-only mode

promotion:
  high-confidence in-scope candidates go to DNS/liveness queues; weak or
  single-source candidates stay passive-only
```

### Phase 3 Pipeline: Internet Exposure Mapping

```text
inputs:
  roots, host candidates, org/brand names, ASN/netblock hints, cert terms,
  favicon hashes, titles, provider API keys

process:
  query exposure providers, normalize host/IP/service/banner/TLS data, attach
  provider timestamps and raw evidence, classify ownership confidence

outputs:
  assets/ips.jsonl, assets/services.jsonl, output/raw/exposure/,
  exposure-derived host candidates

quality gates:
  provider last_seen recorded; IP ownership not assumed from banner alone;
  private/reserved ranges blocked; old exposure hits downscored unless
  confirmed by another source

promotion:
  recent in-scope web services go to live baseline; ambiguous IPs remain
  passive-only or needs_review
```

### Phase 4 Pipeline: DNS, Subdomain, And VHost Discovery

```text
inputs:
  passive host candidates, roots, wordlists, resolver config, scope rules,
  active discovery permission

process:
  resolve DNS, detect wildcard behavior, normalize CNAME chains, run active
  subdomain/vhost fuzzing only where allowed, classify host ownership

outputs:
  assets/subdomains.jsonl updated, assets/hosts.jsonl, assets/third-party.jsonl,
  output/raw/dns/, output/normalized/dns/

quality gates:
  wildcard DNS filtered; resolver and TTL recorded; CNAME third-party status
  classified; vhost fuzzing only against allowed hosts/IPs

promotion:
  resolving, in-scope, non-noisy hosts move to liveness; dangling dependencies
  become takeover leads only with scope proof and policy fit
```

### Phase 5 Pipeline: Liveness And Web Surface Classification

```text
inputs:
  in-scope hosts, request wrapper config, rate limits, headers, account states

process:
  perform low-impact root and baseline probes, capture redirects, TLS, headers,
  cookies, CSP, CORS, screenshots, robots/sitemap/security.txt, soft-404 and
  auth-redirect fingerprints

outputs:
  notes/live-probing.md, assets/services.jsonl, assets/urls.jsonl,
  output/evidence/http/, output/screenshots/

quality gates:
  wrapper used; scope decision logged; baseline paths captured; out-of-scope
  redirects blocked or labeled; soft-404 and WAF pages fingerprinted

promotion:
  apps, APIs, admin/support/auth surfaces, unusual errors, and sensitive
  headers move to surface mapping or leads
```

### Phase 6 Pipeline: JavaScript Discovery And Mining

```text
inputs:
  live pages, archived pages, script URLs, HAR files, source maps, mobile and
  extension JS assets

process:
  download allowed scripts, hash content, parse routes, API hosts, GraphQL
  operations, WebSockets, feature flags, source-map references, storage URLs,
  and secret candidates

outputs:
  assets/js.jsonl, assets/endpoints.jsonl candidates, target-specific
  wordlists, output/js/

quality gates:
  script host classified; third-party scripts separated; duplicate script
  hashes merged; secret candidates not validated against services; source-map
  access follows policy

promotion:
  in-scope API hosts/endpoints feed endpoint inventory; hidden routes and
  sensitive strings feed leads or wordlists
```

### Phase 7 Pipeline: URL, Endpoint, And Parameter Inventory

```text
inputs:
  live crawl URLs, archives, JS extraction, API docs, OpenAPI, Postman,
  GraphQL schemas, mobile strings, code references

process:
  canonicalize URLs, infer endpoint templates, extract params, methods,
  content types, auth hints, object IDs, tenant IDs, and state-changing actions

outputs:
  assets/urls.jsonl, assets/endpoints.jsonl, parameter dictionaries,
  endpoint coverage maps

quality gates:
  archive-only URLs flagged; soft-404 endpoints filtered; endpoint shapes
  deduped; auth/state hints labeled as inferred unless observed live

promotion:
  authenticated, object-bearing, state-changing, hidden, legacy, and API routes
  move to API/workflow mapping and fuzz candidate generation
```

### Phase 8 Pipeline: API, GraphQL, WebSocket, And Realtime Surfaces

```text
inputs:
  endpoints, docs, schemas, owned-account traffic, HAR, WebSocket messages,
  GraphQL operations

process:
  map methods, content types, schemas, roles, tenants, object IDs, field-level
  behavior, GraphQL suggestions/introspection, WebSocket handshakes/messages

outputs:
  surfaces/api.md, surfaces/graphql.md, surfaces/websocket.md,
  assets/endpoints.jsonl enriched, authz-diff request sets

quality gates:
  no state-changing tests without owned objects and policy permission; schema
  claims backed by evidence; WebSocket messages tied to auth/role context

promotion:
  object/role/tenant boundaries, hidden params, mass-assignment candidates,
  GraphQL authz candidates, and WebSocket subscription/action candidates become
  high-priority leads or fuzz jobs
```

### Phase 9 Pipeline: Mobile, Desktop, And Browser Extension Recon

```text
inputs:
  app store metadata, package files where legal, extension manifests, desktop
  update manifests, CLI packages, deep link metadata

process:
  extract hosts, endpoints, schemes, app links, permissions, message handlers,
  update URLs, telemetry endpoints, GraphQL operations, and mobile-only routes

outputs:
  assets/mobile.jsonl, assets/endpoints.jsonl candidates,
  surfaces/mobile.md, surfaces/integrations.md

quality gates:
  artifact source legality recorded; secrets not validated; mobile-only hosts
  pass scope classifier before active probing

promotion:
  mobile-only APIs, deep links, extension message handlers, and update channels
  move to API/auth/workflow mapping
```

### Phase 10 Pipeline: Code, Package, And Container Registry Recon

```text
inputs:
  public repos, package registries, SDKs, CLIs, containers, docs examples

process:
  extract endpoints, env var names, object models, deprecated APIs, webhook
  names, OAuth scopes, bucket patterns, and target-specific terms

outputs:
  sources/code-registries.md, assets/endpoints.jsonl candidates,
  wordlists/*, output/raw/code/

quality gates:
  public source only; secrets not used; old code marked historical; package
  ownership confidence recorded

promotion:
  live-confirmable endpoints and high-value terms feed endpoint inventory,
  wordlists, and passive checks
```

### Phase 11 Pipeline: Cloud, CDN, Storage, And Origin Mapping

```text
inputs:
  DNS/CNAME chains, JS/cloud URLs, docs, exports/download links, exposure data,
  storage naming patterns

process:
  classify cloud provider, CDN, storage, signed URL, origin, cache behavior,
  upload/download/export/preview relationships

outputs:
  assets/cloud.jsonl, surfaces/files.md, graph cloud/storage edges,
  file-workflow test candidates

quality gates:
  active storage permission checks require scope permission; cloud URLs tied to
  source evidence; third-party storage separated; signed URL tests use owned
  objects only

promotion:
  upload, preview, import, export, signed URL, origin leak, and cache-boundary
  candidates move to workflow mapping or leads
```

### Phase 12 Pipeline: Auth, Identity, SSO, And Session Mapping

```text
inputs:
  auth pages, owned accounts, cookies/tokens, OIDC/SAML metadata, session
  traffic, invite/reset/email/MFA flows

process:
  map identity provider, token storage, cookies, CSRF, redirects, roles, tenant
  switching, invite/reset lifecycle, session invalidation, SSO/SCIM surfaces

outputs:
  surfaces/auth.md, surfaces/sso.md, role/tenant matrices, auth state baselines

quality gates:
  only owned accounts; no takeover beyond proof; no password attacks; token
  material stored outside notes; state-changing flows clearly allowed

promotion:
  session, role, tenant, invite, reset, OAuth/OIDC/SAML, MFA, and SCIM anomalies
  move to leads with exact account context
```

### Phase 13 Pipeline: Business Workflow And Trust Boundary Mapping

```text
inputs:
  product docs, live traffic, owned accounts, endpoint maps, role matrices,
  billing/file/webhook/integration/admin/support surfaces

process:
  model workflows as state machines, map allowed roles/states, identify trust
  boundaries, compare expected vs observed access and side effects

outputs:
  surfaces/*.md, notes/traffic-map.md, graph workflow edges, lead candidates

quality gates:
  expected behavior sourced from docs or observed normal flow; side effects
  confined to owned accounts; blocked workflows documented

promotion:
  cross-role, cross-tenant, feature-gate, billing, invite, export, import,
  webhook, admin/support, race, and cache anomalies become leads
```

### Phase 14 Pipeline: Fuzzing Framework

```text
inputs:
  scoped targets, endpoint inventory, baselines, target-specific wordlists,
  owned-account requests, safe fuzz profiles, rate limits

process:
  calibrate baselines, select profile, run ffuf or specialized runner, normalize
  results, cluster responses, remove soft-404/noise, compare auth states

outputs:
  fuzzing/jobs.jsonl, fuzzing/results.jsonl, fuzzing/anomalies.jsonl,
  output/ffuf/, lead candidates

quality gates:
  fuzz gate passed; calibration complete; stop conditions configured; result
  survives baseline comparison; no out-of-scope redirects followed

promotion:
  route-existence, parser reachability, auth differences, hidden params,
  content-type differences, and object/tenant anomalies become leads
```

### Phase 15 Pipeline: Target-Specific Wordlist Generation

```text
inputs:
  seeds, docs, JS, schemas, mobile strings, code refs, product terms, historic
  endpoints, object models

process:
  tokenize, normalize, rank, split by use case, remove dangerous/noisy terms,
  attach provenance and freshness

outputs:
  wordlists/subdomains.txt, paths.txt, api-paths.txt, params.txt,
  json-fields.txt, graphql-fields.txt, cloud-names.txt

quality gates:
  every generated term has source_refs; sensitive terms reviewed; generic lists
  separated from target-specific lists; stale-only terms downscored

promotion:
  high-confidence target terms feed fuzz profiles and passive searches
```

### Phase 16 Pipeline: Attack Surface Graph

```text
inputs:
  all normalized assets, endpoints, roles, tenants, workflows, cloud, JS,
  mobile, code, and evidence refs

process:
  create graph nodes and edges, merge duplicates, attach confidence, scope,
  freshness, business relevance, and evidence

outputs:
  graph/assets.graph.json, graph/attack-surface.graph.json, graph deltas

quality gates:
  edges require evidence; inferred edges labeled; stale edges downscored;
  unknown-scope nodes cannot unlock active actions

promotion:
  graph paths that cross trust boundaries or reveal untested high-value surfaces
  feed lead scoring and coverage gaps
```

### Phase 17 Pipeline: Lead Scoring

```text
inputs:
  graph, anomalies, fuzz results, baselines, workflow maps, business context,
  policy rules

process:
  compute impact, exploitability, confidence, freshness, novelty, and safety
  scores; explain positive and negative factors

outputs:
  leads/*.md candidates, notes/loop/queue.md updates, priority-testing-plan.md

quality gates:
  no lead without evidence path, next action, boundary hypothesis, and policy
  status; scanner-only hits stay notes until reproduced

promotion:
  high-scoring, policy-safe leads move to primitive reproduction tasks
```

### Phase 18 Pipeline: Evidence Promotion

```text
inputs:
  leads, owned-account tests, raw requests/responses, screenshots, callback
  evidence, state-change evidence, novelty checks

process:
  reproduce, control, explain mechanism, escalate safely, prove impact, check
  duplicates and policy fit

outputs:
  primitives/*.md, findings/*.md, reports/*.md

quality gates:
  six-step finding gate; exact repro; minimal data; owned accounts; impact
  evidence; no theoretical or scanner-only claims

promotion:
  report-ready findings only after proofreading by following the steps
```

### Phase 19 Pipeline: Continuous Recon And Diffing

```text
inputs:
  previous normalized state, current collectors, policy updates, source updates,
  JS hashes, DNS, exposure, URLs, schemas, mobile versions

process:
  rerun scheduled collectors, normalize, compare, classify changes, update
  freshness, reopen coverage gaps, reprioritize leads

outputs:
  output/normalized/diff/, notes/recent-state.md, metrics/recon-metrics.json,
  new queues and changed-priority leads

quality gates:
  diffs separate added/removed/changed; policy changes trigger reclassification;
  stale data expires or is marked historical

promotion:
  newly in-scope, newly exposed, newly changed, or newly high-value surfaces
  become priority testing items
```

### Phase 20 Pipeline: Completion And Handoff

```text
inputs:
  coverage matrix, metrics, unresolved unknowns, leads, primitives, findings,
  recent-state

process:
  check completion criteria, summarize blockers, accepted gaps, high-value next
  actions, evidence locations, and residual risk

outputs:
  notes/recent-state.md, coverage/*.md, priority-testing-plan.md,
  campaign summary

quality gates:
  no uncategorized unknowns; every phase has metrics; every blocker has reason;
  every high-priority item has next action or accepted-gap status

promotion:
  engagement is ready for hunting, rerun, or report finalization
```

## Operational Runbooks

The framework should generate these runbooks in every target workspace and keep
them current as program rules change.

### Start-Session Runbook

```text
1. recheck program policy and scope
2. update program-kb timestamps
3. verify required headers, user-agent, and rate limits
4. verify owned accounts and auth material paths
5. review notes/recent-state.md
6. review open blockers, accepted gaps, and high-priority queues
7. run passive refresh before active probing
8. regenerate active queues from current program-kb
9. refuse active tooling if scope or rate rules are stale
```

### Scope-Change Runbook

```text
1. write raw policy evidence to output/raw/program/
2. update program-kb/scope.json and exclusions.json
3. reclassify all assets, endpoints, queues, leads, and primitives
4. move newly out-of-scope items to blocked_queue
5. move newly in-scope items to passive enrichment before active probing
6. invalidate active queues created under old rules
7. update coverage and recent-state
8. record the diff in decision-log.jsonl
```

### Active-Probing Runbook

```text
1. select queue item
2. verify scope_status == in_scope
3. verify allowed action and rate profile
4. verify wrapper adds headers and user-agent
5. verify no out-of-scope redirect following
6. execute lowest-impact request first
7. store raw request/response metadata and evidence
8. update baseline fingerprints
9. stop immediately on safety trigger
```

### Fuzzing Runbook

```text
1. select fuzz_queue item
2. verify selected fuzz profile and payload class
3. verify baseline calibration inputs
4. verify auth context uses owned accounts when required
5. run calibration requests
6. abort if calibration cannot distinguish soft-404/auth-redirect/WAF behavior
7. run low-rate fuzz job
8. cluster and normalize results
9. suppress baseline-equivalent hits
10. create leads only for calibrated, explainable anomalies
```

### Incident-Stop Runbook

Run this if a tool hits a safety trigger, an asset becomes out of scope, account
lockout appears, unexpected real-user data appears, or availability impact is
suspected.

```text
1. stop the job
2. stop sibling jobs targeting the same host/workflow
3. preserve raw logs and timestamps
4. mark affected queue items blocked pending review
5. write notes/recent-state.md with exact trigger and scope
6. do not retry automatically
7. ask for program/user clarification if needed
8. resume only after program-kb and queues are updated
```

### Handoff Runbook

```text
1. update metrics and coverage
2. summarize completed phases
3. list high-priority leads with evidence and next action
4. list blocked items with reprocess condition
5. list accepted gaps with revisit trigger
6. list active findings and report-readiness state
7. write notes/recent-state.md
8. ensure no required job/session is still running
```

## Failure Modes And Recovery

Every robust recon system needs defined behavior for common failure modes.

```text
provider outage:
  mark provider data stale_or_unavailable, keep previous evidence historical,
  do not fabricate missing results, rerun later

provider disagreement:
  preserve both results, lower confidence, require another source or live
  in-scope validation before active use

parser failure:
  quarantine raw data, write rejection reason, keep phase running for other
  inputs

schema migration:
  version schemas, keep old normalized data readable, write migration log

scope ambiguity:
  mark needs_review, passive-only, generate scope question, block active queues

rate-limit uncertainty:
  block active jobs until configured; do not infer safe rate from tool defaults

auth expiration:
  stop authenticated queues, refresh owned-account auth, invalidate stale
  baseline comparisons

soft-404 calibration failure:
  block fuzz job or require manual baseline; do not promote fuzz hits

wildcard DNS failure:
  block active subdomain fuzzing for that root until wildcard filtering works

out-of-scope redirect:
  record redirect target, classify it, do not actively follow it

unexpected sensitive data:
  stop job, minimize access, preserve minimal evidence, follow program policy

tool crash:
  preserve partial raw output, mark job incomplete, do not treat missing output
  as absence of assets

duplicate explosion:
  pause promotion, tune dedupe keys, rerun normalization before continuing
```

## Schema Versioning And Change Control

The framework must be evolvable without breaking old target workspaces.

```text
schema_version:
  every JSON/JSONL object includes schema_version

framework_version:
  every run records framework document date and optional git/hash identifier

migration_log:
  schema changes write output/normalized/migrations/<timestamp>.md

backward compatibility:
  old objects are readable or explicitly migrated before diffing

decision log:
  every automated reclassification writes old state, new state, rule, evidence,
  and timestamp to program-kb/decision-log.jsonl

manual override:
  overrides require reason, source, operator, timestamp, expiry, and revisit
  condition
```

## Security And Secret Handling

Recon output must not become a liability.

```text
store secrets outside target notes and reports
store only secret file paths in notes
redact cookies, bearer tokens, API keys, session IDs, CSRF tokens, and personal
  data from summaries
encrypt or permission-restrict raw authenticated traffic when possible
never commit secrets, PATs, cookies, callback tokens, or private report drafts
minimize real-user data in evidence
use owned-account data for screenshots and reports
redact unrelated personal data from HARs and responses
separate raw evidence from shareable report artifacts
```

## Design Review Checklist

Before declaring a target workspace ready, verify:

```text
program-kb complete enough to enforce scope
all active actions require wrappers
all queues have preconditions and stop conditions
all phases have inputs, outputs, gates, and metrics
all schemas have stable IDs and source refs
all passive collectors preserve raw evidence
all active collectors preserve request metadata
all fuzz jobs require calibration
all role/tenant tests use owned accounts
all leads have boundary hypothesis and next action
all findings require six-gate proof
all unknowns are blocked, review, or accepted_gap
all accepted gaps have revisit triggers
all trusted-source benchmark rows are covered or blocked
all runbooks exist in the target workspace
all secrets are out of notes and reports
```

## Phase 0: Program Knowledge Base

The program knowledge base is the decision source for scope, testability,
priority, and blocked actions. It must be populated before live probing and
before active fuzzing.

### Program Data To Store

```text
program identity:
  platform, program name, program id, policy URL, retrieved timestamp

legal and brand context:
  company names, subsidiaries, acquired brands, product names, old names

scope:
  exact domains, wildcard domains, IP ranges, APIs, mobile apps, repos,
  browser extensions, cloud assets, explicitly included third-party surfaces

out of scope:
  domains, apps, IPs, vendors, vulnerability classes, workflows, actions

testing rules:
  required headers, user-agent tags, rate limits, automation limits,
  account rules, credential rules, data handling rules

safe action model:
  passive only, GET/HEAD allowed, authenticated read allowed, owned-object
  state changes allowed, fuzzing allowed, prohibited actions

business model:
  products, roles, tenants, sensitive data, critical workflows, money flows,
  trust boundaries, integration ecosystem

security model:
  auth provider, SSO/OIDC/SAML, MFA, SCIM, sessions, cookies, CSP, CORS,
  tenant model, role model, data isolation model

triage and payout model:
  platform severity taxonomy, program severity table, accepted high-impact
  classes, excluded low-impact classes, duplicate guidance, report format,
  required evidence, novelty expectations

automation model:
  allowed automation types, maximum request rate, concurrency, time windows,
  scanning prohibitions, AI/agent restrictions, required human validation,
  required request markers
```

### Classification Outputs

Every discovered item gets:

```text
scope_status:
  in_scope
  out_of_scope
  unknown_do_not_touch
  third_party
  conflict_needs_review

testability:
  passive_only
  safe_baseline_allowed
  authenticated_read_allowed
  owned_object_state_allowed
  fuzzing_allowed
  blocked
  needs_review

confidence:
  0.0 to 1.0

allowed_actions:
  dns, ct_lookup, archive_lookup, http_head, http_get_root, js_inventory,
  api_schema_check, screenshot, crawl_low_rate, ffuf_path_low, ffuf_api_low,
  authz_diff_owned, upload_owned, callback_owned

blocked_actions:
  high_volume_scan, brute_force, password_attack, destructive_state_change,
  billing_action, spam, takeover, real_user_data_access, third_party_testing
```

### Confidence Model

The classifier must use explicit confidence levels. Confidence affects whether
the framework can act automatically or must keep the item passive-only.

```text
0.95-1.00:
  exact policy match or official program asset, no exclusion match

0.80-0.94:
  wildcard policy match with supporting live DNS/TLS/HTTP evidence and no
  exclusion match

0.60-0.79:
  strong ownership evidence such as official docs, multiple passive sources,
  cert SANs, or CNAME patterns, but policy wording is indirect

0.30-0.59:
  weak relation such as brand string, old cert, archive-only URL, shared CDN,
  or single exposure-provider hit

0.00-0.29:
  likely unrelated, third-party, parked, stale, or explicitly excluded
```

Default action mapping:

```text
>= 0.95 and rules allow:
  active baseline and eligible fuzz profiles

0.80-0.94:
  active baseline allowed only if wildcard scope and automation rules are clear

0.60-0.79:
  passive enrichment and manual/policy review before active probing

< 0.60:
  passive-only or blocked
```

### Decision Examples

```json
{
  "asset": "api.dev.example.com",
  "decision": "safe_baseline_allowed",
  "confidence": 0.92,
  "reason": [
    "matches wildcard scope rule: *.example.com",
    "does not match exclusions",
    "low-impact unauthenticated GET/HEAD is allowed",
    "rate limit profile exists"
  ],
  "allowed_actions": ["dns", "http_head", "http_get_root", "headers", "js_inventory"],
  "blocked_actions": ["high_volume_scan", "destructive_state_change"]
}
```

```json
{
  "asset": "help.example.com",
  "decision": "needs_review",
  "confidence": 0.58,
  "reason": [
    "matches wildcard scope rule",
    "CNAME points to vendor helpdesk platform",
    "third-party testing rules are ambiguous"
  ],
  "allowed_actions": ["passive_collection"],
  "blocked_actions": ["active_testing", "fuzzing"]
}
```

## Phase 1: Seed Expansion

Start from official, policy-backed seeds. Do not start from random internet
matches.

### Seed Sources

```text
program policy
official website
product pages
pricing pages
developer docs
API docs
OpenAPI/Swagger docs
GraphQL docs
help center
status page
trust center
security page
privacy policy
subprocessor list
press releases
changelogs and release notes
engineering blog
job postings
app store listings
Google Play listings
browser extension stores
public GitHub/GitLab orgs
package registries
container registries
certificate transparency logs
DNS records
known ASNs and netblocks
brand and acquisition records
public disclosed reports and hacktivity when relevant
platform asset inventory exports when available
```

### Seed Object Schema

```text
seed:
type:
value:
source_url:
retrieved_at:
scope_relevance:
confidence:
derived_terms:
notes:
```

Derived terms should feed target-specific wordlists:

```text
company names
product names
feature names
role names
object names
API resource names
old brand names
internal environment names from docs
integration names
```

### Business And Product Understanding

For high-signal hunting, source ingestion must extract business meaning, not
just hostnames.

```text
customer types
tenant model
roles and permissions
paid tiers and feature gates
admin/support operations
data import and export paths
file handling paths
integrations and webhooks
identity and SSO options
compliance-sensitive data
new features from changelog
deprecated or migrating products
```

The framework should prioritize surfaces where product documentation says one
role, tenant, tier, or state should not be able to perform an action, because
those statements become test oracles for access control and business logic.

## Phase 2: Passive Asset Intelligence

Passive collection may be massive because it does not touch target
infrastructure directly. It still must label unknown and third-party results
correctly.

### Subdomain And DNS Sources

Use multiple overlapping sources because every source has blind spots:

```text
subfinder
amass intel
amass enum passive mode
certificate transparency logs
crt.sh
Censys certificate data
SecurityTrails
VirusTotal
AlienVault OTX
ProjectDiscovery Chaos
DNSDB-style feeds when available
RapidDNS-style indexes
Common Crawl host extraction
urlscan.io domain searches
Wayback/CDX host extraction
search engine indexed hosts
```

### Passive URL Sources

```text
ProjectDiscovery urlfinder
Wayback Machine CDX
Common Crawl Index
urlscan.io
gau-style collectors
waybackurls-style collectors
search engine cache/index results
public sitemap archives
public API docs
public Postman collections
GitHub code search
GitLab code search
package readmes and examples
```

### Passive Takeover And Dangling Dependency Signals

Detect takeover-style leads passively first. Active claim attempts are blocked
unless explicitly allowed by the program.

```text
dangling CNAMEs
unclaimed SaaS hostnames
orphaned CDN distributions
orphaned storage aliases
deleted app platforms
expired domains in redirects or scripts
missing DNS targets
NXDOMAIN CNAME targets
service-specific default error pages
old documentation pointing to retired hosts
```

High-signal requirements:

```text
scope proof for the hostname
evidence that the dependency is dangling
evidence that the service is takeover-capable
program policy allows takeover validation or the lead remains unclaimed
no attempt to claim production assets without explicit approval
```

### Passive Output Requirements

Every result must preserve provenance:

```text
value:
value_type:
source:
source_query:
first_seen:
last_seen:
retrieved_at:
raw_evidence_path:
normalized_value:
scope_status:
confidence:
dedupe_key:
```

## Phase 3: Internet Exposure Mapping

Exposure providers identify public services, banners, certs, favicons,
technologies, and historical infrastructure. These results are not authorization
proof. They feed the classifier.

### Providers

```text
Shodan
Censys
FOFA
ZoomEye
Netlas
BinaryEdge
LeakIX
Criminal IP
GreyNoise-style context
```

### Query Strategies

```text
domain and subdomain
TLS common name
TLS SAN values
certificate issuer patterns
favicon hash
HTTP title
HTTP body fingerprint
org name
legal entity name
brand name
ASN
netblock
CNAME/CDN patterns
technology banners
known product strings
API route strings
```

### Exposure Object Schema

```text
provider:
query:
host:
ip:
port:
protocol:
service:
title:
banner_hash:
favicon_hash:
tls_subject:
tls_sans:
org:
asn:
country:
first_seen:
last_seen:
technologies:
raw_evidence_path:
scope_status:
testability:
confidence:
```

### Non-Standard HTTP Port Discovery

Heavy bounty recon should not assume web services live only on ports 80 and
443. Use exposure providers first, then policy-gated low-impact probing for
confirmed in-scope assets.

Track:

```text
non-standard HTTP/HTTPS ports
admin panels
developer consoles
debug dashboards
metrics endpoints
API gateways
service meshes
preview environments
staging environments
old app servers
```

High-signal filters:

```text
HTTP title indicates product, admin, staging, docs, API, metrics, or debug
TLS certificate matches in-scope identity
technology fingerprint suggests app framework or management console
port has auth boundary, API behavior, or sensitive route hints
provider last_seen is recent
```

## Phase 4: DNS, Subdomain, And VHost Discovery

This phase combines passive results with active discovery where the program
allows it.

### DNS Normalization

For each hostname:

```text
hostname:
root_domain:
source_count:
sources:
resolves:
record_types:
a_records:
aaaa_records:
cname_chain:
mx_records:
txt_records:
ns_records:
wildcard_dns_detected:
cdn_or_waf:
scope_status:
testability:
```

### DNS Quality Controls

```text
detect wildcard DNS per root and per environment
detect CDN default catch-all behavior
resolve from multiple resolvers where practical
store resolver, timestamp, and TTL
compare A/AAAA/CNAME/MX/TXT/NS drift across runs
label private, reserved, loopback, link-local, and metadata IP targets as
  blocked for active probing unless the program explicitly includes them
separate hostname discovery from HTTP liveness
```

### Active Subdomain Fuzzing With ffuf

Only run if active discovery is allowed and wildcard filtering is configured.

```bash
ffuf -w subdomains.txt \
  -u https://FUZZ.example.com/ \
  -mc all \
  -fs <wildcard_size> \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/subdomains.example.com.json
```

Use target-specific and generic lists:

```text
generic subdomains
cloud service names
environment names
product names
feature names
region names
old brand names
team names from docs or jobs
```

### VHost Fuzzing With ffuf

Only run against in-scope IPs or where the policy explicitly permits vhost
testing against related infrastructure.

```bash
ffuf -w vhosts.txt \
  -u https://<known-host>/ \
  -H "Host: FUZZ.example.com" \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/vhosts.<known-host>.json
```

## Phase 5: Liveness And Web Surface Classification

For confirmed in-scope hosts, perform low-impact baseline probes through request
wrappers that enforce scope, headers, user-agent, and rate limits.

### Baseline Data

```text
asset:
scope_status:
probe_profile:
timestamp:
request_summary:
status_code:
final_url:
redirect_chain:
tls:
dns:
headers:
cookies:
csp:
cors:
robots_txt:
sitemap_xml:
security_txt:
page_title:
visible_features:
linked_scripts:
api_hints:
auth_entry_points:
errors_or_anomalies:
evidence_paths:
```

### Classification Labels

```text
marketing_site
web_app
api
graphql
websocket
admin
support
docs
developer_portal
auth
sso
static_assets
cdn
storage
status
mobile_backend
internal_candidate
staging_candidate
third_party
```

### Live Baseline Quality Controls

Every baseline probe must include enough comparison data to prevent noisy
findings:

```text
known-missing path baseline
random path baseline
root path baseline
authenticated and unauthenticated baseline when accounts exist
redirect-chain normalization
body hash and perceptual screenshot hash
soft-404 fingerprint
auth redirect fingerprint
error-page fingerprint
WAF/block-page fingerprint
cache headers and CDN identifiers
content-language and region variation when relevant
```

Only create a lead from a baseline anomaly when it differs from the expected
baseline in at least one meaningful way:

```text
authorization boundary changed
route existence is proven
sensitive metadata exposed
unexpected technology or admin surface appears
state-changing route is reachable
error discloses stack, config, tenant, object, or internal routing data
redirect or CORS behavior is controllable
```

## Phase 6: JavaScript Discovery And Mining

JavaScript discovery is a first-class recon layer. Modern apps expose routes,
API bases, object names, feature flags, build systems, and integration hints in
client bundles.

### JS Collection Sources

```text
live pages
linked script tags
Next.js manifests
Webpack manifests
Vite manifests
Nuxt assets
Angular bundles
source maps
service workers
web workers
browser HAR captures
archived pages
urlscan.io captures
Common Crawl pages
mobile app WebView assets
browser extension packages
```

### JS Extraction Targets

```text
API base URLs
REST routes
GraphQL endpoints
GraphQL operation names
WebSocket URLs
SSE endpoints
object/resource names
role and permission strings
feature flags
environment names
cloud storage URLs
CDN origins
OAuth client ids
SAML/OIDC metadata paths
third-party SDK keys
error tracking DSNs
build ids and release ids
source map URLs
```

### JS Object Schema

```text
script_url:
host:
hash:
size:
content_type:
source:
retrieved_at:
build_system:
sourcemap_url:
routes:
api_hosts:
endpoints:
graphql_operations:
websocket_urls:
cloud_urls:
secrets_candidates:
feature_flags:
evidence_path:
```

Secrets candidates are triage leads only. Do not use or validate credentials
against real services unless the program explicitly allows it.

## Phase 7: URL, Endpoint, And Parameter Inventory

Merge URLs from live crawl, passive archives, JS extraction, API docs, mobile
apps, and code search.

### URL Schema

```text
url:
normalized_url:
host:
path:
query_keys:
method_hint:
content_type:
source:
auth_required:
status_observed:
scope_status:
sensitivity_hint:
first_seen:
last_seen:
```

### Endpoint Schema

```text
endpoint_id:
method:
base_url:
path_template:
params:
body_schema_hint:
auth_required:
roles_seen:
object_ids_seen:
tenant_ids_seen:
state_changing:
source:
evidence_paths:
testability:
priority:
```

### Discovery Methods

```text
browser navigation with HAR capture
katana-style crawling
robots.txt and sitemap.xml expansion
JS-derived routes
archive-derived URLs
OpenAPI and Swagger parsing
GraphQL schema and operation parsing
Postman collection parsing
mobile app string extraction
GitHub/GitLab code search
documentation examples
```

## Phase 8: API, GraphQL, WebSocket, And Realtime Surfaces

API inventory is a top-level deliverable because shadow APIs, zombie versions,
and undocumented mobile endpoints are common bug bounty opportunities.

### REST And HTTP API Mapping

Track:

```text
API bases
versions
resource names
object ID patterns
pagination
filters
sort fields
bulk endpoints
import/export endpoints
admin routes
partner routes
mobile-only routes
legacy routes
undocumented routes
error behavior
```

### API High-Signal Test Oracles

For each API endpoint, capture the expected behavior before fuzzing or authz
diffing:

```text
required auth state
required role
required tenant
required object ownership
supported methods
supported content types
required headers
accepted query params
accepted body fields
error model
pagination model
rate-limit behavior
idempotency behavior
side effects
```

### Hidden Parameter And Mass Assignment Mapping

PortSwigger's API testing guidance makes hidden parameters, supported methods,
content types, mass assignment, and server-side parameter pollution explicit API
recon targets. The framework must inventory:

```text
documented fields
fields observed in responses but absent from requests
role, permission, status, tier, price, owner, tenant, admin, verified, and
  feature flag fields
query parameters accepted silently
JSON keys accepted silently
duplicate query parameters
array and object wrapper behavior
content-type parser differences
method override behavior
REST path segment pollution
structured data pollution in JSON, XML, multipart, and form bodies
```

High-signal promotion requires an observable impact:

```text
field changes state
hidden field changes authorization, price, tier, owner, role, status, or
  visibility
duplicate or polluted parameter reaches an internal API differently
unsupported content type reaches a different parser
method or override changes authorization handling
```

### GraphQL Mapping

Track:

```text
endpoint paths
introspection status
operation names
query and mutation names
subscription support
object types
ID fields
role-specific fields
tenant-specific fields
error messages
depth and complexity limits
batching behavior
CSRF posture
suggestions behavior
persisted query behavior
file upload behavior
authorization per object and field
cost, depth, and alias limits
```

Use ffuf for discovery and low-rate operation checks where allowed, but use
GraphQL-aware schema analysis for deeper testing after policy approval.

High-signal GraphQL leads:

```text
introspection available in production and exposes sensitive schema detail
suggestions reveal types or fields when introspection is disabled
queries and mutations differ across roles or tenants
object IDs from account A return data under account B
field-level authorization differs from object-level authorization
batching bypasses rate, auth, or cost controls
CSRF is possible on state-changing operations
persisted query IDs expose hidden operations
```

### WebSocket And SSE Mapping

Track:

```text
connection URLs
handshake headers
auth tokens
message types
channels
tenant or room identifiers
subscribe/unsubscribe flows
server events
role-specific behavior
state-changing message types
origin checks
CSRF or cross-site WebSocket posture
message schemas
client-to-server actions
server-to-client sensitive data
reconnect and resume behavior
```

High-signal WebSocket leads:

```text
handshake trusts spoofable headers
cross-site WebSocket connection succeeds with user credentials
message includes tenant, room, org, project, or user IDs that can be swapped
role-specific message actions succeed for lower roles
server broadcasts sensitive data to unauthorized subscriptions
state-changing messages lack CSRF or origin protection
input in WebSocket messages reaches another user's browser or server-side sink
```

## Phase 9: Mobile, Desktop, And Browser Extension Recon

Mobile and extension artifacts often expose backend hosts and flows not visible
from the web app.

### Mobile Sources

```text
Apple App Store listings
Google Play listings
APK packages where legally accessible
IPA metadata where legally accessible
deep links
intent filters
universal links
app links
embedded API hosts
GraphQL operations
certificate pinning notes
analytics and crash reporting endpoints
```

### Extension Sources

```text
Chrome Web Store
Firefox Add-ons
manifest.json
permissions
content scripts
background scripts
externally connectable domains
API hosts
message handlers
OAuth flows
```

### Desktop And CLI Sources

Where included by the program, also inspect:

```text
desktop app update manifests
auto-update endpoints
Electron bundles
local API bridges
deep link handlers
custom protocol handlers
CLI package registries
CLI config files and environment variable docs
telemetry and crash upload endpoints
```

## Phase 10: Code, Package, And Container Registry Recon

Public code and packages help build target-specific dictionaries and identify
old endpoints, examples, and configuration references.

### Sources

```text
GitHub orgs and code search
GitLab public groups and code search
Bitbucket public references
npm
PyPI
RubyGems
Maven
NuGet
Go modules
Docker Hub
GitHub Container Registry
Helm charts
Terraform modules
public SDKs
public CLI tools
```

### Extract

```text
API hosts
endpoint paths
environment variable names
object model names
deprecated routes
example credentials placeholders
OAuth scopes
webhook event names
integration names
cloud bucket naming patterns
```

## Phase 11: Cloud, CDN, Storage, And Origin Mapping

Cloud recon must remain policy-gated. Public references and naming patterns can
be collected passively. Active validation of buckets, origins, and storage
permissions needs explicit scope and policy fit.

### Surfaces

```text
S3-style buckets
GCS buckets
Azure Blob containers
CloudFront distributions
Fastly services
Cloudflare zones
Akamai hostnames
signed URL workflows
asset upload paths
export/download links
static build buckets
origin host leakage
```

### High-Value Questions

```text
Can owned users create files that are later rendered or transformed?
Are signed URLs scoped to account, object, and time?
Do exports include cross-tenant data?
Do previews fetch attacker-controlled URLs?
Are CDN cache keys tenant-aware?
Can old static builds reveal retired APIs?
```

## Phase 12: Auth, Identity, SSO, And Session Mapping

Identity workflows are high-impact and policy-sensitive. Map broadly, then test
carefully with owned accounts.

### Surfaces

```text
signup
login
logout
password reset
email verification
email change
MFA enrollment and removal
recovery codes
OAuth connect and disconnect
OIDC flows
SAML flows
SCIM provisioning
invite accept and revoke
session refresh
device/session management
API tokens
personal access tokens
service accounts
role changes
tenant switching
```

### Evidence To Store

```text
cookies
token storage location
CSRF mechanism
redirect URIs
state and nonce behavior
session invalidation behavior
role claims
tenant claims
token audience
token issuer
owned-account request/response pairs
```

### Client-Side Trust Boundaries

Modern apps often enforce important state in client code. Map and test:

```text
client-side route guards
feature flag checks
role checks in JavaScript
hidden admin links
postMessage listeners
OAuth redirect handling
fragment and query token handling
CORS preflight and credential behavior
CSP policy and nonce behavior
service worker scope and cache behavior
localStorage/sessionStorage token use
cross-origin iframe and clickjacking posture
DOM sinks fed by URL, storage, postMessage, WebSocket, or API data
```

High-signal client-side leads require a server-side or user-impact path, such as
authorization bypass, token leakage, stored or privileged client-side execution,
or a confused-deputy flow.

## Phase 13: Business Workflow And Trust Boundary Mapping

The framework must understand the business before ranking leads.

### Critical Workflows

```text
billing
subscription changes
coupons and credits
refunds
invites
team and org membership
role management
project/resource sharing
file upload
file preview
file import
file export
webhooks
integrations
support workflows
admin workflows
audit logs
notifications
approval flows
data deletion
data transfer
AI or automation features
template builders
report generators
server-side rendering or preview flows
web cacheable personalized content
```

### Role And Tenant Matrix

For each endpoint and workflow, record:

```text
unauthenticated reachability
account A reachability
account B reachability
tenant A member reachability
tenant A admin reachability
tenant B member reachability
tenant B admin reachability
support or admin reachability when allowed
expected access
observed access
differences
```

### Cache, Race, And State-Machine Surfaces

Add these as first-class high-signal workflow categories where policy permits:

```text
web cache deception
web cache poisoning
CDN cache key confusion
race conditions on limits, invites, coupons, credits, and role changes
state-machine bypasses in invite, approval, reset, purchase, refund, and export
double-submit and replay behavior
idempotency-key misuse
async job authorization
delayed processing after permission revocation
audit-log and notification side effects
```

These are promoted only when there is clear owned-account impact, such as
private data in cache, unauthorized state transition, duplicate value creation,
or a privileged action completed from a lower role.

## Phase 14: Fuzzing Framework

Fuzzing is a policy-gated module. It is not baseline recon. It runs only after
scope classification, baseline capture, rate-limit setup, and action approval.

### Fuzzing Control Flow

```text
surface discovery
  -> fuzz candidate generation
  -> policy and scope gate
  -> risk profile selection
  -> ffuf or specialized runner
  -> result normalization
  -> baseline comparison
  -> anomaly detection
  -> lead creation
```

### Fuzz Gate

Before any fuzz job runs:

```text
asset_scope == in_scope
testability includes fuzzing_allowed
required headers are configured
rate limit is configured
auth context uses owned account when needed
payload class is allowed by policy
stop conditions are configured
output path is configured
```

### Stop Conditions

```text
stop_on_429
stop_on_403_spike
stop_on_5xx_spike
stop_on_waf_block
stop_on_account_lock
stop_on_unexpected_real_data
stop_on_large_response_volume
stop_on_redirect_to_out_of_scope
stop_on_state_change_outside_owned_objects
```

### Fuzz Calibration Requirements

Every ffuf profile must run a calibration phase before the main job:

```text
random token baseline
known missing route baseline
known valid route baseline where available
authenticated baseline where applicable
unauthenticated baseline where applicable
content length and word count clustering
response hash clustering
redirect target clustering
content-type clustering
soft-404 and auth-redirect detection
WAF/block-page detection
```

Fuzz output becomes a candidate only when it survives calibration. Good signals
include:

```text
status differs from soft-404 cluster
content type differs from baseline
body hash differs from baseline
auth state changes response shape
method changes route behavior
error code indicates parser or router reached
response includes route-specific schema, validation, or permission text
```

### ffuf Profiles

#### Subdomain DNS Fuzzing

```bash
ffuf -w subdomains.txt \
  -u https://FUZZ.example.com/ \
  -mc all \
  -fs <wildcard_size> \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/subdomains.example.com.json
```

#### VHost Fuzzing

```bash
ffuf -w vhosts.txt \
  -u https://example.com/ \
  -H "Host: FUZZ.example.com" \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/vhosts.example.com.json
```

#### Web Path Fuzzing

```bash
ffuf -w paths.txt \
  -u https://app.example.com/FUZZ \
  -mc 200,204,301,302,307,308,401,403 \
  -fc 404 \
  -rate <program_rate> \
  -recursion \
  -recursion-depth 1 \
  -of json \
  -o output/ffuf/paths.app.example.com.json
```

#### API Path Fuzzing

```bash
ffuf -w api-paths.txt \
  -u https://api.example.com/FUZZ \
  -H "Accept: application/json" \
  -mc 200,201,204,301,302,400,401,403,405,415,422 \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/api.api.example.com.json
```

Useful API status signals:

```text
200/204: accessible route
400/415/422: parser reached, route likely exists
401/403: route likely exists and requires auth
405: method mismatch, route likely exists
```

#### Parameter Fuzzing

```bash
ffuf -w params.txt \
  -u 'https://app.example.com/search?FUZZ=test' \
  -mc all \
  -fs <baseline_size> \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/params.search.json
```

#### JSON Key Fuzzing

```bash
ffuf -w json-fields.txt \
  -u https://api.example.com/v1/search \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"FUZZ":"test"}' \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/json-fields.search.json
```

#### Server-Side Parameter Pollution Fuzzing

Only run where API parameter testing is allowed.

```bash
ffuf -w params.txt \
  -u 'https://api.example.com/v1/search?existing=value&FUZZ=probe' \
  -H "Accept: application/json" \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/sspp-query.search.json
```

Structured format variants:

```text
duplicate query keys
array notation
object notation
semicolon path parameters
encoded separators
JSON duplicate keys
multipart field duplication
XML duplicate elements
```

#### Content-Type Fuzzing

```bash
ffuf -w content-types.txt \
  -u https://api.example.com/v1/search \
  -X POST \
  -H "Content-Type: FUZZ" \
  -d '{"query":"test"}' \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/content-types.search.json
```

#### Method Fuzzing

Default method wordlist:

```text
GET
HEAD
OPTIONS
```

Add `POST`, `PUT`, `PATCH`, and `DELETE` only for owned-object workflows and
only when the policy allows state-changing method tests.

```bash
ffuf -w methods.txt \
  -u https://api.example.com/v1/users/me \
  -X FUZZ \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/methods.users-me.json
```

#### Header Fuzzing

Header fuzzing can trigger sensitive proxy and routing behavior, so it is
medium risk by default.

```bash
ffuf -w headers.txt \
  -u https://api.example.com/v1/me \
  -H "FUZZ: test" \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/headers.me.json
```

Candidate headers:

```text
X-Forwarded-Host
X-Forwarded-For
X-Original-URL
X-Rewrite-URL
X-HTTP-Method-Override
X-Forwarded-Proto
X-Forwarded-Prefix
```

#### GraphQL Endpoint Fuzzing

```bash
ffuf -w graphql-paths.txt \
  -u https://api.example.com/FUZZ \
  -mc 200,400,401,403,405 \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/graphql-paths.json
```

Common paths:

```text
graphql
api/graphql
v1/graphql
query
graphiql
playground
console
```

#### GraphQL Operation Fuzzing

```bash
ffuf -w graphql-ops.txt \
  -u https://api.example.com/graphql \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"query FUZZ { __typename }"}' \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/graphql-ops.json
```

#### GraphQL Suggestions Fuzzing

Use only low-rate target-specific operation and field names.

```bash
ffuf -w graphql-fields.txt \
  -u https://api.example.com/graphql \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"query { FUZZ }"}' \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/graphql-suggestions.json
```

Promote only if responses reveal valid schema elements or authorization-relevant
objects, and only after scope and GraphQL testing rules are confirmed.

#### GraphQL Introspection Checks

Only run if GraphQL testing and introspection checks are allowed.

```bash
ffuf -w graphql-introspection.txt \
  -u https://api.example.com/graphql \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"FUZZ"}' \
  -mc all \
  -rate <program_rate> \
  -of json \
  -o output/ffuf/graphql-introspection.json
```

#### Object ID And Authz Differential Fuzzing

This is usually higher value than blind payload fuzzing.

Inputs:

```text
owned account A object IDs
owned account B object IDs
tenant A object IDs
tenant B object IDs
role A auth
role B auth
baseline legitimate requests
```

Compare:

```text
status code
response size
object owner
tenant owner
hidden fields
side effects
error text
timing
audit log entries
notification side effects
```

#### WebSocket Message Fuzzing

`ffuf` is not the main runner for WebSocket messages. Use browser/Burp/custom
message replay where allowed, then normalize results into the same fuzz schema.

Targets:

```text
message type
channel
room id
tenant id
object id
role action
pagination cursor
filter fields
resume token
origin header in handshake
authorization header in handshake
```

Promote only when owned-account comparisons show unauthorized subscription,
unauthorized action, cross-tenant data, missing origin checks, or sensitive
message leakage.

#### File Workflow Fuzzing

Only in owned test workspaces and only if uploads/imports are allowed.

Targets:

```text
content type
extension
filename
metadata
archive structure
preview renderer
converter
import parser
download authorization
signed URL scope
```

Use benign mutations first. Do not upload destructive payloads, malware-like
content, excessive files, or production-disruptive inputs.

#### Callback And Fetcher Fuzzing

Only with an owned callback server and clear policy permission.

Targets:

```text
webhooks
URL importers
link previews
image fetchers
PDF generators
HTML renderers
integration test callbacks
```

Blocked by default:

```text
localhost
private IP ranges
cloud metadata IPs
internal DNS names
file schemes
gopher schemes
non-HTTP schemes
```

Unblock only if the program explicitly permits SSRF-style testing.

### Fuzz Result Schema

```json
{
  "tool": "ffuf",
  "profile": "api_paths",
  "target_template": "https://api.example.com/FUZZ",
  "wordlist": "api-paths.txt",
  "rate": 20,
  "timestamp": "2026-04-30T00:00:00Z",
  "program_rules": ["SCOPE-003", "RATE-001", "FUZZ-API-LOW"],
  "result": {
    "url": "https://api.example.com/v1/users",
    "status": 401,
    "length": 82,
    "words": 5,
    "lines": 1,
    "redirect": null
  },
  "classification": "candidate_endpoint",
  "reason": "401 indicates route likely exists and requires auth",
  "next_action": "add to endpoint inventory and compare with owned auth"
}
```

## Phase 15: Target-Specific Wordlist Generation

Massive recon becomes useful when wordlists are target-specific.

Generate dictionaries from:

```text
program policy
product pages
developer docs
help center
changelogs
API docs
OpenAPI schemas
GraphQL schemas
JS routes
mobile strings
GitHub code
package names
job postings
blog posts
status pages
feature flags
object names
role names
integration names
tenant terminology
old brands
region names
environment terms
```

Wordlist categories:

```text
subdomains
vhosts
paths
api_paths
params
json_fields
graphql_paths
graphql_operations
headers
methods
object_keys
file_names
cloud_bucket_names
environment_names
```

## Phase 16: Attack Surface Graph

All normalized data should feed a graph. The graph makes recursion and chaining
possible.

### Node Types

```text
program
brand
domain
host
ip
service
web_app
api_base
endpoint
url
js_file
mobile_app
extension
cloud_resource
identity_provider
role
tenant
account
object_type
workflow
third_party
finding_candidate
```

### Edge Types

```text
mentions
resolves_to
cname_to
serves
redirects_to
loads_script
calls_api
uses_auth_provider
uses_storage
belongs_to_brand
owned_by_tenant
reachable_by_role
creates_object
reads_object
updates_object
deletes_object
exports_data
imports_data
sends_callback
triggers_workflow
```

## Phase 17: Lead Scoring

Score candidates by impact likelihood and policy safety.

### Positive Signals

```text
explicitly in scope
business-critical workflow
auth boundary present
tenant boundary present
role difference observed
owned object IDs available
admin/support/billing surface
file upload or import surface
export/download surface
webhook or callback surface
GraphQL endpoint
mobile-only API
legacy version
staging/dev/qa/uat naming
unexpected 200
unexpected 500
401/403 route discovered from fuzzing
route exists but is unlinked
archived endpoint still live
source map available
JS exposes hidden routes
```

### Negative Signals

```text
unknown scope
third-party hosted and ambiguous
policy exclusion
rate limit unknown
auth unavailable
no owned object setup
static marketing content only
duplicate source-only signal
historical-only URL with no live evidence
```

### Example Score Formula

```text
score =
  business_criticality
  + auth_boundary_presence
  + tenant_boundary_presence
  + role_difference
  + owned_object_control
  + sensitive_data_potential
  + state_change_potential
  + file_or_callback_surface
  + legacy_or_hidden_signal
  - policy_restriction
  - scope_uncertainty
  - third_party_risk
  - rate_limit_uncertainty
```

## Phase 18: Evidence Promotion Pipeline

Use the existing bounty pipeline:

```text
notes -> leads -> primitives -> findings -> reports
```

### Promotion Gates

```text
notes -> leads:
  observed anomaly, unusual exposure, route, difference, or sensitive surface

leads -> primitives:
  reproducible, attacker-controlled behavior using owned accounts or allowed
  unauthenticated access

primitives -> findings:
  crosses or chains to a meaningful security boundary with demonstrated impact

findings -> reports:
  concise policy-fit writeup with exact repro, evidence, and novelty checks
```

### Six-Step Finding Gate

Every reportable issue must pass:

```text
1. observe live weirdness
2. reproduce and control it
3. understand the mechanism
4. escalate to highest safe impact
5. build minimal proof with owned accounts and minimal data
6. prove novelty and policy fit
```

## Phase 19: Continuous Recon And Diffing

Recon should be continuous. Every rerun should preserve old state and produce a
diff.

### Daily Or Per-Session

```text
program policy diff
scope diff
CT log diff
new subdomains
DNS resolution diff
new JS bundle hashes
new URL archive hits
new urlscan captures
new status page incidents
```

### Weekly

```text
exposure provider refresh
Shodan/Censys/FOFA-style diffs
full URL archive refresh
technology/version drift
mobile app version checks
GitHub/package/container registry search refresh
cloud naming pattern refresh
```

### On Major App Change

```text
JS route diff
API operation diff
GraphQL schema diff
OpenAPI diff
mobile strings diff
role behavior diff
auth/session behavior diff
```

## Phase 20: Completion Criteria

Recon is not complete because tools finished. It is complete when these are
true for the current campaign scope:

```text
program rules are stored and enforceable
all seeds are sourced and timestamped
all discovered assets are classified or blocked as unknown
all in-scope assets have passive enrichment
all allowed in-scope assets have live baseline evidence or documented blockers
all JS, URL, API, mobile, and cloud signals are normalized
all redirect, script, API, and third-party hosts are classified
all high-priority fuzz candidates are either run, blocked, or queued with reason
all anomalies are in notes/loop/queue.md or leads/
all primitives have reproducible owned-account proof
all findings pass the six-step gate
unknowns are resolved, blocked, or accepted gaps
recent-state.md is updated
design invariants have no open violations
acceptance tests pass for the current framework implementation
all queues contain only items with preconditions, allowed actions, and stop
  conditions
all rejected objects have reason and reprocess condition
all manual overrides have expiry and revisit condition
all secrets and auth materials are excluded from notes and reports
```

## Coverage Matrix

Maintain `coverage/` files for every target. A heavy engagement is not deep
enough until each row is `covered`, `blocked_by_policy`, `blocked_by_access`, or
`accepted_gap`.

### OWASP WSTG Information Gathering Coverage

```text
search engine discovery:
  sources/search-indexes.md, assets/urls.jsonl

webserver fingerprinting:
  assets/services.jsonl, notes/live-probing.md

webserver metafiles:
  robots.txt, sitemap.xml, security.txt, well-known files

attack surface identification:
  graph/attack-surface.graph.json, surfaces/*.md

web page content review:
  output/evidence/, assets/js.jsonl, notes/traffic-map.md

entry point identification:
  assets/endpoints.jsonl, assets/urls.jsonl

execution path mapping:
  notes/traffic-map.md, surfaces/*, role/tenant matrix

framework fingerprinting:
  assets/services.jsonl, JS build metadata, headers, screenshots

application fingerprinting:
  live baselines, tech fingerprints, route maps

architecture mapping:
  graph/assets.graph.json, cloud/CDN/auth/API relations
```

### OWASP API Security Coverage

```text
API1 BOLA:
  owned-object differential requests across accounts and tenants

API2 broken auth:
  login, session, token, reset, MFA, OAuth/OIDC/SAML mapping

API3 object property authorization:
  response-field inventory, hidden field testing, mass-assignment checks

API4 resource consumption:
  rate-limit and expensive workflow mapping only where policy permits

API5 function-level authorization:
  role matrix for admin, support, billing, and member actions

API6 sensitive business flows:
  billing, invite, export, import, approval, support, and automation workflows

API7 SSRF:
  callback/fetcher inventory and owned callback testing where allowed

API8 misconfiguration:
  debug endpoints, CORS/CSP/cookies, headers, directory listing, default panels

API9 improper inventory management:
  shadow APIs, zombie versions, mobile-only APIs, archived endpoints

API10 unsafe API consumption:
  webhooks, integrations, third-party callbacks, partner API trust boundaries
```

### PortSwigger API And Realtime Coverage

```text
API documentation:
  docs, OpenAPI/Swagger, Postman, GraphQL schema, SDK examples

hidden endpoints:
  JS, archives, ffuf path/API fuzzing, mobile strings

supported methods:
  method inventory and method fuzzing with safe profiles

supported content types:
  content-type inventory and parser-difference tests

hidden parameters:
  query, JSON, form, multipart, XML, and response-field-derived dictionaries

mass assignment:
  writeable hidden fields with owned objects

server-side parameter pollution:
  duplicate keys, structured formats, REST path pollution

GraphQL:
  endpoint discovery, introspection, suggestions, batching, CSRF, authz

WebSocket:
  handshake, origin, auth context, message schema, role/tenant subscriptions
```

### Platform Quality Coverage

```text
scope proof:
  policy rule, SSL/TLS, WHOIS/ASN/network evidence where needed

report readiness:
  affected asset, scope proof, request/response, repro steps, impact, evidence

safe automation:
  headers, user-agent, rate limit, owned accounts, stop conditions

high-signal output:
  confidence, provenance, baseline comparison, business relevance, next action
```

## Default Safety Rules

These defaults apply unless the program explicitly allows more:

```text
do not actively probe unknown assets
do not fuzz unknown assets
do not test third-party systems unless explicitly included
do not brute force credentials or secrets
do not perform password attacks
do not access real user data
do not perform destructive actions
do not affect billing, spam, production stability, or availability
do not bypass rate limits
do not validate leaked credentials against services
do not submit scanner-only or theoretical reports
```

## Practical First Implementation

Build the framework in this order:

```text
1. program-kb schema and target workspace generator
2. source ingestion and scope classifier
3. passive collector runners with normalized JSONL
4. exposure provider adapters
5. DNS and liveness normalization
6. JS and URL extraction
7. endpoint inventory and attack-surface graph
8. ffuf profile generator and safety wrapper
9. lead scoring and promotion templates
10. continuous diff jobs
```

The first version should prefer correctness and auditability over speed. Once
classification and evidence quality are reliable, expand the collector set and
fuzz profiles without changing the control model.

## Trusted Source Links

These links were used to validate the framework design on 2026-04-30:

```text
OWASP WSTG Information Gathering:
  https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/

OWASP API Security Top 10 2023:
  https://owasp.org/API-Security/editions/2023/en/0x11-t10/

HackerOne Code of Conduct:
  https://www.hackerone.com/policies/code-of-conduct

HackerOne Quality Reports:
  https://docs.hackerone.com/en/articles/8475116-quality-reports

HackerOne Asset Discovery:
  https://docs.hackerone.com/en/articles/13485278-asset-discovery

Bugcrowd Recon and Discovery:
  https://www.bugcrowd.com/resources/levelup/recon-discovery/

Bugcrowd Discovering Subdomains:
  https://www.bugcrowd.com/blog/discovering-subdomains/

Bugcrowd Vulnerability Rating Taxonomy:
  https://bugcrowd.com/vulnerability-rating-taxonomy/

Intigriti Methodology Guide:
  https://www.intigriti.com/researchers/blog/hacking-tools/crafting-your-bug-bounty-methodology-a-complete-guide-for-beginners

Intigriti Triage Standards:
  https://kb.intigriti.com/en/articles/10335710-intigriti-triage-standards

Intigriti Report Writing:
  https://www.intigriti.com/researchers/blog/hacking-tools/writing-effective-bug-bounty-reports

PortSwigger API Testing:
  https://portswigger.net/web-security/learning-paths/api-testing

PortSwigger GraphQL:
  https://portswigger.net/web-security/graphql

PortSwigger WebSockets:
  https://portswigger.net/web-security/websockets

ProjectDiscovery Katana:
  https://github.com/projectdiscovery/katana
```
