# Source File Review

File ID:
Path:
Language/Type:
Reviewer:
Timestamp:

## RESTATE-OK

Restate the file's role in concrete terms before analysis.

-

## FILE-PURPOSE

-

## ENTRYPOINTS

Routes, exported functions, handlers, CLI entrypoints, cron jobs, hooks,
components, or event listeners.

-

## TRUST-BOUNDARIES

Auth/session, role, tenant, object ownership, CSRF, origin, network, file, or
external service boundaries.

-

## ROUTES-ENDPOINTS

| Endpoint ID | Method/Path | Source Line/Function | Runtime Evidence | Status |
|---|---|---|---|---|
| - | - | - | - | - |

## DATA-FLOW

```text
input -> validation -> auth/session -> handler -> service -> model/query/cache/file/external call -> response
```

-

## SINKS-SOURCES

| Type | Name/Location | Risk | Linked Endpoint |
|---|---|---|---|
| source | - | - | - |
| sink | - | - | - |

## AUTHZ-AUTHN

-

## ATTACK-SURFACE

-

## MULTI-ANGLE-PLAN

| Endpoint ID | Angle | Planned Test | Required Evidence | Status |
|---|---|---|---|---|
| - | authn_session | - | - | queued |
| - | authz_role | - | - | queued |
| - | object_tenant_boundary | - | - | queued |
| - | input_validation | - | - | queued |
| - | state_transition | - | - | queued |
| - | business_logic | - | - | queued |
| - | data_exposure | - | - | queued |
| - | side_effect_write | - | - | queued |
| - | rate_limit_or_race | - | - | queued |
| - | cache_cors_redirect | - | - | queued |
| - | file_or_url_handling | - | - | queued |
| - | error_oracle | - | - | queued |
| - | source_runtime_diff | - | - | queued |
| - | chain_potential | - | - | queued |

## CHAIN-CANDIDATES

| Primitive | Capability | Next Link To Test | Event ID |
|---|---|---|---|
| - | - | - | - |

## EVENTS-WRITTEN

-

## OPEN-GAPS

-
