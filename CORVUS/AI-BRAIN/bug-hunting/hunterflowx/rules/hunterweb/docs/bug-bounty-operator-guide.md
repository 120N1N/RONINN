# Bug Bounty Operator Guide

Date: 2026-04-29

This guide explains how to operate the authorized Web2 bug bounty agent from the
start of an engagement. It is the practical checklist. The full methodology is
in `docs/web2-bounty-agent-operating-plan.md`, and copy/paste prompts are in
`docs/operator-prompts.md`.

Path convention: set `HUNTERWEB_HOME` to the workspace root before running
examples. On the VPS this may be `/home/hunterweb`; in a local checkout it may
be another path.

```bash
export HUNTERWEB_HOME="${HUNTERWEB_HOME:-$(pwd)}"
```

## Non-Negotiable Rules

- Work only inside explicit program scope.
- Use owned test accounts only.
- Enforce program headers, User-Agent tags, account limits, rate limits, and
  exclusions before every request.
- Do not submit reports, comment, edit, change settings, perform destructive
  actions, access real user data, or take over resources without explicit user
  approval and program permission.
- Do not rely on scanner-only or theoretical claims.
- POC or GTFO: no working proof means the issue is not confirmed.
- Keep durable notes on disk before stopping every phase.
- Use the promotion pipeline: `notes -> leads -> primitives -> findings ->
  reports`.

## What The User Must Provide First

Before live probing, provide as much of this as possible:

```text
Program:
Platform:
Policy URL:
Workspace path: $HUNTERWEB_HOME/bounty/<program>/<target>
In-scope assets:
Out-of-scope assets:
Required headers / UA tags:
Rate limit:
Test accounts / roles:
Auth files or cookies:
Forbidden actions:
```

Minimum required for safe probing:

- Exact in-scope asset or API base.
- Exact out-of-scope assets.
- Required request markers, if any.
- Rate limit.
- Owned account/auth material for any authenticated testing.
- Program-specific forbidden actions.

If these are missing, the agent should stop after setup and write the missing
items to `notes/missing-info.md` and `notes/recent-state.md`.

### Intigriti Program-Name Lookup

For Intigriti programs, the `bounty-recon` skill can start from just the program
name if a researcher PAT is configured locally.

Example request:

```text
Use bounty-recon for the Intigriti program: <program name>
```

The skill will use:

```text
$HUNTERWEB_HOME/.codex/skills/bounty-recon/scripts/intigriti_lookup.py
```

to query the Intigriti researcher API, match the accessible program by name,
fetch program detail, and save raw API evidence under:

```text
<workspace>/platform/intigriti/
```

The helper reads the PAT from one of these local sources:

```text
INTIGRITI_PAT
INTIGRITI_RESEARCHER_PAT
INTIGRITI_PAT_FILE
$HUNTERWEB_HOME/secrets/intigriti_pat
$HUNTERWEB_HOME/secrets/intigriti/pat
~/.config/intigriti/pat
```

Recommended setup:

```bash
mkdir -p $HUNTERWEB_HOME/secrets
chmod 700 $HUNTERWEB_HOME/secrets
printf '%s' '<PAT>' > $HUNTERWEB_HOME/secrets/intigriti_pat
chmod 600 $HUNTERWEB_HOME/secrets/intigriti_pat
```

Do not paste the PAT into chat, prompts, notes, reports, findings, or skill
files. The PAT should stay in a local secret file or environment variable only.

If multiple programs match the supplied name, the agent should ask for the exact
program name or program ID. If the API returns 403 for details, the agent should
record that the program terms may need to be accepted in the Intigriti UI before
scope can be read.

## Workspace Layout

Each target gets a workspace:

```text
$HUNTERWEB_HOME/bounty/<program>/<target>/
  config/target.env
  config/target.env.example
  scripts/req.sh
  scripts/api.sh
  notes/rules.md
  notes/recon.md
  notes/live-probing.md
  notes/traffic-map.md
  notes/session.md
  notes/missing-info.md
  notes/request-wrapper-design.md
  notes/execution-checklist.md
  notes/recent-state.md
  notes/loop/queue.md
  notes/loop/log.md
  leads/
  primitives/
  findings/
  reports/
  output/
  acct2/
```

