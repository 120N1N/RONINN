# Recursive Hunting Loop

The loop is:

```text
recon -> analyze -> expand -> retest -> repeat
```

The dashboard must make this visible.

## Loop Inputs

| Input | Next Work |
|---|---|
| endpoint | role check, parameter tests, attack path |
| parameter | bug-class-specific payload/control |
| JS file | hidden route, API client, feature flag |
| fingerprint | payload strategy adjustment |
| response anomaly | focused retest |
| Burp request | replay baseline and mutation point |
| dead end | pivot, blocker, retest, or close |

## Dead End Handling

Every dead end must be classified:

```text
wrong_role
missing_second_account
missing_csrf_or_state
wrong_payload_family
fingerprint_changed_strategy
endpoint_unreachable
scope_unclear
control_successfully_negative
```

Then one decision is required:

```text
pivot_decision
strategy_adjusted
retest_scheduled
gap_found
verdict_set = tested_secure
```

## Pivot Types

```text
endpoint_pivot
js_pivot
role_pivot
fingerprint_pivot
param_pivot
state_pivot
impact_pivot
scope_pivot
```

## Closure Rules

A loop can close only when:

- confirmed impact exists, or
- tested secure has adequate controls, or
- blocked has concrete needed action, or
- out of scope is supported by program policy, or
- by design is supported by target docs/rules.

