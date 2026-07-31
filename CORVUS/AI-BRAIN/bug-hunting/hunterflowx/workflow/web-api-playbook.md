# Web/API Playbook

Use for SaaS, REST, GraphQL, dashboards, and general web bug bounty targets.

## Mapping Sources

- program scope
- Burp sitemap
- browser navigation
- JS bundles
- OpenAPI/Swagger
- GraphQL schema/operations
- mobile/API clients if available
- source route files if whitebox

## Priority Bug Classes

1. IDOR / BOLA / authorization
2. state-changing missing authz
3. mass assignment
4. business logic
5. OAuth/OIDC/SAML
6. GraphQL authz
7. SSRF/callback where allowed
8. stored XSS with impact
9. cache poisoning/deception
10. SQLi only when input-to-query path exists

This list is only the human-priority lens. The required baseline coverage must
still cover Web/App A01-A10 and OWASP API Top 10 when the endpoint or surface is
important enough to test deeply.

## Web/App A01-A10 Baseline

Use `bbf owasp-plan web` for broad web/application coverage, then execute only
the safe and applicable cards:

1. A01 Broken Access Control
2. A02 Security Misconfiguration
3. A03 Software Supply Chain Failures
4. A04 Cryptographic Failures
5. A05 Injection
6. A06 Insecure Design
7. A07 Authentication Failures
8. A08 Software/Data Integrity Failures
9. A09 Security Logging and Alerting Failures
10. A10 Mishandling Exceptional Conditions

## OWASP API Top 10 Baseline

Use `bbf owasp-plan api` for API surfaces:

1. API1 Broken Object Level Authorization
2. API2 Broken Authentication
3. API3 Broken Object Property Level Authorization
4. API4 Unrestricted Resource Consumption
5. API5 Broken Function Level Authorization
6. API6 Unrestricted Access to Sensitive Business Flows
7. API7 Server Side Request Forgery
8. API8 Security Misconfiguration
9. API9 Improper Inventory Management
10. API10 Unsafe Consumption of APIs

Use `bbf owasp-plan both` when the same surface is both web workflow and API
boundary. It automatically queues `bbf angle-plan full` unless skipped. Do not
let A01/BOLA dominate the whole engagement; A01 is one high-priority lane, not
the complete methodology.

## Anti A01-Heavy Guardrail

For important endpoints, the dashboard should show all three:

```text
planned_tests    > 0
planned_angles   > 0
creative_ideas   > 0
```

If `planned_tests` exists but `planned_angles` is `0`, the endpoint only has
test cards, not real multi-angle coverage. Run:

```bash
../../../bin/bbf angle-plan full --endpoint-id <endpoint-id> --asset-id <asset-id> --method <METHOD> --path <PATH>
```

If `planned_angles` exists but `tested_angles` stays `0`, the endpoint has not
been executed. Run a safe executor pass:

```bash
../../../bin/bbf angle-exec --transport burp --base-url <base-url> --endpoint-id <endpoint-id> --angle <angle> --allow-active
```

After execution, evidence quality must be scored:

```bash
../../../bin/bbf evidence-score --endpoint-id <endpoint-id> --angle <angle>
```

Do not treat a candidate as report-ready when the score is
`evidence_partial` or `evidence_incomplete` unless the missing evidence is
explicitly explained in the report draft.

## Required Runtime Tests

- account A vs account B
- tenant A vs tenant B
- user vs admin/member role
- baseline vs mutated object id
- documented schema vs accepted fields
- JS route vs runtime reachability
