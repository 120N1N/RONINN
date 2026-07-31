# Angle Executor

`bbf angle-exec` executes queued endpoint angles and writes runtime evidence.

It is intentionally conservative:

- active traffic requires `--allow-active`
- non-safe methods require `--allow-state-change`
- Burp/Caido traffic is sent through a configured proxy
- automatic verdicts are never `confirmed`
- request/response evidence is saved before `endpoint_angle_tested`

## Basic Flow

```bash
cd engagements/<program>/<target>

../../../bin/bbf angle-plan full \
  --asset-id asset-api \
  --endpoint-id ep-user \
  --method GET \
  --path /api/users/123

../../../bin/bbf angle-exec \
  --transport burp \
  --proxy http://127.0.0.1:8080 \
  --base-url https://target.example \
  --endpoint-id ep-user \
  --angle authn_session \
  --header "Authorization: Bearer REDACTED" \
  --allow-active
```

## Transports

```text
http     direct HTTP execution
burp     HTTP execution through Burp proxy
caido    HTTP execution through Caido proxy
browser  Playwright browser execution if Playwright is installed
```

Burp and Caido default to:

```text
http://127.0.0.1:8080
```

Use `--proxy` if your listener uses a different port.

## Evidence Written

```text
evidence/responses/<run-id>-baseline.http.txt
evidence/responses/<run-id>-<variant>.http.txt
evidence/burp/<run-id>-proxy-note.md
evidence/caido/<run-id>-proxy-note.md
evidence/screenshots/<run-id>-baseline.png
test-ledger.md
data/events.jsonl
```

## Events Written

```text
test_started
control_request_sent
payload_attempted
evidence_added
endpoint_angle_tested
verdict_set
```

`verdict_set` is conservative:

```text
tested_secure
finding_candidate
inconclusive
blocked
```

The executor never writes `confirmed`; that still requires manual evidence
review.

After execution, run:

```bash
../../../bin/bbf evidence-score --test-id <test-id>
```

This checks whether the evidence package contains baseline, mutation, negative
control, read-back, and saved evidence files.

## Role, Object, And Tenant Tests

For role comparison:

```bash
../../../bin/bbf angle-exec \
  --transport burp \
  --base-url https://target.example \
  --endpoint-id ep-admin-export \
  --angle authz_role \
  --headers-file headers-admin.json \
  --alt-headers-file headers-member.json \
  --allow-active
```

For owned object or tenant comparison:

```bash
../../../bin/bbf angle-exec \
  --transport burp \
  --base-url https://target.example \
  --endpoint-id ep-user \
  --angle object_tenant_boundary \
  --headers-file headers-account-a.json \
  --replace user_own_id=user_other_owned_id \
  --allow-active
```

Only use owned accounts and in-scope objects.

## State-Changing Requests

POST, PUT, PATCH, DELETE, and similar methods are blocked unless explicitly
allowed:

```bash
../../../bin/bbf angle-exec \
  --transport caido \
  --base-url https://target.example \
  --endpoint-id ep-update-profile \
  --angle client_trust_integrity \
  --method PATCH \
  --path /api/profile \
  --body '{"displayName":"bbf-test"}' \
  --allow-active \
  --allow-state-change
```

Use this only when the program rules allow active state-changing tests.
