# Evidence Quality Scorer

`bbf evidence-score` reviews executed tests and scores whether the evidence is
strong enough to support a verdict.

It checks for:

- baseline request
- baseline evidence file
- mutated or variant request
- mutated or variant evidence file
- negative control
- negative control evidence
- read-back, browser state, or response diff
- `endpoint_angle_tested`
- non-empty evidence files
- Burp, Caido, or browser-visible context
- verdict event
- possible unredacted secret-bearing evidence

## Basic Usage

```bash
cd engagements/<program>/<target>

../../../bin/bbf evidence-score --test-id test-angle-ep-user-authn_session-abcd1234
```

Score all tests in an endpoint:

```bash
../../../bin/bbf evidence-score --endpoint-id ep-user --all
```

Score one angle:

```bash
../../../bin/bbf evidence-score --endpoint-id ep-user --angle authn_session
```

## Grades

```text
evidence_sufficient
evidence_partial
evidence_incomplete
```

The default sufficient threshold is `75`, but read-back is mandatory for
`evidence_sufficient`. Without read-back, the scorer will keep the result at
partial even if the numeric score is high.

## Outputs

```text
evidence/reviews/review-<test-id>.md
data/events.jsonl       # evidence_reviewed
data/graph_state.json
dashboard metrics
```

Dashboard metrics added:

```text
evidence_quality_sufficient
evidence_quality_partial
evidence_quality_incomplete
evidence_quality_avg
```

## Example Flow

```bash
../../../bin/bbf angle-plan full --endpoint-id ep-user --asset-id asset-api --method GET --path /api/users/123

../../../bin/bbf angle-exec \
  --transport burp \
  --base-url https://target.example \
  --endpoint-id ep-user \
  --angle object_tenant_boundary \
  --headers-file headers-account-a.json \
  --replace user_a_id=user_b_owned_id \
  --readback-url https://target.example/api/users/user_b_owned_id \
  --allow-active

../../../bin/bbf evidence-score --endpoint-id ep-user --angle object_tenant_boundary
```

`confirmed` is still manual. A high score means the evidence package is
complete enough to review, not that the finding is automatically valid.
