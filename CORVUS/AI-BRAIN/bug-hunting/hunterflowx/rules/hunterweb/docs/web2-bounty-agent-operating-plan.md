# Web2 Bounty Agent Operating Plan

Date: 2026-04-29

This plan defines the operating model for an authorized Web2 bug bounty agent in
`/home/hunterweb`. It is based on current public bounty/vulnerability trend data,
the local Splunk hunting skill at `claude/splunk-hunt-skill.md`, the local CTBB
novelty-pattern corpus at `ctbb_novelty_patterns.md`, the Intigriti hunter
profile at `docs/hunter-profile-from-intigriti.md`, the workflow references
provided by the user, the operator prompts at `docs/operator-prompts.md`, and
the existing target workspace conventions under `bounty/<program>/<target>/`.

## Positioning

The agent must not become an agentic vulnerability scanner. Scanner-shaped
systems enumerate many payloads and produce many weak claims. This agent should
optimize for proven security-boundary crossings, chain construction, and
reportable impact inside explicit bounty scope.

The first product wedge is authorization, state-change abuse, and business logic
because both public trend data and the user's own bounty history support it:
OWASP Top 10:2025 keeps Broken Access Control at A01, OWASP API Security Top
10:2023 has authorization-heavy risks in three of its top five, Bugcrowd 2025
reported growth in critical broken access control and sensitive data exposure,
and the Intigriti history is dominated by authz/IDOR/privilege/tenant findings,
unauthorized state changes, and business logic bypasses. The difference from a
scanner is the method: live weirdness first, source/static analysis second, proof
and escalation before reporting.

## Non-Negotiable Rules

- Only run against explicitly authorized in-scope assets.
- Enforce program-specific headers, user-agent tags, account restrictions, and
  rate limits before every request.
- Use only owned test accounts and clearly public/demo data.
- Do not perform destructive actions, persistence, spam, takeover, mass
  enumeration, billing-affecting operations, or production-instability tests
  without explicit user approval and program permission.
- Do not submit theoretical reports. Every report needs reproducible evidence
  against a live authorized system or a local vendor-authorized lab build.
- POC or GTFO: without a working proof, the issue remains a lead or primitive,
  not a finding.
- Treat known CVEs and disclosed reports as pattern references, not submissions.
- Keep all meaningful observations on disk. Session compaction and context loss
  are expected failure modes; durable notes are part of the harness.

## Core Doctrine Imported From The Splunk Skill

The transferable value from the Splunk skill is methodology, not Splunk-specific
facts.

1. Start outside-in.
   Interact with the live target as unauthenticated, low-privileged, second
   tenant, and higher-role test users before reading code or running broad
   pattern searches.

2. Live observation outranks static hypothesis.
   A 200 where 403 is expected, a 500 with a stack trace, a role-specific
   response difference, unexpected reflection, timing anomaly, or controllable
   redirect is more valuable than a grep hit.

3. Maintain a weirdness journal.
   `notes/loop/queue.md` is not a payload checklist. It is a queue of observed
   anomalies with endpoint, account, request, response, expected behavior, and
   next escalation step.

4. Use static analysis as targeted explanation.
   Read source, JS bundles, OpenAPI specs, GraphQL schemas, or decompiled code
   after live behavior identifies a promising path. Static work explains and
   escalates weirdness.

5. Chain primitives.
   A weak primitive should be tested for whether it unlocks a stronger primitive:
   token leak, internal request, cross-tenant object access, privileged workflow,
   file write, template rendering, OAuth flow abuse, webhook callback, or admin
   action.

6. Reachability is mandatory.
   If the realistic starting role cannot reach the affected behavior, it is not a
   bounty finding. Record it as a hardening note at most.

7. Report facts, not forecasts.
   Findings should say what was probed, what the target returned, what boundary
   was crossed, and what impact was demonstrated.

8. Promote evidence through stages.
   Raw notes, leads, primitives, findings, and reports are separate maturity
   levels. Moving forward requires evidence; moving backward is normal when a
   hypothesis fails.

## Six-Step Finding Gate

Every reportable issue must pass all six gates:

1. Observe weirdness.
   Capture the live request, account/role, endpoint, expected behavior, actual
   behavior, and why the delta matters.

