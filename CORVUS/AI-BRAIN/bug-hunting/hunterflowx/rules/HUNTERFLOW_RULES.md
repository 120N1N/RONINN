# Hunterflowx Rules

Hunterflowx combines three native layers:

```text
1. Hunterflowx runtime and dashboard
2. hunterweb operating discipline
3. GPTxOPUS source-grounded A01-A10 methodology
```

The exact source rule files are vendored into this directory so an agent can
work without reopening the original folders.

## Mandatory Rule Sources

Read these before serious hunting:

```text
rules/hunterweb/AGENTS.md
rules/hunterweb/CLAUDE.md
rules/hunterweb/docs/web2-bounty-agent-operating-plan.md
rules/hunterweb/docs/bug-bounty-operator-guide.md
rules/hunterweb/docs/codex-quickstart.md
rules/hunterweb/recon-framework/README.md

rules/gptxopus/AGENTS.md
rules/gptxopus/workflow/operating_model.md
rules/gptxopus/workflow/source_grounding_protocol.md
rules/gptxopus/workflow/browser_caido_burp_loop.md
rules/gptxopus/workflow/a01_a10_baseline.md
rules/gptxopus/checklists/evidence_pack.md
rules/gptxopus/checklists/endpoint_coverage.md
rules/gptxopus/checklists/owasp_a01_a10_coverage.md
```

## Operating Contract

Use hunterweb for:

```text
restate rule
authorized scope discipline
live behavior as ground truth
notes -> leads -> primitives -> findings -> reports
weirdness journal
chain primitives before reporting
POC or GTFO
six-step reportability gate
framework-backed handoff and coverage checks
```

Use GPTxOPUS for:

```text
source-grounded baseline coverage
A01-A10 method coverage
manual test-card format
creative/off-checklist leads
evidence refs before status promotion
retest matrix
report QA
source material and source pattern registry checks
```

Use Hunterflowx for:

```text
bbf event ledger
bbf build graph state
bbf queue command center
bbf angle-plan and angle-exec
bbf evidence-score
bbf judge
bbf source-verify
bbf risk-prioritize
bbf domain-plan and domain-verify
dashboard and Neo4j views
```

## Conflict Resolution

When rules differ:

```text
stricter scope rule wins
stricter safety rule wins
stricter evidence rule wins
manual browser/Caido/Burp validation wins over source-only claims
durable event/evidence state wins over chat memory
```

Do not downgrade `tested_secure`, `finding_candidate`, or `confirmed` from
source-only reading. Those statuses require evidence refs and reproducible proof
from owned accounts or an authorized lab.

## Dashboard Rule

The dashboard UI in `dashboard/` is the canonical Hunterflowx operator surface.
Keep it stable, consistent, and professional unless the operator explicitly
requests a redesign.