Use `$HUNTERWEB_HOME/templates/target/` as the base template.

If the program or target name is unknown, use a temporary workspace such as:

```text
$HUNTERWEB_HOME/bounty/_pending/_scope
```

Move or recreate it under the real path once the target is known.

## Secrets And Auth Material

Store secrets outside notes and reports. Notes should include only file paths.

Recommended layout:

```text
$HUNTERWEB_HOME/secrets/<platform>/<program>/
  pat
  acct-a.cookies
  acct-b.cookies
  acct-a.bearer
  acct-b.bearer
```

Permissions should be restrictive:

```bash
chmod 700 $HUNTERWEB_HOME/secrets/<platform>/<program>
chmod 600 $HUNTERWEB_HOME/secrets/<platform>/<program>/*
```

Do not paste tokens into `notes/`, `leads/`, `primitives/`, `findings/`, or
`reports/`.

## Request Wrappers

All probing should go through wrappers after `config/target.env` is configured.

Required behavior:

- Refuse to run if `config/target.env` is missing.
- Reject URLs outside `SCOPE_REGEX`.
- Add required headers and User-Agent tags.
- Use selected owned-account auth only.
- Apply rate limits.
- Log request metadata to `output/request-log.tsv`.

Example configuration fields:

```text
TARGET_PROGRAM=""
TARGET_NAME=""
PLATFORM=""
POLICY_URL=""
SCOPE_REGEX='^https://example\\.com(/|$)'
REQUIRED_HEADER_NAME=""
REQUIRED_HEADER_VALUE=""
USER_AGENT_TAG=""
RATE_LIMIT_SECONDS="2"
API_BASE_URL=""
AUTH_COOKIE_JAR_A=""
AUTH_COOKIE_JAR_B=""
AUTH_BEARER_FILE_A=""
AUTH_BEARER_FILE_B=""
```

Example wrapper usage after configuration:

```bash
scripts/req.sh -a none -X GET https://in-scope.example/path
scripts/req.sh -a A -X GET https://in-scope.example/api/resource
scripts/api.sh /v1/resource -a B -X GET
```

Never bypass wrappers for live target requests unless the user explicitly
approves a different safe method.

## Evidence Pipeline

Use this promotion model:

```text
notes/       raw observations, session log, recon, rules, queue
leads/       interesting anomalies that need reproduction
primitives/  reproducible controllable behavior with plausible security use
findings/    six-gate issues with demonstrated impact and novelty checks
reports/     concise final drafts with exact reproduction steps
```

Promotion rules:

- `notes -> leads`: live target did something unexpected.
- `leads -> primitives`: behavior is reproducible and attacker-controlled.
- `primitives -> findings`: boundary is crossed or safely chained with proof.
- `findings -> reports`: writeup is concise, policy-fit, deduped, and proofread.

Demote weak evidence instead of forcing it forward.

## Six-Step Finding Gate

Every reportable finding must pass all six:

1. Observe live weirdness.
2. Reproduce and control it.
3. Understand the mechanism.
4. Escalate to the highest safe impact.
5. Build minimal proof with owned accounts and minimal data.
6. Prove novelty and policy fit before submission.

If any gate fails, the issue is not ready for `findings/` or `reports/`.

## Phase 0: Intake

Goal: give the agent enough information to start safely.

User action:

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

We are executing an authorized Web2 bug bounty workflow.

Program:
Platform:
Policy URL:
Workspace path:
In-scope assets:
Out-of-scope assets:
Required headers / UA tags:
Rate limit:
Test accounts / roles:
Auth files or cookies:
Forbidden actions:
```

Expected agent output:

- Restates the concrete target and assumptions.
- Reads the operating docs.
- Records missing information.
- Does not probe anything until scope is explicit.

## Phase 1: Setup And Scope

Goal: create the workspace and write the rules before traffic.

Run this when target details are available or partially available:

```text
Run Phase 1: Setup And Scope.

