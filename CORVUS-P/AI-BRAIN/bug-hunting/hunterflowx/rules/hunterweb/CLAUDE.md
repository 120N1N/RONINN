# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this directory is

Not a single application — it is a multi-program **authorized bug-bounty research workspace**. Two layers:

1. **Control plane**: `recon-framework/` — a Python 3.12 / `uv` package that exposes the `reconfw` CLI. It is policy-gated and fails closed on scope, headers, rate, account, and evidence rules. Treat it as the canonical way to do recon, not a scratch tool.
2. **Engagements**: `bounty/<platform>/<target>/` — one workspace per target, scaffolded from `templates/target/` (or `reconfw init-target`). All durable state for an active hunt lives here: `scope.md`, `notes/rules.md`, `notes/recent-state.md`, `program-kb/`, `leads/`, `primitives/`, `findings/`, `reports/`, `output/`, `evidence/`, `coverage/`, `metrics/`, `scripts/`.

The workspace root may be `$HUNTERWEB_HOME` on a VPS or this local checkout. `AGENTS.md` resolves the root — never hard-code an absolute path in scripts or docs.

## Operating contract (mandatory)

[AGENTS.md](AGENTS.md) is the authoritative contract for working in this directory. Read it before any non-trivial task. The rules that bind every reply:

- **Restate Rule** ([.claude/CLAUDE.md](.claude/CLAUDE.md), AGENTS.md): every user prompt and every internal reasoning step must be restated in fully concrete terms (subjects, objects, paths, dates, assumptions) **before** answering or calling a tool. Use the form `**Restate:** ...` in user-facing text. If an assumption would change scope or risk, ask one focused clarification instead of assuming.
- **Six-step finding gate**: observe → reproduce → understand → escalate → minimal proof on owned accounts → prove novelty/policy fit. Skipping a step disqualifies the finding.
- **Promotion pipeline**: `notes → leads → primitives → findings → reports`. Raw observations never skip to findings; scanner output never directly becomes a finding.
- **POC or GTFO**: no working proof against owned accounts (or an authorized local lab) means the bug is not confirmed. Block theoretical or scanner-only claims.
- **Per-program rules live in the target's `notes/rules.md`** — re-read before any active request. Required headers, UA tags, rate limits, account scope, exclusions all come from there.
- **≤ 2–3 sub-agents per hunt** without explicit user approval, and only when their write scopes are independent.
- **Secrets**: never print values. Reference path, variable name, fingerprint, or success/failure status only. Tokens live under `secrets/<platform>/<program>/...` (chmod 600) — see [secrets/intigriti/](secrets/intigriti/).
- **Read boundaries**: do not bulk-read `.cache/`, `.npm/`, `go/pkg/mod/`, `.ansible/`, `.bbot/`, `.claude/`, `.codex/history.jsonl`, `.codex/sessions/`, `node_modules/`, or tool scan directories unless the task specifically requires them.
- **No destructive / takeover / state-changing actions** without explicit user approval, even when a bug enables them — describe the capability and stop.

## High-level architecture

### `recon-framework/` — the `reconfw` control plane

Typer CLI (`src/reconfw/cli.py`) backed by:

- `pipeline/` — collectors, audit, DNS, baseline, recursive, exposure, graph, extraction, wordlists, diffing, fuzz, mapping, reporting (one module per milestone, see [recon-framework/README.md](recon-framework/README.md) for the milestone list).
- `collectors/` — adapters per source (`subfinder`, `amass`, `bbot`, `crtsh`, `commoncrawl`, `urlscan`, `virustotal`, `securitytrails`, `otx`, `github`, `gitlab`).
- `exposure/` — `fofa`, `binaryedge`, `criminalip`, `leakix`, `censys`, behind a registry.
- `models/` — Pydantic canonical models (assets, baseline, dns, evidence, exposure, extraction, fuzz, graph, mapping, program, queues, reporting, wordlists).
- `storage/` — `evidence_store`, `jsonl`, `objects`, `sqlite`. Raw evidence and provenance are preserved for every promoted object.
- `kb.py`, `workspace.py`, `paths.py`, `constants.py` — program-kb ingestion, workspace scaffolding, path resolution.

Safety invariants enforced by the framework: out-of-scope assets cannot enter active queues; active actions require `in_scope` + allowed safe action + rate profile + required headers; fuzz needs a calibrated profile and stop conditions; secret candidates are redacted, never validated.

### `templates/target/` — per-target scaffold

