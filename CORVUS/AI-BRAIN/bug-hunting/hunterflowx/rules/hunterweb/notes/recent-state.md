# Recent State

## 2026-05-06 Firefox Playwright MCP Setup

- Request: set up browser control for Firefox from Codex.
- Workspace root confirmed: `/Users/raihan/BugBounty/worfklow/hunterweb`.
- Local Firefox app found at `/Applications/Firefox.app`.
- Bright Data MCP package checked: `@brightdata/mcp` exists, but it requires `API_TOKEN` and no Bright Data token environment variable was present in this session.
- Added global Codex MCP server: `playwright-firefox`.
- MCP command: `npx -y @playwright/mcp@latest --browser firefox --user-data-dir /Users/raihan/.codex/browser/firefox-playwright-profile --output-dir /Users/raihan/.codex/browser/firefox-playwright-output --save-session --caps vision,devtools --viewport-size 1440x1000`.
- Installed Playwright Firefox browser build with `npx -y playwright@latest install firefox`.
- Smoke test passed with Playwright Firefox screenshot output at `/Users/raihan/.codex/browser/firefox-playwright-output/smoke.png`.
- Current limitation: Codex MCP tool lists do not hot-reload inside an already running session; the `playwright-firefox` MCP server should be available after starting/resuming a new Codex session.

## 2026-05-06 Codex Plugin Migration

- Request: migrate the current project's Claude Code plugin setup from `.claude/plugins` into Codex-facing project artifacts.
- Source inspected: `.claude/plugins/installed_plugins.json`, `.claude/plugins/known_marketplaces.json`, installed plugin cache manifests, and marketplace manifests.
- Codex artifacts created:
  - `.agents/plugins/marketplace.json`
  - `plugins/claude-mem/`
  - `plugins/insane-search/`
  - `plugins/andrej-karpathy-skills/`
  - `plugins/caveman/`
- Installed Claude plugins represented in the Codex marketplace: `claude-mem`, `insane-search`, `andrej-karpathy-skills`, and `caveman`.
- `claude-mem` MCP config was migrated as disabled in `plugins/claude-mem/.mcp.json` for manual review before enabling.
- Validation run: JSON parsing for marketplace and plugin manifests passed; marketplace paths resolve; bundled plugin skill frontmatter has `name` and `description`; `migrate-to-codex --validate-target ./.codex/` completed with one unrelated warning under `.codex/.tmp/plugins`.
- Migrator note: `migrate-to-codex --dry-run` still reports `.claude/plugins` as manual review because Claude plugin trees are intentionally outside the automated converter.

## Current Phase And Status

- Phase: Phase 5 - Report Drafting.
- Completion status: Blocked before drafting.
- Stop condition: stopped because there are no validated findings, no distinct root causes, no reproduction steps, no evidence, and no target scope or owned-account proof.

## Target Program, Platform, And Workspace Path

- Target program: Signicat.
- Platform: Intigriti.
- Policy URL: `https://app.intigriti.com/researcher/programs/signicat/Signicat/detail`.
- Requested workspace path pattern: `/home/hunterweb/bounty/<program>/<target>`.
- Actual setup workspace path: `/home/hunterweb/bounty/_pending/_scope`.
- Reason for placeholder path: the user supplied workflow rules but left the target block blank.

## Scope, Rules, And Forbidden Actions

- Scope status: no explicit in-scope assets provided.
- Safe probing status: blocked.
- All real external assets are treated as out of scope until explicitly listed.
- Target rules file: `/home/hunterweb/bounty/_pending/_scope/notes/rules.md`.
- Forbidden actions: live probing before scope is known; submitting, commenting, editing, changing settings, destructive actions, real user data access, resource takeover, persistence, spam, mass enumeration, billing-affecting operations, production instability testing, non-owned-account testing, unapproved state changes, and report drafting without validated proof.

## Auth And Account Status

- Test accounts / roles: not provided.
- Auth files or cookies: Intigriti PAT provided for platform/API access only; no target application auth provided.
- Auth file locations: `/home/hunterweb/secrets/intigriti/signicat/pat` (chmod `600`, token not stored in notes).
- Account/tenant model: unknown.

## Request Wrappers And How To Use Them

