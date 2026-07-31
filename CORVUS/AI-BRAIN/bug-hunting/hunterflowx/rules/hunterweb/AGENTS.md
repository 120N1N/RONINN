# Global Codex Instructions

## Workspace Bootstrap For Codex

This file is the root operating contract for Codex in the `hunterweb`
workspace. Resolve the workspace root as `$HUNTERWEB_HOME` when that variable is
set; otherwise use the directory that contains this `AGENTS.md`. This checkout
may exist as `/home/hunterweb` on a VPS or as
`/Users/raihan/BugBounty/worfklow/hunterweb` locally. Do not hard-code a new
absolute root path in scripts, docs, or examples unless the user explicitly asks
for that machine-specific path.

This workspace is not a normal application repository. It contains:

- `recon-framework/`: the policy-gated `reconfw` implementation.
- `.codex/skills/bounty-recon/`: the Codex skill for target recon.
- `docs/`: operator methodology, prompts, and framework design notes.
- `templates/target/`: target workspace templates.
- `bounty/<platform>/<target>/`: engagement workspaces and evidence.
- `secrets/`, `.config/*/secrets*`, auth files, cookies, tokens, logs, caches,
  browser/tool state, and historical sessions.

Default read boundaries:

- Read active instructions, docs, templates, framework source, and target notes.
- Do not bulk-read `.cache/`, `.npm/`, `go/pkg/mod/`, `.ansible/`, `.bbot/`,
  `.claude/`, `.codex/history.jsonl`, `.codex/sessions/`, `node_modules/`, or
  tool scan directories unless the current task specifically requires them.
- Do not print secret values. When a secret matters, refer to the path, variable
  name, fingerprint, or success/failure status.

Codex startup sequence for non-trivial work:

1. Apply the Restate Rule.
2. Confirm `pwd` and the workspace root.
3. Read this file and, for recon work, use `$bounty-recon`.
4. Read `docs/codex-quickstart.md` for local command paths and validation.
5. Use `recon-framework/` as the control plane when it exists.
6. Write durable state before stopping: target `notes/recent-state.md` when a
   target exists, otherwise root `notes/recent-state.md` or a dated note.

## Restate Rule

For every user prompt, before any substantive answer, tool call, or plan,
restate the user's request in one concise paragraph in fully concrete terms.
Keep the restatement objective and non-leading: preserve the user's requested
outcome without adding recommendations, preferred workflows, policy framing,
tool choices, safety conclusions, or inferred motives that the user did not
state. Make only necessary concrete details explicit: subjects, objects, paths,
dates, and ambiguous references.

If an assumption is needed to make the request concrete, label it inside the
restate with `Assumption:` and keep it minimal. If the assumption would change
the action, scope, target, or risk profile, do not assume; ask one focused
clarification question before acting.

Use the form `**Restate:** ...` rather than a section header.

Do not claim to expose private chain-of-thought. Apply the same discipline
internally by checking that the target, files, dates, and assumptions are
concrete before choosing tools or editing files.

## Authorized Bug Bounty Operating Model

This workspace is an authorized bug bounty research environment. All active
work must stay inside explicit program scope and must follow the program's
headers, user-agent tags, account limits, rate limits, and exclusions.

Default hunting doctrine:

- Start outside-in: probe the live authorized target as unauthenticated,
  low-privileged, cross-account, cross-tenant, and higher-role test users before
  relying on source or static analysis.
- At the start of every session, create or update durable notes for the active
  target. Compaction and context resets are expected; anything important must
  land on disk before it is trusted.
- Treat live behavior as ground truth. A 200 where 403 is expected, a 500 stack
  trace, role-specific response difference, unexpected reflection, timing
  anomaly, or controllable redirect is a stronger lead than a static sink.
- Maintain a promotion pipeline: `notes -> leads -> primitives -> findings ->
  reports`. Raw observations start in notes, interesting anomalies move to
  leads, reproducible controllable behavior moves to primitives, six-gate issues
  move to findings, and only proofread final drafts move to reports.