What `reconfw init-target` writes (existing user-authored notes are preserved). Same shape used by `bounty/intigriti/dropbox/`. Key files (full list in [recon-framework/README.md](recon-framework/README.md#workspace-scaffold)):

- Scope/policy: `scope.md`, `program-kb/`, `notes/rules.md`.
- Live state: `notes/recent-state.md` (handoff between sessions), `notes/loop/{queue,log}.md`.
- Recon: `notes/recon.md`, `notes/live-probing.md`, `notes/traffic-map.md`.
- Promotion: `leads/`, `primitives/`, `findings/`, `reports/`.
- Evidence: `output/`, `output/live-probes/`, `evidence/`, `metrics/`, `coverage/`.

### `bounty/<platform>/<target>/`

Currently scaffolded targets:

- [bounty/intigriti/dropbox/](bounty/intigriti/dropbox/) — Intigriti Dropbox program, scaffold populated.
- [bounty/intigriti/signicat/](bounty/intigriti/signicat/), [bounty/atlassian/cloud/](bounty/atlassian/cloud/), [bounty/twilio/sendgrid/](bounty/twilio/sendgrid/), [bounty/nasa/vdp/](bounty/nasa/vdp/) — engagement folders.
- [bounty/_pending/_scope/](bounty/_pending/_scope/) — placeholder workspace for programs whose scope has not yet been ingested. Wrappers fail-closed until `config/target.env` is filled.

Loose top-level cookie files like [bounty/dropbox/](bounty/dropbox/) are stash, not a scaffolded target.

### `docs/` — methodology and plan

- [docs/web2-bounty-agent-operating-plan.md](docs/web2-bounty-agent-operating-plan.md) — full current operating plan referenced from AGENTS.md.
- [docs/bug-bounty-operator-guide.md](docs/bug-bounty-operator-guide.md) — start-to-finish operating guide.
- [docs/operator-prompts.md](docs/operator-prompts.md) — prompt library for hunt phases.
- [docs/massive-recon-framework.md](docs/massive-recon-framework.md), `…-execution-plan.md`, `…-implementation-prompt.md` — framework design notes.
- [docs/recon-framework-assessment-2026-04-30.md](docs/recon-framework-assessment-2026-04-30.md), [docs/recon-skill-assessment-2026-05-01.md](docs/recon-skill-assessment-2026-05-01.md) — dated capability/gap audits.

### `.codex/skills/bounty-recon/` — Codex recon skill

Invoked as `$bounty-recon` per AGENTS.md startup sequence. Has its own `SKILL.md`, `scripts/`, `references/`, `agents/`. Mirrors the Claude operating doctrine; useful as a reference even when working under Claude Code.

## Common commands

All `reconfw` commands run from `recon-framework/` via `uv`:

```bash
# Setup (one time per shell, when $HUNTERWEB_HOME is unset)
export HUNTERWEB_HOME="$(pwd)"
export PATH="$HUNTERWEB_HOME/.local/bin:$PATH"

cd "$HUNTERWEB_HOME/recon-framework"

# Dev checks
uv run pytest                                    # full suite
uv run pytest tests/test_workspace.py            # one file
uv run pytest tests/test_workspace.py::test_init # one test
uv run pytest -k recursive                       # by keyword
uv run ruff check .                              # lint (line-length 100)
uv run reconfw --help                            # discover CLI surface

# Per-target lifecycle (paths use $HUNTERWEB_HOME/bounty/<platform>/<target>)
uv run reconfw init-target --workspace <path>
uv run reconfw kb validate --workspace <path>
uv run reconfw classify asset --workspace <path> --value <host>
uv run reconfw collect passive --workspace <path> --root <root> --collectors subfinder,amass,bbot
uv run reconfw recurse run --workspace <path> --root <root>
uv run reconfw baseline --workspace <path> --queue queues/safe-probe.jsonl
uv run reconfw extract endpoints --workspace <path>
uv run reconfw map apis --workspace <path>
uv run reconfw wordlists generate --workspace <path>
uv run reconfw fuzz queue --workspace <path> --target <url> --profile <profile.json> --wordlist <wl>
uv run reconfw graph build --workspace <path>
uv run reconfw coverage check --workspace <path> --fail-on-blockers
uv run reconfw handoff --workspace <path>
```

[recon-framework/README.md](recon-framework/README.md#commands) has the full list of subcommands.

Misc workspace-level helpers:

- [`runauto.sh <session> [cmd...]`](runauto.sh) — `screen` session attach/create wrapper. `RUNAUTO_DETACHED=1` for detached creation.

## Where to look first

In this order:

1. [AGENTS.md](AGENTS.md) — operating contract.
2. [notes/recent-state.md](notes/recent-state.md) — workspace-level handoff (current target, phase, blockers).
3. `bounty/<platform>/<target>/notes/recent-state.md` — per-target handoff (preferred over the workspace-level one when a target is active).
4. `bounty/<platform>/<target>/notes/rules.md` — program-binding rules (headers, rate, accounts, exclusions).
5. [recon-framework/README.md](recon-framework/README.md) — capability inventory and CLI surface.
6. [docs/web2-bounty-agent-operating-plan.md](docs/web2-bounty-agent-operating-plan.md) — current hunt plan.

## Memory location

Persistent memory about the user and engagements:

- Local checkout: `~/.claude/projects/-Users-raihan-BugBounty-worfklow-hunterweb/memory/`
- VPS checkout (`/home/hunterweb`): `~/.claude/projects/-home-hunterweb/memory/`

Check `MEMORY.md` in the active path before assuming facts about scope or prior decisions.
