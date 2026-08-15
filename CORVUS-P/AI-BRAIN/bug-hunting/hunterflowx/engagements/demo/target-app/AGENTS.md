# AGENTS.md - Final AI Bug Bounty Workflow

This workflow is for authorized bug bounty work only. The agent must optimize
for auditability, evidence, and repeatable testing, not for chat confidence.

## Prime Contract

Never claim that something was tested, secure, vulnerable, complete, or
confirmed unless the engagement contains durable evidence:

```text
event -> graph -> ledger -> evidence -> verdict
```

Chat is not durable state.

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

## Source Hierarchy

Use the local methodology sources this way:

```text
hunterweb/recon-framework
  policy gate, recursive recon, scope validation, durable workspace

GPTxOPUS
  manual test cards, evidence discipline, source-grounded coverage
```

No external module output can directly become a finding. It must pass this
workflow's evidence and verdict gates.

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

## Event Rules

Every meaningful action must write an event:

- `scope_loaded`
- `asset_added`
- `endpoint_discovered`
- `param_discovered`
- `endpoint_seen_runtime`
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
