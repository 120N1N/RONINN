# Codex Quickstart

Use this when starting Codex in the `hunterweb` workspace.

## Root And Paths

This workspace can run from a VPS path such as `/home/hunterweb` or from a local
checkout such as `/Users/raihan/BugBounty/worfklow/hunterweb`. Set one portable
root variable and use it in commands:

```bash
export HUNTERWEB_HOME="${HUNTERWEB_HOME:-$(pwd)}"
if "$HUNTERWEB_HOME/.local/bin/uv" --version >/dev/null 2>&1; then
  export PATH="$HUNTERWEB_HOME/.local/bin:$PATH"
fi
```

Do not assume `/home/hunterweb` unless that is the actual current checkout.
The bundled `.local/bin` may contain Linux binaries from a VPS export; on macOS
only add it to `PATH` after the command check above succeeds.

## What To Read First

For a normal Codex session:

1. `AGENTS.md`
2. `.codex/skills/bounty-recon/SKILL.md` when the task is target recon
3. `docs/web2-bounty-agent-operating-plan.md`
4. `docs/bug-bounty-operator-guide.md`
5. Active target notes under `bounty/<platform>/<target>/notes/`

Avoid bulk-reading caches, tool histories, session logs, dependency directories,
and secret folders. Read secret values only when the task specifically requires
using the credential, and do not print them.

## Framework Commands

Run framework commands from `recon-framework/`:

```bash
cd "$HUNTERWEB_HOME/recon-framework"
uv run reconfw --help
uv run reconfw init-target --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
uv run reconfw kb validate --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
uv run reconfw coverage check --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
uv run reconfw handoff --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
```

Use `reconfw init-target` as the default scaffold path. It preserves existing
notes and creates missing framework files.

## Intigriti Program Lookup

If only an Intigriti program name is provided and a researcher PAT is configured
locally:

```bash
"$HUNTERWEB_HOME/.codex/skills/bounty-recon/scripts/intigriti_lookup.py" "<program name>" \
  --workspace "$HUNTERWEB_HOME/bounty/intigriti/<target>" \
  --init-target
```

Accepted token sources are environment variables or local secret files:

```text
INTIGRITI_PAT
INTIGRITI_RESEARCHER_PAT
INTIGRITI_PAT_FILE
$HUNTERWEB_HOME/secrets/intigriti_pat
$HUNTERWEB_HOME/secrets/intigriti/pat
~/.config/intigriti/pat
```

Never paste the PAT into prompts, notes, reports, or skill files.

## Target Workspaces

Target data lives under:

```text
bounty/<platform>/<target>/
```

Important files and directories:

```text
program-kb/
notes/rules.md
notes/recon.md
notes/recent-state.md
notes/live-probing.md
notes/traffic-map.md
leads/
primitives/
findings/
reports/
output/
evidence/
metrics/
coverage/
```

For an unknown target, use `bounty/_pending/_scope` only as a temporary holding
workspace. Move to the real platform and target path once scope is known.

## Validation

Quick environment check:

```bash
"$HUNTERWEB_HOME/scripts/codex-doctor.sh"
```

Before handing back framework or skill edits:

```bash
cd "$HUNTERWEB_HOME/recon-framework"
uv run pytest
uv run ruff check .
uv run reconfw --help
```

For Python helper scripts outside the package:

```bash
python3 -m py_compile "$HUNTERWEB_HOME/.codex/skills/bounty-recon/scripts/intigriti_lookup.py"
```

If a command cannot run because a dependency, token, or target detail is missing,
record the exact blocker and the next command or file needed to unblock it.
