# OWASP A01-A10 And API Top 10 Coverage

Use this as the baseline map. It does not replace creative exploration or
target-specific scenarios.

## Web / App A01-A10 Baseline

| Category | Surface | Status | Evidence/Event | Creative Lead | Next Action |
|---|---|---|---|---|---|
| A01 Broken Access Control | actor/role/object/tenant/state/route | queued | - | - | plan endpoint angles |
| A02 Security Misconfiguration | service/config/env/CORS/debug/admin | queued | - | - | map exposure |
| A03 Supply Chain | dependency/CI/artifact/registry/CDN | queued | - | - | review manifests |
| A04 Cryptographic Failures | token/signature/secret/JWT/signed URL | queued | - | - | map token binding |
| A05 Injection | SQL/NoSQL/OS/template/XML/parser sinks | queued | - | - | link input to sink |
| A06 Insecure Design | business invariant/workflow abuse | queued | - | - | model normal flow |
| A07 Authentication Failures | login/session/MFA/OAuth/reset/logout | queued | - | - | map auth lifecycle |
| A08 Integrity Failures | client state/webhook/import/update/replay | queued | - | - | test tamper/replay |
| A09 Logging/Alerting Failures | audit/log/security events/sensitive logs | queued | - | - | safe audit check |
| A10 Exceptional Conditions | malformed/timeout/rollback/fail-open | queued | - | - | test error paths |

## OWASP API Top 10 2023

| Category | Surface | Status | Evidence/Event | Creative Lead | Next Action |
|---|---|---|---|---|---|
| API1 BOLA | object-level authorization | queued | - | - | A/B object tests |
| API2 Broken Authentication | auth/session/token/MFA | queued | - | - | auth lifecycle tests |
| API3 BOPLA | mass assignment/excessive data/field auth | queued | - | - | field mutation tests |
| API4 Resource Consumption | rate/batch/pagination/upload/cost | queued | - | - | safe cost tests |
| API5 BFLA | function/admin/role authorization | queued | - | - | role/method tests |
| API6 Business Flows | sensitive workflow abuse | queued | - | - | state machine tests |
| API7 SSRF | URL fetch/protocol/internal service | queued | - | - | controlled callback |
| API8 Misconfiguration | CORS/errors/methods/default config | queued | - | - | config exposure tests |
| API9 Inventory | shadow/deprecated/versioned APIs | queued | - | - | runtime/source diff |
| API10 Unsafe API Consumption | third-party trust/external input | queued | - | - | trust boundary tests |

Generate cards:

```bash
../../../bin/bbf owasp-plan web --endpoint-id ep-example --asset-id asset-api
../../../bin/bbf owasp-plan api --endpoint-id ep-example --asset-id asset-api
../../../bin/bbf owasp-plan both --endpoint-id ep-example --asset-id asset-api
```