Do not perform live probing yet.
```

Expected agent actions:

- Create or refresh workspace from `$HUNTERWEB_HOME/templates/target/`.
- Write `notes/rules.md`.
- Write `notes/session.md`.
- Write `notes/missing-info.md`.
- Create or verify wrapper design.
- Write `notes/execution-checklist.md`.
- Update `notes/recent-state.md`.

Do not continue to Phase 2 until `notes/rules.md` and `config/target.env` are
safe enough to prevent out-of-scope requests.

## Phase 1A: Target-Specific Scope Ingestion

Goal: convert a platform policy page into enforceable local rules.

Use this when the program URL or platform token is known but scope is not yet
written locally:

```text
Run Phase 1A: Target-Specific Scope Ingestion.
Move or recreate the workspace at $HUNTERWEB_HOME/bounty/<program>/<target>/,
ingest the program policy and scope into notes/rules.md, configure
config/target.env, validate wrappers without live probing, and stop.
```

Expected agent actions:

- Read the platform policy using stored credentials if needed.
- Extract in-scope and out-of-scope assets.
- Extract required headers, User-Agent tags, rate limits, account rules, and
  exclusions.
- Create the real target workspace.
- Configure `config/target.env`.
- Validate wrappers locally and with safe blocked checks only.
- Stop before live probing.

## Phase 2: Recon And Traffic Map

Goal: build a live baseline, endpoint, object, role, and tenant map.

Run only after wrappers are configured:

```text
Run Phase 2: Recon And Traffic Map.
```

Expected agent actions:

- Read current notes.
- Verify wrappers enforce scope, headers, auth, and rate limits.
- Run safe live baseline probes against confirmed in-scope assets only:
  low-rate root `HEAD`/`GET`, redirects, headers, cookies, TLS/DNS, CSP,
  public metadata, linked scripts, public routes, and browser observation.
- Capture or ingest authenticated read-only traffic from owned accounts only.
- Record live observations in `notes/live-probing.md`, `notes/traffic-map.md`, and
  `output/live-probes/` where practical.
- Map unauthenticated surfaces.
- Map auth surfaces, roles, tenants, object types, APIs, GraphQL routes, and
  state-changing endpoints.
- Update `notes/recon.md` and `notes/loop/log.md`.
- Add only observed anomalies to `notes/loop/queue.md` or `leads/`.

Stop when the initial endpoint/object/role map is useful.

Do not fuzz, brute force, run high-volume crawls, perform DoS checks, use
scanner-style payload sweeps, touch out-of-scope/unknown hosts, make destructive
state changes, affect billing, spam, persist access, take over resources, or
access real-user data during Phase 2. Do not promote anything to findings in
Phase 2.

## Phase 3: Authz And State-Change Hunting

Goal: turn observed anomalies into reproducible primitives.

Run after Phase 2 has mapped accounts, objects, roles, tenants, and endpoints:

```text
Run Phase 3: Authz And State-Change Hunting.
```

Focus only on high-EV patterns:

- Authz/IDOR/BOLA.
- Role or tenant confusion.
- Unauthorized state-changing APIs.
- Business logic workflow bypass.

Expected agent actions:

- Replay account A object requests as account B.
- Replay tenant/admin/member actions across roles.
- Test allowed owned-account state-changing endpoints:
  create, delete, transfer, reset, clone, assign, rebuild, overwrite, restore,
  invite, revoke, update.
- Diff status codes, response bodies, hidden fields, ownership, and side
  effects.
- Move reproducible controllable behavior from `leads/` to `primitives/`.
- Record failed tests in `notes/loop/log.md`.
- Produce a prioritized primitive list.

POC or GTFO. No proof means not confirmed.

## Phase 4: Chain And Validate

Goal: turn primitives into validated findings.

Run after Phase 3 produces confirmed primitives:

```text
Run Phase 4: Chain And Validate.
```

Expected agent actions:

- For each high-priority primitive, test safe chains to:
  cross-tenant access, privileged action, sensitive data exposure, account
  takeover, SSRF impact, stored execution/rendering impact, or RCE in an
  authorized lab.
- Use source, JS bundles, schemas, or docs only to explain and escalate observed
  live behavior.
- Build minimal PoCs using owned accounts only.
- Apply the six-step finding gate.
- Promote only validated issues into `findings/`.

Do not draft reports for weak primitives.

## Phase 5: Report Drafting

Goal: write final reports only for validated findings.

Run after Phase 4 produces validated findings:

```text
Run Phase 5: Report Drafting.
```

Each report must include:

- Exact asset.
- Endpoint or component.
- Attacker role.
- Preconditions.
- Reproduction steps.
- Evidence.
- Impact.
- Root cause.
- Remediation.
- Policy fit.

Expected agent actions:

- Draft one report per distinct root cause in `reports/`.
- Keep language concise, technical, and dry.
- Proofread by following reproduction steps from scratch.
- Mark failed reports as not ready and move them back to `findings/` or
  `primitives/`.

Do not submit, comment, edit, or take account actions without explicit approval.

## End-Of-Phase Handoff

Before stopping any phase, the agent must update:

```text
notes/recent-state.md
```

Required fields:

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

This file is the main resume point after context loss.

## Resume After Context Loss

Use this prompt:

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

Resume the authorized Web2 bug bounty workflow from:
$HUNTERWEB_HOME/bounty/<program>/<target>/notes/recent-state.md

First read:
- $HUNTERWEB_HOME/bounty/<program>/<target>/notes/recent-state.md
- $HUNTERWEB_HOME/bounty/<program>/<target>/notes/rules.md
- $HUNTERWEB_HOME/bounty/<program>/<target>/notes/recon.md
- $HUNTERWEB_HOME/bounty/<program>/<target>/notes/loop/queue.md
- $HUNTERWEB_HOME/bounty/<program>/<target>/notes/loop/log.md
- $HUNTERWEB_HOME/bounty/<program>/<target>/leads/
- $HUNTERWEB_HOME/bounty/<program>/<target>/primitives/
- $HUNTERWEB_HOME/bounty/<program>/<target>/findings/
- $HUNTERWEB_HOME/bounty/<program>/<target>/reports/

Continue with the phase named in the resume instruction.

At the end, update notes/recent-state.md again with a precise handoff.
```

