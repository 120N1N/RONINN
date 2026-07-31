# Evidence Judge

Dashboard visibility is not enough. `bbf judge` adds an explicit reportability
judgement layer on top of the existing event graph.

Use it after `bbf evidence-score`:

```bash
cd engagements/<program>/<target>
../../../bin/bbf evidence-score --endpoint-id <endpoint-id> --all
../../../bin/bbf judge --endpoint-id <endpoint-id> --all
```

Or judge one test:

```bash
../../../bin/bbf judge --test-id <test-id>
```

## What It Judges

The judge reads durable events and evidence files. It checks:

| Gate | Required Signal |
|---|---|
| baseline | `control_request_sent` plus baseline evidence |
| mutation | `payload_attempted` plus mutated/variant evidence |
| negative control | denied/blocked alternate case plus evidence |
| read-back | independent server state, browser state, response diff, or read-back evidence |
| saved files | non-empty files under `evidence/` |
| proxy/browser context | Burp, Caido, or browser-visible evidence |
| scorer result | latest `evidence_reviewed` status and score |
| verdict coherence | latest `verdict_set` must match evidence quality |
| redaction | token/cookie/API-key evidence must be redacted |

## Decisions

```text
judge_reportable      evidence is strong enough to draft report
judge_candidate       strong lead, but missing some report-grade proof
judge_needs_evidence  cannot judge reportable yet
judge_blocked         scope/session/gap blocks judgement
judge_rejected        not reportable, out-of-scope/by-design, or unsafe evidence
```

`judge_reportable` still does not submit anything. It means the evidence package
is report-ready enough to draft and manually reproduce one final time if the
program requires it.

## Output

```text
data/judgements.json
evidence/judgements/judge-<test-id>.md
data/events.jsonl       # evidence_judged, judge_reviewed
data/graph_state.json
```

Dashboard metrics:

```text
judge_tests_total
judge_avg_score
judge_reportable
judge_candidate
judge_needs_evidence
judge_blocked
judge_rejected
```

## Operating Rule

Use this flow before report writing:

```text
angle-exec -> evidence-score -> judge -> report draft
```

Do not promote a finding only because the dashboard shows evidence exists.
Promote only when the judge says `judge_reportable`, or explicitly document why
the program accepts a weaker proof package.
