# AGENTS.md - Hunterflowx

This workflow is for authorized bug bounty work only. The agent must optimize
for auditability, evidence, and repeatable testing, not for chat confidence.

## Prime Contract

Never claim that something was tested, secure, vulnerable, complete, or
confirmed unless the engagement contains durable evidence:

```text
event -> graph -> ledger -> evidence -> verdict
```

Chat is not durable state.

## Hunterflowx Rule Pack

Hunterflowx is an independent operating profile for authorized bounty work. It
combines `hunterweb` recon discipline and `GPTxOPUS` source-grounded testing
into one auditable runtime.

Before non-trivial hunting, read:

```text
rules/HUNTERFLOW_RULES.md
rules/hunterweb/AGENTS.md
rules/gptxopus/AGENTS.md
```

Rule source roles:

```text
hunterweb
  restate discipline, authorized live-behavior-first hunting, promotion
  pipeline, recon-framework control plane, durable notes, six-step proof gate

GPTxOPUS
  source-grounding protocol, A01-A10 baseline, manual test cards, evidence
  pack discipline, creative lane, retest/report QA

Hunterflowx runtime
  event ledger, dashboard, command center, graph, evidence scorer, judge,
  source verifier, risk prioritizer, domain-depth gates
```

If these sources conflict, the stricter scope, safety, source-grounding, and
evidence requirement wins. Dashboard styling must stay consistent and
professional unless the operator explicitly asks for a visual redesign.

## Required Start

For any non-trivial task, restate concretely:

```text
Target:
Program/scope:
Mode: recon | mapping | testing | validation | reporting
Role/session:
Bug class:
Current loop:
Evidence requirement:
Risk/rate-limit boundary:
```

If scope, rate limit, account rules, or authorization is unclear, mark
`blocked` and ask for the missing detail.

## Creative Exploration Rule

The workflow is mandatory as a control plane, not a cage.

AI must still explore, hypothesize, connect unusual signals, and propose new
angles. The rule is:

```text
think freely, act safely, record everything
```

Allowed creative work:

- propose uncommon bug classes from source/runtime signals
- invent new endpoint angles beyond the baseline matrix
- connect weak signals into a chain candidate
- compare source behavior against runtime behavior
- pivot from JS, errors, fingerprints, configs, docs, or business logic
- generate targeted payload mutations after understanding context
- suggest new recon paths inside scope

Not allowed:

- bypass scope, rate, auth, or destructive-test rules
- skip one-file source review when source is the basis of a claim
- call a hypothesis a finding
- report a weak primitive without impact or accepted scope policy
- hide failed experiments from the ledger

Record creative work as:

```text
creative_hypothesis_added
creative_pivot_added
chain_candidate_added
attack_path_expanded
```

Creative ideas become action only after they are converted into planned tests,
safe pivots, or explicit gaps.

## Source Hierarchy

Use the local methodology sources this way:

```text
hunterweb/recon-framework
  policy gate, recursive recon, scope validation, durable workspace

GPTxOPUS
  A01-A10 baseline, manual test cards, evidence discipline, source-grounded coverage
```

No imported methodology output can directly become a finding. It must pass this
workflow's event, evidence, and verdict gates.

The active bridge is `bbf pentest-card` plus `bbf owasp-plan`. Use it to
convert a selected bug class, Web A01-A10 category, or OWASP API Top 10 category
into final workflow `test_planned` events and durable test cards. Do not install
external full agent stacks into this workflow unless the operator explicitly
chooses that later.

Supported baseline suites:

```text
bbf pentest-card a01..a10       # Web/App A01-A10
bbf pentest-card api01..api10   # OWASP API Top 10
bbf angle-plan core|deep|creative|full
                                  # endpoint angle coverage that is not A1-only
bbf angle-exec                    # execute queued angles via HTTP/browser/Burp/Caido
bbf evidence-score                # score baseline, mutation, negative control, read-back evidence
bbf judge                         # judge whether evidence is reportable
bbf source-verify                 # verify source files were read one by one
bbf risk-prioritize               # rank endpoints worth testing first
bbf ai-governance                 # review autonomy, agent roles, data governance, and proof gates
bbf attack-path-review             # rank source-to-finding paths and queue next pivots
bbf domain-plan wp|onprem|mobile|all
                                  # activate domain-specific depth gates
bbf domain-verify                 # score WP/on-prem/mobile domain completion
bbf owasp-plan web|api|both     # generate a full suite for one surface
```

