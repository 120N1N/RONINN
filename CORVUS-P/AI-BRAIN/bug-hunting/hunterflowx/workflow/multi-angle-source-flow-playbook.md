# Multi-Angle Source Flow Playbook

Use this when an engagement has endpoints, JavaScript, PHP, Python, source
archives, config files, route files, controllers, models, templates, or any
other file that can explain how the target works.

## Prime Rule

The AI must understand flow before claiming coverage.

```text
source file -> route/entrypoint -> handler -> service -> data store/external call
-> endpoint -> role/session/object boundary -> multi-angle test -> evidence -> verdict
```

If the link is not known, the correct output is `gap_found`, `blocked`, or
`inconclusive`, not a confident conclusion.

## Creative Exploration Lane

This playbook is mandatory, but it must not make AI rigid.

Use the workflow as a safety and evidence system. Inside that system, AI should
actively explore:

- weird source/runtime differences
- unusual trust boundaries
- hidden frontend flows
- uncommon bug classes
- cross-feature behavior
- business logic shortcuts
- chain paths that combine small primitives
- payload variants tailored to the actual parser, framework, and data flow

Creative exploration must be labeled clearly:

```text
creative_hypothesis_added
creative_pivot_added
chain_candidate_added
attack_path_expanded
```

The idea can be wild; the execution must be safe. A creative hypothesis is not a
finding until it becomes evidence-backed.

## One File At A Time

For each file:

1. Queue the file with `source_file_queued`.
2. Read the whole file.
3. Write `source-reviews/<file-id>.md`.
4. Record `source_file_read`.
5. Link flows with `source_flow_linked`.
6. Map new attack surface with `attack_surface_mapped`.
7. Create endpoint angle tests with `endpoint_angle_planned`.
8. Record unusual hypotheses with `creative_hypothesis_added` when relevant.
9. Record chaining leads with `chain_candidate_added`.
10. Only then move to the next file.

Do not jump between files because a grep result looked interesting. Grep can
prioritize files, but it does not replace full per-file review.

For important endpoints, use the executable helper instead of writing the whole
matrix manually:

```bash
../../../bin/bbf angle-plan full --endpoint-id <endpoint-id> --asset-id <asset-id> --method <METHOD> --path <PATH>
```

This queues 22 endpoint angles and 10 creative hypotheses. If the dashboard
still shows `planned_angles = 0`, the endpoint has not been multi-angle planned.
After planning, use `bbf angle-exec` to run safe runtime validation and write
`endpoint_angle_tested`:

```bash
../../../bin/bbf angle-exec --transport burp --base-url <base-url> --endpoint-id <endpoint-id> --angle <angle> --allow-active
```
Then score the evidence package:

```bash
../../../bin/bbf evidence-score --endpoint-id <endpoint-id> --angle <angle>
```

After reviewing source files, verify the source coverage state:

```bash
../../../bin/bbf source-verify --source-root <extracted-source-root> --queue-missing
```

Use `--all` when the engagement requires every source-like file to be accounted
for. The verifier records `source_completeness_reviewed` and updates dashboard
metrics so missed files are visible instead of hidden in chat context.

When many endpoints are mapped, rank the next testing queue:

```bash
../../../bin/bbf risk-prioritize --limit 25
```

This reads endpoint/source/angle/evidence/verdict events and writes
`endpoint_prioritized` plus `risk_prioritization_reviewed`. Use the resulting
P0/P1 endpoints as the next `angle-plan` or `angle-exec` targets.

## What To Extract Per File

Minimum extraction:

- file purpose
- framework/language
- entrypoints
- routes/endpoints
- request methods
- params/query/body/header/cookie fields
- authn/session assumptions
- authz/role/tenant/object checks
- state transitions
- database/file/cache/external service calls
- error handling
- dangerous sinks
- trusted sources
- frontend calls and hidden routes
- new attack surface
- chaining candidates

## Endpoint Multi-Angle Matrix

For every endpoint, plan or close each relevant angle:

| Angle | Question |
|---|---|
| `authn_session` | Can unauth/fake/expired/low-session reach different code? |
| `authz_role` | Can a lower role use higher-role action or data? |
| `object_tenant_boundary` | Can account A access account B, tenant B, org B, or object B? |
| `input_validation` | Do path/query/body/header/cookie inputs reach parser/query/sink? |
| `state_transition` | Can steps be skipped, replayed, reordered, or partially completed? |
| `business_logic` | Can price, quota, approval, ownership, invite, refund, or workflow rules be bypassed? |
| `data_exposure` | Does the response reveal private, non-public, or privileged data? |
| `side_effect_write` | Does a write persist and can it be read back independently? |
| `rate_limit_or_race` | Can concurrency or request volume change the result? |
| `cache_cors_redirect` | Does cache, CORS, redirect, or origin behavior create impact? |
| `file_or_url_handling` | Does upload, download, import, webhook, preview, or URL fetch cross a boundary? |
| `error_oracle` | Do errors reveal valid IDs, internal service paths, users, roles, or query behavior? |
| `source_runtime_diff` | Does runtime behavior contradict source or docs? |
| `chain_potential` | What capability does this give, and what can it unlock next? |

An endpoint is meaningfully covered only when every applicable angle has one of:

```text
endpoint_angle_tested
verdict_set = tested_secure
verdict_set = finding_candidate
verdict_set = confirmed
blocked
out_of_scope
by_design
inconclusive
gap_found
```

## Chaining Method

When any primitive is found, map capability first:

| Primitive | Capability | Common Next Link |
|---|---|---|
| IDOR read | private data | token leak, PII exfil, account takeover |
| IDOR write | state change | privilege change, destructive action, workflow bypass |
| XSS | JS execution | token theft, CSRF-like action, postMessage, OAuth code theft |
| Open redirect | URL control | OAuth code theft, phishing only if accepted by scope |
| SSRF | server-side fetch | internal service access, cloud metadata, IP allowlist bypass |
| File upload | stored file | stored XSS, parser bug, path traversal, RCE if allowed |
| Info disclosure | secret/config | API access, source map route discovery, cloud/storage access |
| Race | duplicate state | quota bypass, coupon reuse, payment/refund abuse |
| GraphQL field leak | resolver gap | nested object pivot, mutation auth bypass |

Record the chain as `chain_candidate_added` or `attack_path_expanded`. Do not
report weak primitives until impact is complete or the program accepts that
class alone.

## Stop Rules

Stop and record a gap when:

- source file is unreadable or generated/minified and cannot be safely reviewed
- endpoint exists in source but not runtime
- runtime endpoint exists but source route is missing
- role/session/object ownership cannot be established
- test accounts are missing
- proof would require forbidden destructive action
- rate limit or scope boundary is unclear

## Completion Checklist

Before saying a source-backed target is mapped:

- all prioritized source files have `source-reviews/` artifacts
- source files are linked to endpoints or marked not runtime-relevant
- `bbf source-verify` has no `source_incomplete` files for the selected source root
- endpoint multi-angle matrix is updated
- risk queue is refreshed with `bbf risk-prioritize` when there are many endpoints
- attack surface from source is reflected in events
- dashboard shows planned/tested/gap state
- chaining candidates are recorded or explicitly absent
- no verdict is based on source reading alone
