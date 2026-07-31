# Operator Prompts

Date: 2026-04-29

Use these prompts to operate the authorized Web2 bug bounty workflow across
fresh sessions, context clears, and phase handoffs.

For a practical start-to-finish operating manual, see
`docs/bug-bounty-operator-guide.md`. This file is the copy/paste prompt
reference.

Path convention: `$HUNTERWEB_HOME` means the current `hunterweb` workspace root.
Set it before running examples:

```bash
export HUNTERWEB_HOME="${HUNTERWEB_HOME:-$(pwd)}"
```

## Master Prompt

Paste this into a fresh session before running a phase.

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

We are executing the authorized Web2 bug bounty agent workflow.

First read:
- $HUNTERWEB_HOME/docs/web2-bounty-agent-operating-plan.md
- $HUNTERWEB_HOME/docs/hunter-profile-from-intigriti.md
- $HUNTERWEB_HOME/docs/operator-prompts.md

Core rules:
- Operate only inside explicit scope.
- Use owned test accounts only.
- Do not submit, comment, edit, change settings, perform destructive actions,
  access real user data, or take over resources without explicit approval.
- Use the promotion pipeline: notes -> leads -> primitives -> findings -> reports.
- POC or GTFO: no working proof means not confirmed.
- Bias toward authz/IDOR/BOLA, role/tenant confusion, unauthorized
  state-changing APIs, business logic workflow bypasses, and chains from low
  privilege to higher impact.
- Keep reports concise, technical, and dry.
- Cap sub-agents at 2-3 unless explicitly approved.

End-of-phase handoff requirement:
Before stopping every phase, write or update notes/recent-state.md with:
- Current phase and completion status.
- Target program, platform, and workspace path.
- Scope/rules summary and forbidden actions.
- Auth/account status and auth file locations.
- Request wrappers and how to use them.
- What was done this phase.
- Key observations.
- Current leads, primitives, findings, and reports counts.
- Highest-priority next actions.
- Blockers or missing information.
- Files changed or created.
- Exact next prompt/phase to run.

