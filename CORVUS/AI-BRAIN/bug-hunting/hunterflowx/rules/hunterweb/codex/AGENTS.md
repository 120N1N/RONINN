# Global Codex Instructions

## Scope Of This File

This `.codex/AGENTS.md` applies when Codex is operating inside the `.codex/`
configuration tree. The project-wide source of truth is `../AGENTS.md`; read and
follow it before making workflow, skill, hook, or recon changes.

The `.codex/` tree contains live configuration, logs, history, auth state,
sessions, shell snapshots, hooks, and skills. Do not bulk-read or edit
`history.jsonl`, `sessions/`, `log/`, `logs_*.sqlite*`, `auth.json`, or shell
snapshots unless the user specifically asks for that artifact. For normal
maintenance, work on `AGENTS.md`, `config.toml`, `hooks.json`, `hooks/`,
`rules/`, and `skills/`.

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

Do not claim to expose private chain-of-thought. Apply the same discipline internally by checking that the target, files, dates, and assumptions are concrete before choosing tools or editing files.
