# Recon Skill Assessment

Date: 2026-05-01

## Scope Reviewed

- `/home/hunterweb/.codex/skills/bounty-recon/SKILL.md`
- `/home/hunterweb/.codex/skills/bounty-recon/references/recon-workflow.md`
- `/home/hunterweb/.codex/skills/bounty-recon/references/intigriti-api.md`
- `/home/hunterweb/.codex/skills/bounty-recon/scripts/intigriti_lookup.py`
- `/home/hunterweb/.codex/skills/bounty-recon/agents/openai.yaml`
- `/home/hunterweb/AGENTS.md`
- `/home/hunterweb/docs/web2-bounty-agent-operating-plan.md`
- `/home/hunterweb/docs/massive-recon-framework.md`
- `/home/hunterweb/docs/massive-recon-framework-execution-plan.md`
- `/home/hunterweb/docs/massive-recon-framework-implementation-prompt.md`
- `/home/hunterweb/docs/recon-framework-assessment-2026-04-30.md`
- `/home/hunterweb/recon-framework/README.md`
- `/home/hunterweb/recon-framework/src/reconfw/workspace.py`
- `/home/hunterweb/recon-framework/src/reconfw/pipeline/audit.py`
- `/home/hunterweb/templates/target/`

Secret files under `/home/hunterweb/secrets/` were not read.

## Verification Performed

- `cd /home/hunterweb/recon-framework && uv run pytest`
  - Result: `80 passed in 2.07s`
- `cd /home/hunterweb/recon-framework && uv run ruff check .`
  - Result: `All checks passed!`
- `cd /home/hunterweb/recon-framework && uv run reconfw --help`
  - Result: CLI exposes `init-target`, `kb`, `classify`, `collect`, `resolve`,
    `network-baseline`, `baseline`, `queue`, `extract`, `map`, `wordlists`,
    `fuzz`, `graph`, `diff`, `promote`, `coverage`, `handoff`, and `recurse`.

## High-Level Assessment

The `bounty-recon` skill is directionally aligned with the local Web2 bounty
doctrine. It correctly requires explicit scope, durable notes, low-impact live
baseline probing, owned accounts, evidence-backed claims, unknown tracking, and
separation of facts, inferences, and assumptions.

The gap is that the skill is still mostly a manual recon runbook, while the
local recon framework has become a policy-gated implementation with
machine-readable program knowledge base files, normalized JSONL objects,
evidence storage, queues, metrics, audits, handoff gates, recursive recon, and
promotion/reporting checks. The skill should be updated so future recon runs use
the implemented framework as the control plane instead of only creating markdown
deliverables by hand.

## Alignment That Should Stay

- Scope-first behavior matches the workspace doctrine: no active probing until
  target scope, headers, user-agent tags, account rules, rate limits, and
  exclusions are understood.
- The live probing layer stays low-impact and evidence-focused. This matches
  the framework safety model for root GET/HEAD, DNS/TLS/header/cookie/CSP/CORS,
  public metadata, JavaScript inventory, and owned-account read-only workflow
  observation.
- The required human deliverables match the target templates and current
  `reconfw init-target` scaffold: `scope.md`, `sources.md`, `business.md`,
  `technical-business.md`, `architecture.md`, `assets.md`,
  `notes/live-probing.md`, `notes/traffic-map.md`, `security-model.md`,
  `features/`, `attack-surface.md`, `coverage-matrix.md`, `unknowns.md`,
  `priority-testing-plan.md`, `leads/`, `primitives/`, `findings/`, `reports/`,
  and `output/live-probes/`.
- The Intigriti lookup flow correctly avoids printing or storing the PAT and
  saves raw API evidence under the target workspace.
- The skill reinforces the core evidence standard: facts need source,
  timestamp, evidence, confidence, and unknowns must be resolved, blocked, or
  accepted before recon is called complete.

## Skill-Side Gaps

### P0: Add First-Class `reconfw` Integration

The skill should explicitly use `/home/hunterweb/recon-framework/` when it
exists. Right now it tells the agent to create or update files manually, but the
framework already provides the safer path:

```bash
cd /home/hunterweb/recon-framework
uv run reconfw init-target --workspace /home/hunterweb/bounty/<program>/<target>
uv run reconfw kb validate --workspace /home/hunterweb/bounty/<program>/<target>
uv run reconfw coverage check --workspace /home/hunterweb/bounty/<program>/<target>
uv run reconfw handoff --workspace /home/hunterweb/bounty/<program>/<target>
```

The skill should say that `reconfw init-target` is the preferred scaffold
generator because it creates both the human markdown deliverables and the
machine-readable framework directories without overwriting existing notes.

### P0: Require Program-KB, Policy Engine, And Safe-Actions Gates

The skill captures rules in `scope.md` and `notes/rules.md`, but it does not
require the framework's machine-readable program-kb files:

- `program-kb/program.json`
- `program-kb/scope.json`
- `program-kb/rate-limits.json`
- `program-kb/safe-actions.json`
- `program-kb/overrides.json`

This is a control-plane gap. Future skill runs should require program-kb
ingestion or manual program-kb completion, then require `reconfw kb validate`
before any live baseline. Active probing should be driven by policy decisions,
not only by markdown notes.

### P0: Tie Live Baselines To Queues, Wrapper Evidence, And Audit

The skill says wrappers must be configured, but it should require framework
evidence paths and queues:

- safe baseline inputs should come from `queues/safe-probe.jsonl` or an
  equivalent explicitly reviewed queue
- wrapper artifacts should be ingested with `reconfw baseline ingest-wrapper`
  when available
- live baseline output should land in `output/live-probes/` and framework
  normalized records, not only `notes/live-probing.md`
- recon should not be called complete until `reconfw coverage check` has no
  unaccepted blockers, or the blockers are documented as accepted gaps

### P0: Add Metrics, Rejections, And Recent-State Requirements

The framework requires metrics and rejected-object tracking:

- `metrics/recon-metrics.json`
- `metrics/phase-quality.jsonl`
- `output/rejected/<phase>/<reason>.jsonl`
- `notes/recent-state.md`

The skill's workflow currently has coverage and unknowns, but not phase metrics,
quarantine, rejected objects, blocker reprocess conditions, or recent-state
updates. This matters because the massive framework treats invariant failures as
stop-and-quarantine events, not just notes.

### P1: Expand Required Workspace Layout Or Delegate It To `init-target`

The skill's required files are valid human deliverables, but they are a subset
of the framework layout. The framework also expects:

- `program-kb/`
- `config/`
- `sources/`
- `assets/`
- `surfaces/`
- `queues/`
- `graph/`
- `metrics/`
- `runbooks/`
- `coverage/`
- broader `output/raw/`, `output/normalized/`, `output/evidence/`,
  `output/rejected/`, `output/http/`, `output/dns/`, and `output/tls/`

The skill does not need to duplicate the full list if it tells the agent to run
`reconfw init-target`, but it should clearly state that manual markdown-only
workspaces are incomplete for framework-backed recon.

### P1: Add Canonical Object Metadata Requirements

The skill asks for evidence-backed claims, but the framework requires every
normalized object to carry structured metadata:

```text
id, type, value, normalized_value, source_refs, raw_evidence_paths,
retrieved_at, first_seen, last_seen, freshness, scope_status, testability,
confidence, owner_evidence, third_party_status, business_relevance,
security_boundary_relevance, risk_score, noise_score, dedupe_key, state,
next_action, blocking_reason, schema_version
```

The skill should add a short rule: when framework-normalized artifacts are
available, preserve raw evidence first and write normalized JSONL records instead
of relying only on prose summaries.

### P1: Add Recursive Recon And Continuous Diff Guidance

The massive framework now includes recursive, policy-gated recon and state
diffing. The skill has source freshness rules but does not instruct the agent to
use:

```bash
uv run reconfw recurse run --workspace <path> --root <root>
uv run reconfw diff state --workspace <path> --previous <jsonl-or-dir> --current <jsonl-or-dir>
```

The skill should add guidance that newly discovered assets are reclassified,
newly in-scope assets re-enter passive enrichment before active probing, stale
evidence expires, and affected active queues are invalidated after policy
changes.

### P1: Add Policy-Gated Fuzz Queue Language Without Turning Recon Into Scanning

The skill correctly blocks fuzzing during normal recon unless explicitly
approved. The framework, however, supports safe fuzz planning and saved ffuf
result normalization behind strong gates. The skill should preserve the
scanner-avoidance doctrine while adding this distinction:

- recon may identify fuzz candidates and write policy-safe queue items
- fuzz execution requires explicit profile, calibration, rate limit, stop
  conditions, allowed payload class, and program permission
- fuzz output can create leads or candidates, never direct findings

This keeps the skill compatible with the framework without making it
scanner-first.

### P1: Add Coverage Benchmark Outputs

The framework tracks broader coverage areas such as WSTG, OWASP API Top 10,
PortSwigger API/GraphQL/WebSocket concepts, platform rules, and target-specific
policy gates. The skill only requires a single `coverage-matrix.md`.

The skill should either require framework coverage outputs under `coverage/` or
state that `reconfw coverage check` is the authoritative coverage gate.

### P1: Add Handoff And Report-Readiness Gate

The skill's final response definition is useful, but the framework now has
first-class handoff behavior. The skill should require:

```bash
uv run reconfw coverage check --workspace <path> --fail-on-blockers
uv run reconfw handoff --workspace <path>
```

If blockers remain, the final response should report the exact blocker count,
accepted gaps, unaccepted gaps, and next action. This prevents a recon run from
looking finished when core gates are still failing.

### P2: Improve Intigriti Lookup Conversion

`intigriti_lookup.py` is useful and handles token safety well, but the skill
still leaves a manual conversion step. Improvements to consider:

- add an option to initialize the target workspace with `reconfw init-target`
- write draft program-kb files from Intigriti API output when fields are present
- write source records that include endpoint, retrieved timestamp, raw path, and
  confidence
- save API failure records as provider/blocker evidence instead of only raising
  runtime errors
- document that heuristic version-id extraction may fail and must be verified
  against saved raw JSON

This would turn Intigriti lookup from evidence collection into a safer framework
ingestion starting point.

### P2: Broaden Secret-Handling Language

The skill handles Intigriti PAT secrecy, but the framework has broader secret
controls. The skill should explicitly say not to store cookie values, bearer
tokens, CSRF tokens, session identifiers, API keys, secret candidates, or private
user data in notes, reports, normalized summaries, HAR summaries, or command
logs. Secret candidates from JavaScript or code search must be recorded as
redacted candidates and must not be validated against real services unless the
program explicitly allows it.

### P2: Add Sub-Agent Governance To The Skill

The workspace rule caps delegated sub-agents at 2-3 per hunt unless the user
explicitly approves more. The skill does not mention this. Add a brief rule that
any delegated recon subtask must have an independent scope and must write
results into durable notes or framework artifacts; sub-agents are not the memory
layer.

### P2: Update `agents/openai.yaml` Default Prompt

The current default prompt is generic:

```text
Use the bounty-recon skill to create or update a precise, evidence-backed recon
map for this authorized target.
```

It should mention the framework path and control-plane gates, for example:

```text
Use the bounty-recon skill and /home/hunterweb/recon-framework as the
policy-gated control plane to create or update an evidence-backed recon map,
program-kb, live-baseline coverage, coverage audit, and handoff notes for this
authorized target.
```

## Suggested Patch Order

1. Update `SKILL.md` Start Here to prefer `reconfw init-target`, program-kb
   validation, coverage audit, and handoff when `/home/hunterweb/recon-framework`
   exists.
2. Update `references/recon-workflow.md` to add framework-backed workspace
   layout, canonical object metadata, metrics/rejection requirements, queue
   semantics, recursive recon/diffing, and handoff gates.
3. Add a short `references/reconfw-integration.md` with command recipes for
   target init, kb ingest/validate, classify, passive collection, live baseline,
   wrapper ingestion, coverage, handoff, and blocker handling.
4. Extend `scripts/intigriti_lookup.py` or add a companion script that converts
   saved Intigriti evidence into draft program-kb files without exposing
   secrets.
5. Update `agents/openai.yaml` so new runs start with the framework-backed
   control plane instead of a markdown-only recon map.

## Bottom Line

The recon skill is not lazy or unsafe, but it is behind the current local
framework. It describes what a high-quality manual recon deliverable should look
like; the framework now implements how that deliverable should be controlled,
validated, measured, audited, and handed off. The main improvement is to make
the skill explicitly drive `reconfw` and treat markdown files as human-facing
summaries of framework-backed evidence, not as the primary source of truth.