Target:
- Program:
- Platform:
- Policy URL:
- Workspace path: $HUNTERWEB_HOME/bounty/<program>/<target>
- In-scope assets:
- Out-of-scope assets:
- Required headers / UA tags:
- Rate limit:
- Test accounts / roles:
- Auth files or cookies:
- Forbidden actions:
```

## Comprehensive Recon Execution Prompt

Use this prompt when starting a target-specific recon pass whose goal is to
build a high-precision business, technical, asset, feature, attack-surface, and
security-control map before active hunting. This recon includes safe live target
probing after scope, wrappers, headers, rate limits, and account rules are
confirmed.

If the target is an Intigriti program and the local researcher PAT is configured,
prefer the skill-based short form:

```text
Use bounty-recon for the Intigriti program: <program name>
```

The skill will read the PAT only from local secret sources such as
`$HUNTERWEB_HOME/secrets/intigriti_pat`, query the Intigriti researcher API, and
save raw API evidence under `<workspace>/platform/intigriti/`. Do not paste PATs
into chat or docs.

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

You are operating as an authorized Web2 bug bounty reconnaissance agent.

Target:
- Program:
- Platform:
- Policy URL:
- Workspace path: $HUNTERWEB_HOME/bounty/<program>/<target>
- Current date:
- In-scope assets:
- Out-of-scope assets:
- Required headers / UA tags:
- Rate limit:
- Test accounts / roles:
- Auth files or cookies:
- Forbidden actions:

Mission:
Build a precise, evidence-backed reconnaissance map for the target. Do not
collect random data. The goal is to understand the target deeply enough to guide
high-quality vulnerability testing inside explicit program scope.

Recon goals:
1. Understand the target's general business.
2. Understand the target's technical business.
3. Understand the target's technical architecture.
4. Understand the target's assets.
5. Understand the target's features on every in-scope asset.
6. Map every realistic attack surface.
7. Understand the target's complete security mechanisms and security features.

Operating rules:
- Stay strictly inside the authorized program scope.
- Do not actively test assets unless they are confirmed in scope.
- Respect rate limits, account rules, required headers, user-agent tags, and
  exclusions.
- Use owned test accounts only.
- Prefer recent official sources and live observed behavior.
- Treat live behavior as stronger evidence than documentation.
- Separate facts, inferences, and assumptions.
- Every claim must have a source, timestamp, confidence level, and evidence.
- Any source older than 12 months must be reconfirmed live or marked historical.
- Every unknown must be tracked until resolved, blocked, or accepted as a gap.
- Do not report theoretical issues. Only promote reproducible behavior.

Required output structure:
Create or update these files under the target workspace:

scope.md
sources.md
business.md
technical-business.md
architecture.md
assets.md
security-model.md
notes/live-probing.md
notes/traffic-map.md
features/
attack-surface.md
coverage-matrix.md
unknowns.md
priority-testing-plan.md
leads/
primitives/
findings/
reports/

Phase 0: Scope Control
- Parse the program policy.
- Extract in-scope assets, out-of-scope assets, testing limits, account rules,
  required headers, user-agent tags, and exclusions.
- Create or update scope.md.
- Do not proceed with active probing until scope status is clear.
- Configure or verify request wrappers before live probing.

Phase 1: Recent Source Collection
Collect and timestamp relevant information from:
- Program page
- Official website
- Product pages
- Pricing pages
- API docs
- Developer docs
- Help center
- Changelog and release notes
- Status page
- Security page or trust center
- Privacy policy
- Subprocessor list
- App Store and Google Play listings
- Browser extension stores
- Public GitHub/GitLab orgs
- Package registries
- Docker/container registries
- Certificate transparency logs
- DNS records
- Engineering blog posts
- Recent job postings
- Recent press releases
- Public security advisories

For each source, record:
source:
url:
type:
published_at:
retrieved_at:
relevance:
assets_mentioned:
features_mentioned:
security_controls_mentioned:
confidence:

Phase 2: Safe Live Target Probing
Run only after scope and wrappers are confirmed.

Allowed unauthenticated baseline probes:
- DNS, TLS, root HEAD/GET, redirects, status, headers, cookies, CSP, CORS where
  safe, robots.txt, sitemap.xml, security.txt, linked public scripts, public
  API docs, and browser observation of public routes/forms/auth entry points.

Allowed authenticated baseline probes:
- Login/logout and session observation with owned accounts.
- Read-only navigation through reachable features.
- Owned-object setup only when required to understand normal workflows and
  allowed by program rules.
- Role/account differences using owned accounts only.

Do not perform during recon:
- Fuzzing, brute force, high-volume crawling, DoS checks, scanner-style payload
  sweeps, destructive state changes, billing-affecting actions, spam,
  persistence, takeover, or real-user data access.

For each probe, record:
asset:
scope_status:
probe_profile:
wrapper_used:
rate_limit:
timestamp:
status_code:
final_url:
redirect_chain:
tls:
dns:
headers:
cookies:
csp:
cors:
visible_features:
linked_scripts:
api_hints:
auth_entry_points:
errors_or_anomalies:
evidence_paths:
qa_status:

Write notes/live-probing.md and notes/traffic-map.md. Store raw evidence under
output/live-probes/ where practical.

Completion gates:
- Every in-scope asset has a live baseline probe or documented blocker.
- Every live request has scope status, timestamp, role/auth state, and evidence.
- Every redirect/script/API/third-party host is labeled in_scope, out_of_scope,
  or unknown.
- Every observed anomaly is added to notes/loop/queue.md or leads/.

Phase 3: Business Understanding
Document:
- What the target does
- Products and customer segments
- Business model
- User roles
- Revenue-critical workflows
- Sensitive data handled
- Compliance/security-sensitive areas
- Partner ecosystem
- Workflows that create money, access, trust, or data movement

Write business.md.

Phase 4: Technical Business Understanding
Map business functions to technical systems:
- Web apps
- APIs
- Mobile apps
- Desktop apps
- Browser extensions
- Developer platform
- Partner portal
- Admin portal
- SSO/SAML/OAuth
- Webhooks
- Billing
- File import/export
- Notifications
- Integrations

Write technical-business.md.

Phase 5: Architecture Mapping
Infer and verify:
- Domains and subdomains
- CDN/WAF
- Auth provider
- API gateway
- Cloud provider hints
- Storage/CDN paths
- REST/GraphQL/WebSocket use
- Mobile API endpoints
- Tenant boundaries
- Role boundaries
- Third-party services
- Callback and webhook flows
- Login and email-link flows

Use evidence from:
- HTTP headers
- DNS
- TLS certificates
- JavaScript bundles
- API docs
- CSP/connect-src
- Redirect chains
- Error responses
- Mobile app metadata where allowed
- Live baseline probes
- Traffic observations

Write architecture.md.

Phase 6: Asset Inventory
For every discovered asset, record:
asset:
type:
scope_status:
source:
first_seen:
last_confirmed:
auth_required:
roles_available:
main_features:
technologies:
security_controls:
live_baseline_status:
notes:

Do not leave assets without scope_status.
Write assets.md.

Phase 7: Feature Inventory
For every in-scope asset, create a feature file under features/.

For each feature, record:
feature:
asset:
path_or_endpoint:
method:
auth_required:
roles:
objects_accessed:
state_change:
data_exposed:
inputs:
outputs:
security_controls:
attack_surfaces:
test_accounts_used:
evidence:
live_probe_evidence:
qa_status:

Highlight:
- State-changing features
- Object-accessing features
- Uploads
- Imports
- Exports
- Search
- Invites
- Sharing
- Billing
- Role management
- Integrations
- Webhooks
- OAuth apps
- API tokens
- Account recovery
- Admin/security settings

Phase 8: Security Mechanism Mapping
Document observed behavior for:
- Login methods
- Password policy
- Email verification
- MFA
- Passkeys
- SSO/SAML
- OAuth
- Session management
- Refresh tokens
- Logout
- Device/session management
- Password reset
- Account recovery
- Account lockout
- CAPTCHA/bot controls
- Rate limits
- CSRF
- CORS
- CSP
- Cookie flags
- Security headers
- API keys
- OAuth scopes
- Webhook signing
- Audit logs
- Admin security settings
- Tenant isolation
- Role permissions
- Data export controls
- Signed URLs
- File access controls
- Alerts and notifications

For each security control, record:
security_control:
where_observed:
asset:
feature:
role:
expected_behavior:
observed_behavior:
bypass_hypotheses:
evidence:
qa_status:

Write security-model.md.

Phase 9: Attack Surface Mapping
For each feature and security boundary, create attack surface entries:
surface:
related_assets:
related_features:
attacker_role:
victim_role:
security_boundary:
likely_bug_classes:
impact_if_broken:
test_priority:
evidence:
status:

Include:
- Authentication
- Authorization
- Cross-tenant access
- Object-level access control
- Role escalation
- Invite/share flows
- Billing logic
- File upload/download
- Import/export
- Search/indexing
- SSRF-like fetchers/previews
- Redirects
- Webhooks/callbacks
- OAuth integrations
- SSO/SAML
- API tokens
- GraphQL
- WebSockets
- Mobile APIs
- Admin/support functions
- Public data exposure
- Security feature bypasses

Write attack-surface.md.

Phase 10: Coverage And QA
Maintain coverage-matrix.md with:

Asset | Scope | Live Baseline | Auth States | Roles | Features | Security Controls | Attack Surfaces | Evidence | QA Status | Unknowns

Completion gates:
- Every asset has scope_status.
- Every in-scope asset has live baseline evidence or a documented blocker.
- Every in-scope asset has feature inventory.
- Every feature has role mapping.
- Every state-changing feature has authorization notes.
- Every object-accessing feature has ownership-boundary notes.
- Every security mechanism is tied to observed behavior or marked unverified.
- Every attack surface has attacker role, victim role, boundary, and impact
  hypothesis.
- Every claim has evidence.
- Every stale source is marked stale or reconfirmed.
- Every unknown is resolved, blocked, or accepted_gap.

Write unknowns.md with:
unknown:
why_it_matters:
attempted_resolution:
blocked_by:
next_action:
status:

Phase 11: Priority Testing Plan
Produce priority-testing-plan.md.

Prioritize by:
- Impact
- Reachability from realistic attacker role
- Weakness of observed controls
- Business criticality
- Cross-tenant or privileged potential
- Novelty
- Program policy fit

For each test idea:
test:
related_surface:
attacker_role:
victim_role:
required_accounts:
steps_summary:
expected_control:
impact_if_control_fails:
priority:
status:

Definition of done:
Recon is complete only when the system can answer with evidence:
- What does the target do?
- What systems expose the business?
- What assets are in scope?
- What live behavior was safely observed for each in-scope asset?
- What does each asset do?
- What roles exist?
- What can each role access?
- What security controls exist?
- Where are the trust boundaries?
- What attack surfaces exist?
- What are the highest-priority tests?
- What remains unknown and why?

Final response:
Summarize:
- Completed files
- Live baseline coverage
- Most important assets
- Most important features
- Security mechanisms observed
- Highest-priority attack surfaces
- Unknowns or blockers
- Recommended next tests
```