2. Reproduce and control.
   Show the behavior is deterministic and attacker-controlled. If the input
   cannot influence the output, state, target object, callback, or authorization
   result, it is not ready.

3. Understand the mechanism.
   Use code, traffic, schema, docs, or differential testing to identify the root
   cause. Avoid naming a class before the mechanism is understood.

4. Escalate to the ceiling.
   Test whether the primitive chains to account takeover, cross-tenant access,
   privileged action, sensitive data exposure, SSRF with meaningful reachability,
   stored XSS with privileged impact, or safe command execution in a local lab.

5. Build minimal proof.
   Create a reproducible PoC using owned accounts and minimal data. Capture
   screenshots, raw requests, responses, callback evidence, and state changes.

6. Prove novelty and policy fit.
   Check program exclusions, known reports, disclosed CVEs, local notes, and
   bounty policy. Do not submit duplicates, N/A classes, or policy-prohibited
   tests.

## Runtime Loop

For each authorized target:

1. Ingest rules into `notes/rules.md`.
2. Create or refresh durable session notes before probing.
3. Build or verify request wrappers that enforce headers, tags, auth files, and
   rate limits.
4. Map unauthenticated, account A, account B, tenant A admin/member, tenant B,
   and any program-specific role.
5. Crawl manually and with browser automation while capturing traffic.
6. Convert observed endpoints into an object/role/tenant graph.
7. Run reachability and response-diff probes across accounts.
8. Add anomalies to `leads/` or `notes/loop/queue.md`.
9. Promote reproducible controllable behavior into `primitives/`.
10. Pick the highest-impact primitive and investigate mechanism.
11. Attempt escalation and chaining before writing any report.
12. Promote only six-gate issues into `findings/`.
13. Draft concise, technical reports in `reports/`, then proofread by following
    the reproduction steps.

## Data Model

The agent needs these first-class objects:

- Program: scope, policy, platform, payout model, exclusions, required headers.
- Asset: host, app, API base, auth surface, owner, source of authorization.
- Account: identity, tenant, role, auth material, allowed actions.
- Endpoint: method, URL, parameters, body schema, auth requirement, role reach.
- Object: IDs, owners, tenant, visibility, lifecycle, related endpoints.
- Observation: request, response, account, expected result, actual result.
- Primitive: controllable read, write, redirect, callback, reflection, authz gap.
- Chain: ordered primitives, start role, final impact, proof status.
- Finding: reportable issue after the six-step gate.

## Evidence Promotion Pipeline

Use this hierarchy for every target:

```text
notes/       raw observations, session log, recon, rules, queue
leads/       interesting anomalies that need reproduction
primitives/  reproducible controllable behavior with a plausible security use
findings/    six-gate issues with demonstrated impact and novelty checks
reports/     concise final drafts with exact reproduction steps
```

Promotion rules:

- `notes -> leads`: the live target did something unexpected.
- `leads -> primitives`: the behavior is reproducible and attacker-controlled.
- `primitives -> findings`: the primitive crosses or chains to a security
  boundary with owned-account proof.
- `findings -> reports`: the writeup is concise, policy-fit, deduped, and
  manually proofread by following the repro.

Demotion rules:

- If a lead is not reproducible, move it back to notes with the failed attempts.
- If a primitive cannot reach meaningful impact, keep it as chain material, not a
  finding.
- If a finding cannot survive policy or duplicate review, do not report it.

## Hunt Modules

### Authorization, Tenant Isolation, And State Change

This is the MVP module.

- Replay account A object requests with account B.
- Replay tenant admin actions as tenant member.
- Test `/users/me`, namespace, org, team, project, file, billing, and invite IDs.
- Prioritize state-changing verbs and actions: create, delete, transfer, reset,
  clone, assign, rebuild, overwrite, restore, invite, revoke, and update.
- Diff not only status codes but object ownership, hidden fields, side effects,
  and mutation results.
- Treat 200, 204, partial object leakage, different 403 body, timing deltas, and
  silent side effects as leads.

### Business Logic

Model workflows as state machines:

