# Multi-Angle Endpoint Coverage

Use one row per endpoint angle. Do not mark an endpoint as covered only because
one payload was tried.

| Endpoint ID | Method/Path | Angle | Status | Evidence/Event | Gap/Next Action |
|---|---|---|---|---|---|

Allowed statuses:

```text
queued
test_attempted
tested_secure
finding_candidate
confirmed
inconclusive
blocked
out_of_scope
by_design
not_applicable
```
