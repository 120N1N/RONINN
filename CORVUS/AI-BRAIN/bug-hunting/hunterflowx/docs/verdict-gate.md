# Verdict Gate

## Statuses

| Status | Meaning |
|---|---|
| `not_tested` | no test exists |
| `mapped_only` | mapped, not tested |
| `test_attempted` | started but not resolved |
| `inconclusive` | test ran but evidence/control insufficient |
| `tested_secure` | negative result with adequate controls |
| `finding_candidate` | promising lead, not reportable |
| `confirmed` | impact proven with runtime evidence |
| `out_of_scope` | not eligible under program rules |
| `by_design` | expected target behavior |
| `blocked` | cannot continue without concrete action |

## Promotion Rules

```text
mapped_only -> test_attempted -> inconclusive | tested_secure | finding_candidate
finding_candidate -> confirmed
confirmed -> report draft
```

Never promote:

```text
source-only -> confirmed
scanner-only -> confirmed
AI-confidence -> confirmed
```

## Confirmed Finding Requirements

Required:

- scoped target
- realistic attacker role
- request/response or browser-visible proof
- expected vs actual behavior
- impact under program policy
- no private third-party data dump
- replayable reproduction

## Tested Secure Requirements

Required:

- baseline request
- negative test
- expected vulnerable signal
- actual result
- evidence path
- reason controls are adequate

If any requirement is missing, use `inconclusive`.