- invite accept/revoke
- email change
- password reset
- MFA enrollment/removal
- OAuth connect/disconnect
- billing, coupons, credits, refunds
- file sharing and permission changes
- exports/imports
- webhooks
- admin approvals

Probe out-of-order transitions, replayed tokens, stale permissions, role changes
mid-flow, and cross-tenant object substitution.

### Client And Browser Logic

Use the CTBB novelty corpus to avoid scanner thinking:

- normalization desync: browser/router/framework/backend path differences
- parser differential: MIME, URL, header, multipart, and JSON parser mismatches
- predictable identifier: static popup/window names, postMessage channels, OAuth
  windows, shared worker names
- gadget chains: implicit coercion, template engines, expression evaluators
- state-machine races: redirect stopping, OAuth code persistence, workflow races
- trust-boundary crossings: static assets, CSP gaps, postMessage, iframe behavior

### API And Schema Intelligence

- Extract OpenAPI, GraphQL, gRPC-web, tRPC, and JS-discovered API routes.
- Build parameter and object dictionaries from live traffic.
- Compare documented schema with actual accepted fields.
- Test object-property authorization and mass assignment by adding fields from
  higher-privileged responses into lower-privileged writes.
- For GraphQL, map operations, variables, fragments, batching, aliases, and
  resolver-level auth behavior.

### Callback And SSRF

Only where policy allows:

- Prefer callbacks to controlled OAST domains over internal resource access.
- Validate with benign URLs and metadata-free endpoints.
- Escalate only if program permits and the proof can avoid sensitive data.

### AI Feature Surface

Only when AI features are explicitly in scope:

- Prompt injection with concrete unauthorized action or data exposure.
- RAG cross-tenant leakage.
- Tool/plugin misuse.
- Connector authorization confusion.
- Stored indirect prompt injection in shared objects.

## Anti-Slop Controls

Reports are blocked when they contain:

- a theoretical sink without live reachability
- no owned-account reproduction
- no security boundary crossed
- scanner-only output
- generic missing headers, clickjacking, self-XSS, low-impact rate limits, or
  other common policy exclusions
- uncontrolled real-user data access
- unverified AI-generated reasoning
- known CVE reproduction without a new affected version/surface

The agent should prefer fewer stronger findings over many weak submissions.

## MVP Build Order

1. Request wrappers and policy gate.
2. Notes/leads/primitives/findings/reports schema and templates.
3. Browser traffic capture and endpoint normalization.
4. Multi-account replay and role/tenant diff engine.
5. State-changing endpoint discovery and side-effect verification.
6. Object graph builder.
7. Six-step finding gate implementation.
8. Concise report generator with fixed fields and repro-proofread checklist.
9. Central lead and primitive sink so work survives context resets and multiple
   agent entry points.
10. Business-logic state-machine harness.
11. Caido integration or Caido skill support if Caido becomes the active proxy
   and manual SDK work would slow hunts.
12. Client-side novelty probes from the CTBB corpus.
13. AI-feature module for programs where this is in scope.

## Immediate Workspace Standard

Every active target should contain:

```text
bounty/<program>/<target>/
  notes/rules.md
  notes/recon.md
  notes/loop/queue.md
  notes/loop/log.md
  leads/
  primitives/
  findings/
  reports/
  output/
  scripts/req.sh
  scripts/api.sh
  acct2/
```

`queue.md` should track observed weirdness, not generic payload ideas. `log.md`
should track what was actually tried and what the live target did. `leads/`
stores anomalies, `primitives/` stores reproduced controllable behaviors,
`findings/` stores six-gate issues, and `reports/` stores final concise drafts.

## Sub-Agent And Skill Governance

- Default cap: 2-3 sub-agents total per hunt.
- Use sub-agents only for independent work whose output can be written back into
  durable notes.
- Do not let sub-agents become the memory layer; files are the memory layer.
- Use a central lead/primitive sink when multiple entry points exist, such as
  local agents, Caido, browser automation, or a Discord bot.
- Install or create skills only for knowledge that is not reliably in model
  training data: Caido SDK usage, local VPS/tooling, credentials, program rules,
  private target workflows, and recent techniques from posts or talks.
- For common web classes, try the base workflow first and use custom skills only
  as extra knowledge.