`bbf owasp-plan` must create endpoint angle events by default. If an operator
intentionally skips angle generation, the engagement must explain why in the
ledger. An endpoint with only IDOR/A01 tests is not deeply covered.

## Recursive Hunting Loop

Use this loop:

```text
recon -> analyze -> expand -> retest -> repeat
```

Every discovery can open a new loop:

- endpoint -> attack path
- parameter -> bug-class test
- JS file -> hidden API recon
- fingerprint -> payload strategy
- Burp request -> replay baseline
- dead end -> pivot, blocker, retest, or tested_secure

## Source-To-Flow Rule

When source code or extracted files are available, the agent must not scan them
as a loose blob.

Use a hard one-file-at-a-time gate:

```text
1. queue source file
2. read exactly one file fully
3. restate what the file does
4. extract routes, handlers, middleware, models, queries, sinks, sources, roles
5. link file -> flow -> endpoint -> data store/external service
6. map new attack surface
7. create multi-angle endpoint tests
8. only then move to the next file
```

Do not advance to another source file until the current file has a durable
artifact under `source-reviews/` and at least one event:

```text
source_file_read
source_flow_linked
attack_surface_mapped
endpoint_angle_planned
```

Source reading alone never confirms a vulnerability. It only creates mapped
flows, hypotheses, gaps, and planned tests.

Run `bbf source-verify --source-root <path> --queue-missing` after source is
available and after each source-review batch. A source-backed audit is not
complete while dashboard metrics show `source_files_incomplete`,
`source_reviews_missing`, or low `source_completeness_avg`.

## Endpoint Multi-Angle Rule

Every endpoint must be tested from multiple angles before it can be called
meaningfully covered.

Minimum angle set:

```text
authn_session
authz_role
object_tenant_boundary
input_validation
state_transition
business_logic
data_exposure
side_effect_write
rate_limit_or_race
cache_cors_redirect
file_or_url_handling
error_oracle
source_runtime_diff
chain_potential
```

An endpoint is not "done" when one payload fails. Each relevant angle must end
in one of:

```text
endpoint_angle_tested
verdict_set = tested_secure
verdict_set = finding_candidate
verdict_set = confirmed
gap_found
blocked
out_of_scope
by_design
inconclusive
```

If an angle is not applicable, record why. If it is applicable but untested,
keep it queued.

Use `bbf angle-plan full` on important endpoints to queue the full angle matrix
plus creative hypotheses. The dashboard metric `planned_angles` should rise; if
it stays `0`, multi-angle testing has not been operationalized yet.

Use `bbf angle-exec` to execute queued angles. It must write request/response
evidence before `endpoint_angle_tested`. Automatic executor verdicts can be
`tested_secure`, `finding_candidate`, `inconclusive`, or `blocked`, but never
`confirmed`; confirmation still requires manual evidence review.

After execution, use `bbf evidence-score`. A reportable evidence package should
include baseline, mutated request, negative control, read-back or browser-visible
state, and non-empty saved evidence files. If evidence score is partial or
incomplete, do not promote the issue until the missing evidence is resolved or
explicitly accepted by the program rules.

After scoring, use `bbf judge`. The dashboard is visibility; the judge is the
reportability gate. Do not treat "evidence exists" as report-ready unless the
judge result is `judge_reportable` or the program explicitly accepts the weaker
proof package.

When engagement size makes manual ordering expensive, run
`bbf risk-prioritize --limit <n>`. Start with P0/P1 endpoints that are `ready`
or `needs_context`; unblock high-score `blocked` endpoints only when the missing
role/session/source detail is safe and in scope.

## Governance Rule

Do not use vague autonomy claims. Every queue task must be understandable as:

```text
passive_auto
active_safe_auto
active_requires_approval
hard_deny
```

Run governance review before active testing waves and before report promotion:

```bash
bbf ai-governance check
```

The review must verify:

```text
safety allowlist
rate budget
explicit autonomy labels
active approval gate
finding evidence gate
finding judge gate
hypothesis separation
source review artifacts
agent role coverage
data governance config
```

Treat single-agent self-validation as weak. High-risk candidates should pass
through these conceptual roles, even if one operator/AI process performs the
work:

