# Command Center And Proof Gates

This layer turns the workflow from passive visibility into controlled
operations.

## Command Center

Open:

```text
http://127.0.0.1:5173/command
```

Back-end data:

```text
data/run_queue.json
```

CLI:

```bash
bbf queue seed
bbf queue list
bbf queue approve <task-id>
bbf queue run <task-id>
bbf queue run-next
```

Active tasks keep `approval: pending` until the operator approves them. This is
intentional. Recon, scoring, judging, and reporting tasks can run without active
approval, but request-sending tasks must be approved.

## Safety Policy

Executor requests are checked against:

```text
data/safety_policy.json
```

Default policy is strict:

```text
allow_hosts: []
max_rps: 10
mode: enforce
```

Fill `allow_hosts` before live testing. If it is empty, `bbf angle-exec` blocks
active requests by default.

## Caido Bridge

Two modes are supported:

```text
proxy mode    -> bbf angle-exec --transport caido --proxy http://127.0.0.1:<port>
native import -> bbf caido import --source caido --file history.har
```

`bbf caido status` detects whether `caido-cli` or `caido` exists on PATH and
prints the per-engagement launch command. Import supports HAR and simple JSON
history exports. Imported requests become evidence events and are redacted for
secret-bearing headers.

## Semantic Judge

`bbf judge` now checks more than file presence:

```text
baseline request/evidence
mutated request/evidence
negative control/evidence
read-back evidence
semantic status/body diff
ownership or role context
fresh repro pass
saved evidence files
```

A finding candidate with strong evidence but no fresh repro is intentionally
kept as `judge_candidate`, not `judge_reportable`.

## Fresh Repro

Fresh replay needs new session/account headers:

```bash
bbf fresh-repro --test-id <id> --headers-file .private/fresh-session.json --allow-active
```

If replay cannot run automatically, use a manual proof and mark it:

```bash
bbf fresh-repro --test-id <id> --mark-pass --evidence-path evidence/... --reason "manual browser/Burp replay passed"
```

## Report Lifecycle

Reports are tracked in:

```text
data/report_lifecycle.json
```

Create a draft:

```bash
bbf report-lifecycle draft --test-id <id> --title "Finding title"
```

Submit/triage/accept states are blocked when the proof gate is incomplete.
