# Final Operating Model

## Default Web/API Flow

```text
1. scope intake
2. endpoint mapping
3. source file queue
4. one-file-at-a-time source read
5. source/runtime flow linking
6. attack surface mapping
7. endpoint multi-angle test planning
8. risk-based prioritization for large endpoint sets
9. domain-specific depth profile when target is WP/on-prem/mobile
10. recursive loop queue
11. bug-class focused testing
12. evidence capture
13. evidence judge
14. verdict gate
15. attack-path chaining
16. report only confirmed issues
```

## Operator Rule

Do not ask "did AI test it?"

Ask:

```text
Where is the event?
Where is the evidence?
Where is the ledger entry?
What was expected?
What actually happened?
What is the next gap?
```

## Creativity Rule

The workflow is mandatory, but AI should not become mechanical.

AI is expected to:

- notice unusual relationships between endpoints, files, roles, and data flows
- propose new angles beyond the default matrix
- create chain candidates from weak primitives
- pivot from source/runtime differences
- use business context to prioritize non-obvious tests

AI must record creative ideas as `creative_hypothesis_added` or
`creative_pivot_added` before acting on them. Creativity changes the next test;
it does not weaken scope, evidence, or verdict rules.

## Daily Loop

```text
map new surface
read one source file fully when source exists
link file -> route -> handler -> service -> data store -> endpoint
update multi-angle endpoint coverage
review dashboard gaps
run risk-prioritize when endpoint count is large
run domain-plan/domain-verify when target has WP, on-prem, or mobile depth
pick highest-value active loop or P0/P1 endpoint
test one bug class or one endpoint angle
save evidence
run evidence-score and judge
set verdict
create pivot or close loop
handoff next action
```

## Endpoint Coverage Definition

An endpoint is not covered just because one request or one payload was tried.

Endpoint coverage requires a multi-angle matrix:

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

Every applicable angle must be:

```text
planned -> tested -> evidence/verdict
```

or explicitly closed as:

```text
not_applicable | blocked | out_of_scope | by_design | inconclusive
```

## Source Coverage Definition

When source exists, source coverage means:

```text
file read fully
file purpose restated
entrypoints extracted
trust boundaries extracted
routes/endpoints linked
data flow linked
sinks/sources identified
new attack surface mapped
endpoint angles planned
chaining opportunities recorded
```

Do not move to the next file until this is written into `source-reviews/`.

## Evidence Judge Definition

The dashboard shows state; it does not decide reportability by itself.

Before drafting a report, run:

```bash
../../../bin/bbf evidence-score --test-id <test-id>
../../../bin/bbf judge --test-id <test-id>
```

Only `judge_reportable` means the evidence package has baseline, mutation,
negative control, read-back, saved files, and coherent verdict state. Other
judge states must stay as candidate, blocked, rejected, or needs-evidence.

## Risk Priority Definition

When endpoint count is large, do not choose the next target from chat memory.
Run:

```bash
../../../bin/bbf risk-prioritize --limit 25
```

The next target should come from `priority-testing-plan.md` and the dashboard
P0/P1 queue unless there is a clear scope/safety reason to override it.

## Domain Depth Definition

When target surface is WordPress, on-prem/source product, or mobile app, run:

```bash
../../../bin/bbf wp-plan
../../../bin/bbf onprem-plan
../../../bin/bbf mobile-plan
../../../bin/bbf domain-verify --domain all
```

Domain depth means the specialized workflow has visible checks:

```text
domain_profile_loaded
domain_check_planned
domain_check_completed
domain_depth_reviewed
```

WP depth requires platform routing, hook/REST inventory, nonce/capability,
sanitizer context, SQL/data layer, upload/URL handling, options/usermeta writes,
and local WP lab PoC.

On-prem depth requires target-intel, sandbox install, source/current extraction,
ranked one-file triad, config/defaults, auth/session model, admin API/service
surface, file/import/export/command surfaces, diff review, and lab proof.

Mobile depth requires app inventory, device proxy capture, decompile/static
inventory, mobile-only API diff, token storage, deeplinks/exported components,
WebView bridge, local data review, scoped runtime instrumentation proof, and
mobile evidence package.

Domain depth is still not a verdict. It only says the right specialized gates
were covered before normal evidence-score and judge.

## File Memory Beats Chat Memory

Every important decision must land in:

- `data/events.jsonl`
- `notes/recent-state.md`
- `notes/loop/queue.md`
- `notes/loop/log.md`
- `coverage-matrix.md`
- `test-ledger.md`
- `multi-angle-coverage.md`
- `priority-testing-plan.md`
- `domain-depth/<domain>-plan.md`
- `domain-depth/<domain>-review.md`
- `evidence/judgements/<judge-id>.md`
- `source-file-queue.md`
- `source-reviews/<file-id>.md`