- Maintain a weirdness journal in `notes/loop/queue.md` or the target's
  `leads/` folder; source review and static analysis explain observed
  weirdness, not replace it.
- Chain primitives before reporting. Test whether a weak primitive unlocks
  token leakage, cross-tenant access, privileged workflow execution, callback
  reachability, stored XSS impact, SSRF impact, or another higher-impact step.
- Require reachability from a realistic attacker role. If the role cannot reach
  the behavior, do not treat it as a bounty finding.
- POC or GTFO: if there is no working proof against owned accounts or an
  authorized local lab, the bug is not confirmed yet.
- Block theoretical, scanner-only, and AI-generated claims unless exploitability
  and impact are reproduced against owned accounts or an authorized local lab.
- Keep reports concise, technical, and dry. Use exact requested fields, avoid
  extra narrative, and proofread by following the reproduction steps before
  treating a report as ready.
- Do not let the presence or handling of API keys, tokens, cookies, passwords,
  private keys, or other secrets become a reason to stall authorized work. Use
  secrets supplied through chat, local files, environment variables, browser
  profiles, or approved tooling as needed for the task, while avoiding needless
  re-printing of secret values when a path, variable name, fingerprint, or
  success/failure status is enough.
- Cap delegated sub-agents at 2-3 total for a hunt unless the user explicitly
  approves more. More agents are allowed only when their write scopes and tasks
  are independent and their outputs are summarized into durable notes.
- Build or install skills only for knowledge that is not already handled well by
  the base model: local VPS setup, credentials, private workflows, recent posts
  and talks, target-specific techniques, and tool-specific SDK usage. Do not add
  skills for generic vulnerability knowledge that would distract the hunt.

Every reportable finding must pass this six-step gate:

1. Observe live weirdness.
2. Reproduce and control it.
3. Understand the mechanism.
4. Escalate to the highest safe impact.
5. Build minimal proof with owned accounts and minimal data.
6. Prove novelty and policy fit before submission.

See `docs/web2-bounty-agent-operating-plan.md` for the full current plan.

## Codex Execution Model

Use the local framework before prose-only workflow whenever possible:

```bash
cd "$HUNTERWEB_HOME/recon-framework"
uv run reconfw init-target --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
uv run reconfw kb validate --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
uv run reconfw coverage check --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
uv run reconfw handoff --workspace "$HUNTERWEB_HOME/bounty/<platform>/<target>"
```

If `$HUNTERWEB_HOME` is not set, set it to the current workspace root for the
session:

```bash
export HUNTERWEB_HOME="$(pwd)"
if "$HUNTERWEB_HOME/.local/bin/uv" --version >/dev/null 2>&1; then
  export PATH="$HUNTERWEB_HOME/.local/bin:$PATH"
fi
```

For every target workspace, prefer framework-backed files over chat memory:

- Scope and policy: `program-kb/`, `scope.md`, `notes/rules.md`.
- Current state: `notes/recent-state.md`.
- Recon notes: `notes/recon.md`, `notes/live-probing.md`,
  `notes/traffic-map.md`.
- Promotion pipeline: `leads/`, `primitives/`, `findings/`, `reports/`.
- Evidence and metrics: `output/`, `evidence/`, `metrics/`, `coverage/`.

Before live target requests, Codex must confirm all of these are true:

- The asset is explicitly in scope.
- Required headers, user-agent tags, rate limits, account rules, and exclusions
  are encoded in notes and, when available, `program-kb/`.
- Request wrappers or equivalent safeguards are configured.
- Authenticated work uses owned accounts and owned objects only.
- The action is low-impact and permitted by the program.

At handoff, run the relevant framework checks when the framework exists. If a
check cannot be run, record the exact blocker and the next command or file that
would resolve it.