## Phase Prompts

### Phase 1: Setup And Scope

```text
Run Phase 1: Setup And Scope.

Do not perform live probing yet.

Tasks:
1. Create or refresh the target workspace from $HUNTERWEB_HOME/templates/target/.
2. Ingest scope and rules into notes/rules.md.
3. Create durable session notes.
4. Identify missing information needed before safe probing.
5. Design safe request wrappers for scope, auth, headers, and rate limits.
6. Produce the initial execution checklist.
7. Update notes/recent-state.md with the end-of-phase handoff.

Stop after setup.
```

### Phase 2: Recon And Traffic Map

```text
Run Phase 2: Recon And Traffic Map.

Start by reading:
- notes/recent-state.md
- notes/rules.md
- notes/recon.md
- notes/loop/queue.md
- notes/loop/log.md

Tasks:
1. Verify request wrappers enforce scope, headers, auth, and rate limits.
2. Run safe live baseline probes against confirmed in-scope assets only:
   low-rate root HEAD/GET, redirects, headers, cookies, TLS/DNS, CSP, public
   metadata, linked scripts, public routes, and browser observation.
3. Capture authenticated read-only traffic from owned accounts where allowed.
4. Map auth surfaces, roles, tenants, object types, APIs, GraphQL routes, and
   state-changing endpoints.
5. Populate notes/recon.md, notes/live-probing.md, notes/traffic-map.md, and
   notes/loop/log.md.
6. Add only observed anomalies to notes/loop/queue.md or leads/.
7. Update notes/recent-state.md with the end-of-phase handoff.

Do not promote anything to findings yet. Stop when the initial endpoint/object/
role map is useful.
```