- Wrapper design note: `/home/hunterweb/bounty/_pending/_scope/notes/request-wrapper-design.md`.
- Config example: `/home/hunterweb/bounty/_pending/_scope/config/target.env.example`.
- Low-level wrapper: `/home/hunterweb/bounty/_pending/_scope/scripts/req.sh`.
- API wrapper: `/home/hunterweb/bounty/_pending/_scope/scripts/api.sh`.
- The wrappers fail closed because `config/target.env` has not been created.
- Intended usage after real scope is configured:
  - `cp config/target.env.example config/target.env`
  - Fill in strict `SCOPE_REGEX`, required headers, User-Agent tag, rate limit, API base, and owned-account auth file paths.
  - Use `scripts/req.sh -a none -X GET https://in-scope.example/path`.
  - Use `scripts/api.sh /v1/path -a A -X GET` for API-base requests.

## What Was Done This Phase

- Read target recent state, rules, findings, and report template.
- Confirmed `findings/` contains only `README.md` and no validated findings.
- Confirmed `reports/` contains only `README.md` and `report-template.md`.
- Recorded the blocked Phase 5 report-drafting attempt in the target loop log.
- Did not draft reports, proofread reproduction steps, demote reports, submit, comment, edit, or take account actions.
- Separately created `docs/bug-bounty-operator-guide.md` as a practical start-to-finish operating guide.
- Updated `docs/operator-prompts.md` to point users to the new guide.

## Key Observations

- Program URL and Intigriti PAT are now available, but no in-scope asset list, required request marker, rate limit, target account, role, tenant, endpoint, object ID, lead, confirmed primitive, validated finding, or reportable root cause has been provided.
- Wrapper enforcement is fail-closed in the current state.
- POC or GTFO: no proof means no confirmed primitive, finding, or report.
- Report drafting is blocked because `findings/` contains no validated issues.

## Current Counts

- Notes: 9 files in `/home/hunterweb/bounty/_pending/_scope/notes/`, including loop notes.
- Leads: 0.
- Primitives: 0 confirmed. One prioritized primitive-list planning note exists.
- Findings: 0.
- Reports: 0 drafts, plus `README.md` and `report-template.md`.

## Highest-Priority Next Actions

1. Ingest the Signicat Intigriti program policy and scope from `https://app.intigriti.com/researcher/programs/signicat/Signicat/detail` using the stored PAT if needed.
2. Move or recreate the placeholder workspace at `/home/hunterweb/bounty/<program>/<target>/`.
3. Populate `notes/rules.md` and `config/target.env`.
4. Validate wrapper scope matching, required headers, auth selection, and rate-limit behavior without sending out-of-scope traffic.
5. Resume Phase 2 with low-volume unauthenticated and owned-account traffic mapping inside explicit scope.
6. Re-run Phase 3 only after Phase 2 produces mapped endpoints, owned-account object IDs, roles, tenants, and candidate state-changing requests.
7. Re-run Phase 4 only after confirmed primitives exist.
8. Re-run Phase 5 only after validated findings exist.

## Blockers Or Missing Information

- Target name.
- In-scope assets.
- Out-of-scope assets.
- Required headers or UA tags.
- Rate limit.
- Test accounts and roles.
- Auth files or cookies.
- Account and tenant model.
- Mapped endpoints and object IDs.
- Candidate state-changing requests.
- Confirmed primitives to chain.
- Validated findings with reproduction steps and evidence.
- Program-specific forbidden actions and approval boundaries.

## Files Changed Or Created

- `/home/hunterweb/bounty/_pending/_scope/notes/loop/log.md`
- `/home/hunterweb/bounty/_pending/_scope/notes/execution-checklist.md`
- `/home/hunterweb/bounty/_pending/_scope/notes/recent-state.md`
- `/home/hunterweb/notes/recent-state.md`
- `/home/hunterweb/docs/bug-bounty-operator-guide.md`
- `/home/hunterweb/docs/operator-prompts.md`
- `/home/hunterweb/secrets/intigriti/signicat/pat`

## Exact Next Prompt / Phase To Run

Provide the missing target details, then run: "Run Phase 1A: Target-Specific Scope Ingestion. Move or recreate the placeholder workspace at `/home/hunterweb/bounty/<program>/<target>/`, ingest the program policy and scope into `notes/rules.md`, configure `config/target.env`, validate wrappers without live probing, and stop."
