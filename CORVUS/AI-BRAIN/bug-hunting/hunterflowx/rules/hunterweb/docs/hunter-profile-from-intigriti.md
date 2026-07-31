# Hunter Profile From Intigriti Reports

Date: 2026-04-29

Source: read-only review of the Intigriti researcher submissions API. This file
stores high-level strategy signal only. It intentionally does not include
session cookies or full private report bodies.

## Portfolio Snapshot

- Total submissions observed: 129
- Submissions with nonzero listed bounty: 116
- Total listed bounty: 152,627 across mixed currencies as represented by the
  platform response
- Current/open accepted-or-pending items: 22 with no close reason
- Closed/archived outcomes by Intigriti close reason:
  - Resolved: 16
  - Duplicate: 30
  - Accepted risk: 3
  - Informative: 47
  - Out of scope: 4
  - Not applicable: 7

Top programs by volume and listed bounty:

| Program | Count | Listed bounty |
|---|---:|---:|
| DigitalOcean | 49 | 34,781 |
| Splunk Private Bug Bounty Program | 28 | 94,500 |
| Cloudways by DigitalOcean | 12 | 7,078 |
| Signicat | 7 | 4,700 |
| Salto CloudWorks | 6 | 794 |
| Odoo 19.0 Bug Bounty program | 4 | 4,000 |

## Strongest Personal Patterns

The highest-signal pattern is not generic scanning. It is role/tenant/state
confusion in complex SaaS and platform products.

Recurring winning classes:

- Broken access control, IDOR, BOLA, and privilege escalation
- Unauthorized state-changing API actions
- Cross-tenant or cross-team resource manipulation
- Low-privileged user reaching admin-like object operations
- Business logic bypasses around limits, workflow state, and UI/backend mismatch
- Chained RCE where a lower role can control data consumed by a privileged or
  unsafe server-side mechanism
- SSRF and deserialization only when they are tied to a concrete product feature
  and an end-to-end proof

Rough title-based overlapping classification:

| Class | Count | Listed bounty |
|---|---:|---:|
| Authz / IDOR / privilege / tenant | 67 | 75,261 |
| Unauthorized state change | 48 | 44,634 |
| Business logic / bypass | 27 | 32,221 |
| RCE chain / deserialization / SSTI / sandbox | 11 | 23,800 |
| Info leak / credential / password / sensitive data | 9 | 18,584 |
| SSRF | 2 | 8,000 |
| Race condition | 1 | 1,390 |

Categories overlap; this is meant as hunting signal, not accounting.

## Report Traits That Worked

High-value accepted reports tend to include:

- Exact vulnerable endpoint or component.
- Exact role/permission precondition.
- Concrete request mutation, usually a changed ID, role, tenant, object, or
  unexpected extra parameter.
- Clear before/after verification.
- Impact stated as a real boundary crossing, not generic severity language.
- For RCE-class issues, a complete chain from realistic low privilege to code
  execution, with exact affected version and component.
- Explicit policy eligibility arguments when the bug might be mistaken for a
  configuration issue, third-party-library issue, or high-privilege-only issue.

The strongest example pattern observed:

```text
low-priv reachability
  -> writable product data/control plane object
  -> validator or authorization bypass
  -> privileged consumer or unsafe sink
  -> self-triggerable proof
  -> exact version/component/root-cause explanation
```

## Strategy Implications

The autonomous agent should be biased toward your proven edge:

1. Prioritize complex control planes over simple marketing/web surfaces.
   Best targets are SaaS dashboards, cloud consoles, developer platforms,
   security products, ERP/admin systems, API-heavy products, and products with
   roles, teams, tenants, resources, and asynchronous workers.

2. Make role/tenant diffing the default first move.
   Your historical returns are dominated by changed object IDs, cross-team
   operations, direct GraphQL/API mutations, and mismatches between UI permission
   checks and backend enforcement.

3. Treat every state-changing endpoint as a candidate.
   Create, delete, transfer, reset, clone, assign, rebuild, overwrite, restore,
   invite, revoke, and update operations appear repeatedly in successful titles.

4. Chain upward instead of stopping at medium.
   Sensitive information exposure is most valuable when it becomes credential
   exposure, admin action, tenant compromise, or RCE.

5. Use source/code analysis only when it can explain or escalate live behavior.
   This matches both the Splunk skill and the winning report pattern.

6. Improve duplicate avoidance.
   The portfolio has many paid/accepted findings, but duplicate and informative
   volume is also high. The agent should do stronger novelty checks before
   investing deeply in a lead.

## Revised MVP Priority

The MVP should be:

> A multi-account, multi-role, multi-tenant state-change and authorization
> testing harness for API-heavy SaaS control planes, with workflow replay,
> object graphing, role diffing, mutation side-effect verification, and chain
> escalation.

This is more precise than a general Web2 scanner and better aligned with the
observed bounty history.