### Phase 3: Authz And State-Change Hunting

```text
Run Phase 3: Authz And State-Change Hunting.

Start by reading:
- notes/recent-state.md
- notes/rules.md
- notes/recon.md
- notes/loop/queue.md
- notes/loop/log.md
- leads/
- primitives/

Focus only on highest-EV patterns:
authz/IDOR/BOLA, role/tenant confusion, unauthorized state-changing APIs, and
business logic bypass.

Tasks:
1. Replay account A object requests as account B.
2. Replay tenant/admin/member actions across roles.
3. Test state-changing endpoints: create, delete, transfer, reset, clone, assign,
   rebuild, overwrite, restore, invite, revoke, update.
4. Diff status codes, response bodies, hidden fields, ownership, and side effects.
5. Move reproducible controllable behavior from leads/ into primitives/.
6. Record failed tests in notes/loop/log.md.
7. Update notes/recent-state.md with the end-of-phase handoff.

POC or GTFO. No proof means not confirmed. Stop after producing a prioritized
primitives list.
```

### Phase 4: Chain And Validate

```text
Run Phase 4: Chain And Validate.

Start by reading:
- notes/recent-state.md
- notes/rules.md
- notes/recon.md
- notes/loop/queue.md
- notes/loop/log.md
- leads/
- primitives/
- findings/

Focus on escalating primitives into reportable impact.

Tasks:
1. For each high-priority primitive, test whether it chains to cross-tenant
   access, privileged action, sensitive data exposure, account takeover, SSRF
   impact, stored execution/rendering impact, or RCE in an authorized lab.
2. Use source, JS bundles, schemas, or docs only to explain and escalate observed
   live behavior.
3. Build minimal PoCs using owned accounts only.
4. Apply the six-step finding gate.
5. Promote only proven issues into findings/.
6. Update notes/recent-state.md with the end-of-phase handoff.

Do not draft reports for weak primitives. Stop when findings/ contains only
validated issues.
```

### Phase 5: Report Drafting

```text
Run Phase 5: Report Drafting.

Start by reading:
- notes/recent-state.md
- notes/rules.md
- findings/
- reports/report-template.md

Draft concise, technical, dry reports only for validated findings.

Tasks:
1. Read findings/ and the report template.
2. Draft one report per distinct root cause in reports/.
3. Include exact asset, endpoint, role, reproduction steps, evidence, impact,
   root cause, remediation, and policy fit.
4. Proofread each report by following the reproduction steps from scratch.
5. Mark any report that fails reproduction as not ready and move it back to
   findings/ or primitives/.
6. Update notes/recent-state.md with the end-of-phase handoff.

Do not submit, comment, edit, or take account actions without explicit approval.
```

## Resume Prompt

Use this after context has been cleared, a session compacted, a previous phase
stopped halfway, or a new Codex instance needs to continue from the last saved
state.

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

Resume the authorized Web2 bug bounty workflow from:
<workspace>/notes/recent-state.md

First read:
- <workspace>/notes/recent-state.md
- <workspace>/notes/rules.md
- <workspace>/notes/recon.md
- <workspace>/notes/loop/queue.md
- <workspace>/notes/loop/log.md
- <workspace>/leads/
- <workspace>/primitives/
- <workspace>/findings/
- <workspace>/reports/

Continue with the phase named in the Resume Instruction.

At the end, update notes/recent-state.md again with a precise handoff for the
next session.
```

Example:

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

Resume the authorized Web2 bug bounty workflow from:
$HUNTERWEB_HOME/bounty/digitalocean/cloud/notes/recent-state.md

First read:
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/notes/recent-state.md
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/notes/rules.md
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/notes/recon.md
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/notes/loop/queue.md
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/notes/loop/log.md
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/leads/
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/primitives/
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/findings/
- $HUNTERWEB_HOME/bounty/digitalocean/cloud/reports/

Continue with the phase named in the Resume Instruction.

At the end, update notes/recent-state.md again with a precise handoff for the
next session.
```
