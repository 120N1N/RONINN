# Recon To Checklist Workflow

## Input

| Input | Contoh |
|---|---|
| Scope | domain, mobile app, API, excluded path |
| Recon | live hosts, URLs, JS, tech, dorks |
| Auth | roles, tenants, test accounts |
| Traffic | Caido/Burp HTTP history summary |
| Docs | API docs, GraphQL schema, mobile routes |

## Flow

```text
scope snapshot
-> recon import
-> asset graph
-> endpoint and workflow grouping
-> source refs from source material and coverage matrix
-> A01-A10 baseline queue
-> creative/off-checklist leads
-> manual test-card
-> browser + Caido/Burp validation
-> evidence index
-> findings tracker
-> report/retest
```

## Checklist Conversion

| Recon signal | Checklist action |
|---|---|
| Endpoint with object ID | A01 object binding test |
| Admin route in JS | A01/A02 role and exposure test |
| GraphQL operation | A01/A05/A07 alternate workflow test |
| Export/import route | A01/A05/A06/A08 data flow test |
| Webhook | A04/A08 signature and replay test |
| Cache headers | A01/A02/A10 cache state test |
| OAuth route | A04/A07/A10 parser and token test |
| Async job | A06/A08/A10 side-effect test |

Every checklist row must include `source_refs`, `tested_status`, and evidence needed. Do not mark a row `tested_secure`, `finding_candidate`, or `confirmed` without evidence refs.

## Session Closeout

Always record:

- source-grounded baseline coverage update;
- creative/off-checklist leads;
- untested high-value surfaces;
- blocked tests and why;
- evidence refs;
- source refs used;
- coverage ledger updates;
- next manual actions.