## When To Stop

Stop and ask for missing information when:

- Scope is missing or ambiguous.
- Required headers, User-Agent tags, or rate limits are unknown.
- Auth material is missing for authenticated testing.
- A requested test would touch real user data.
- A requested test would perform destructive or billing-affecting actions.
- The program policy excludes the test class.
- A report would be theoretical, scanner-only, duplicate, or not reproducible.

## Practical First Prompt For A New Engagement

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

Start a new authorized Web2 bug bounty engagement.

Program:
Platform:
Policy URL:
Workspace path: $HUNTERWEB_HOME/bounty/<program>/<target>
In-scope assets:
Out-of-scope assets:
Required headers / UA tags:
Rate limit:
Test accounts / roles:
Auth files or cookies:
Forbidden actions:

Run Phase 1: Setup And Scope. Do not perform live probing yet.
```

## Practical First Prompt When Only A Program URL Exists

```text
Read and follow $HUNTERWEB_HOME/AGENTS.md.

Start target-specific scope ingestion for this authorized program:

Program:
Platform:
Policy URL:
Stored platform token path:
Workspace path: $HUNTERWEB_HOME/bounty/<program>/<target>

Run Phase 1A: Target-Specific Scope Ingestion. Ingest the policy and scope,
configure notes/rules.md and config/target.env, validate wrappers without live
probing, and stop.
```

## Current Signicat Example

Current known Signicat inputs:

```text
Program: Signicat
Platform: Intigriti
Policy URL: https://app.intigriti.com/researcher/programs/signicat/Signicat/detail
Stored platform token path: $HUNTERWEB_HOME/secrets/intigriti/signicat/pat
Current placeholder workspace: $HUNTERWEB_HOME/bounty/_pending/_scope
```

Next safe prompt:

```text
Run Phase 1A: Target-Specific Scope Ingestion for the Signicat Intigriti program.
Use the stored PAT at $HUNTERWEB_HOME/secrets/intigriti/signicat/pat, ingest the
policy and scope, create the real workspace, configure notes/rules.md and
config/target.env, validate wrappers without live probing, and stop.
```