```text
recon_agent -> source_mapper -> attack_path_planner -> executor
-> validator -> evidence_judge -> report_reviewer -> safety_governor
```

Use attack-path review after graph build:

```bash
bbf attack-path-review --limit 25
bbf attack-path-review --queue --queue-limit 5
```

This ranks incomplete paths and turns missing source/auth/chain/evidence/judge
stages into concrete queue tasks.

## Domain-Specific Depth Rule

Generic Web/API testing is not enough for WordPress plugins, on-prem/source
products, or mobile applications. Activate the matching domain profile:

```text
bbf wp-plan        -> Patchstack/Wordfence, hooks, nonce, capability, sanitizer, SQL, upload, local WP lab
bbf onprem-plan    -> target-intel, sandbox install, source/current, ranked one-file triad, config/defaults, lab proof
bbf mobile-plan    -> app inventory, device proxy, decompile, mobile API diff, token storage, deeplinks, WebView, Frida proof
```

Domain profile checks must be completed with `domain_check_completed` or linked
evidence, then scored with:

```bash
bbf domain-verify --domain <wp|onprem|mobile|all>
```

Domain depth does not replace evidence quality:

```text
domain_check_completed -> evidence-score -> judge -> verdict/report
```

If dashboard shows `domain_checks_missing`, the engagement is not deep for that
domain yet.

## Chaining Rule

After any strong signal, do not report immediately unless impact is already
complete. First map what capability the primitive gives:

```text
read data
write state
change role
trigger webhook
control URL
execute JS
mint token
access file
reach internal service
```

Then test whether that capability becomes input to another bug class. Record
the chain as `chain_candidate_added` or `attack_path_expanded`.

## Event Rules

Every meaningful action must write an event:

- `scope_loaded`
- `asset_added`
- `endpoint_discovered`
- `param_discovered`
- `endpoint_seen_runtime`
- `source_file_queued`
- `source_file_read`
- `source_flow_linked`
- `attack_surface_mapped`
- `endpoint_angle_planned`
- `endpoint_angle_tested`
- `evidence_judged`
- `judge_reviewed`
- `source_completeness_reviewed`
- `endpoint_prioritized`
- `risk_prioritization_reviewed`
- `domain_profile_loaded`
- `domain_check_planned`
- `domain_check_completed`
- `domain_depth_reviewed`
- `creative_hypothesis_added`
- `creative_pivot_added`
- `chain_candidate_added`
- `loop_started`
- `analysis_completed`
- `attack_path_expanded`
- `test_started`
- `payload_attempted`
- `evidence_added`
- `dead_end_recorded`
- `pivot_decision`
- `strategy_adjusted`
- `retest_scheduled`
- `verdict_set`
- `finding_promoted`

## Verdict Gate

Allowed statuses:

```text
not_tested
mapped_only
test_attempted
inconclusive
tested_secure
finding_candidate
confirmed
out_of_scope
by_design
blocked
```

Rules:

- `confirmed` requires runtime evidence showing impact.
- `finding_candidate` is a lead, not a report.
- `tested_secure` requires adequate negative controls.
- `inconclusive` is required when evidence is insufficient.
- `blocked` requires a concrete needed action.
- `out_of_scope` requires program policy evidence.
- `by_design` requires target docs or program rules.

## Dead End Rule

A dead end must not disappear.

Choose one:

```text
pivot_decision
strategy_adjusted
retest_scheduled
gap_found
verdict_set = tested_secure
```

Bad:

```text
payload failed, no bug
```

Good:

```text
SQLi loop closed as tested_secure because baseline, boolean, error, and
time-based probes matched baseline and source showed parameterized query.
```

## Evidence Rules

Preferred evidence:

- Burp Proxy/Replayer request-response
- browser-visible screenshot
- saved response body
- owned-account before/after state
- local lab log when authorized

Store under:

```text
evidence/burp/
evidence/screenshots/
evidence/responses/
evidence/logs/
```

Never store raw cookies, tokens, API keys, passwords, CSRF values, or private
third-party data in notes, events, reports, or summaries. Redact secrets.

## Final Handoff

Every work block ends with:

```text
Events written:
Endpoints added:
Tests performed:
Evidence saved:
Verdicts changed:
Active loops:
Pivots created:
Open gaps:
Next safest action:
```
