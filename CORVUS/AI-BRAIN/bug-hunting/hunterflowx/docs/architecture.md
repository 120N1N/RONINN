# Architecture

This workflow is a control plane for AI-assisted bug bounty work.

## Components

```text
AI / human operator / importer
  -> events.jsonl
  -> build_graph.py
  -> graph_state.json
  -> dashboard
  -> coverage and gap review
```

## Why This Exists

AI fails in bug bounty when it:

- scans too broadly and returns generic findings
- stops after the first dead end
- claims source-only vulnerabilities as confirmed
- cannot show what it tested
- loses context between endpoints, JS files, fingerprints, and retests

This workflow fixes that with durable state.

## Core State Files

| File | Purpose |
|---|---|
| `data/events.jsonl` | append-only action history |
| `data/graph_state.json` | generated dashboard graph |
| `coverage-matrix.md` | human review of endpoint/test coverage |
| `multi-angle-coverage.md` | per-endpoint angle coverage |
| `source-file-queue.md` | one-file-at-a-time source review queue |
| `source-reviews/` | per-file source-to-flow artifacts |
| `domain-depth/` | WP/on-prem/mobile domain-specific checks and reviews |
| `test-ledger.md` | detailed testing record |
| `notes/loop/queue.md` | active weirdness and recursive loop queue |
| `notes/loop/log.md` | what was actually tried |
| `evidence/` | runtime proof |

## Trust Boundaries

Do not trust:

- chat-only claims
- scanner-only output
- source-only exploit claims
- screenshots not linked to tests
- verdicts without evidence

Trust:

- scoped request/response evidence
- browser-visible state change
- owned-account comparison
- replayable PoC in authorized lab
- event and ledger trail that matches evidence

## Source-To-Flow Layer

When source exists, the architecture adds this mandatory layer:

```text
source-file-queue.md
  -> source-reviews/<file-id>.md
  -> source_file_read
  -> source_flow_linked
  -> attack_surface_mapped
  -> endpoint_angle_planned
  -> source_completeness_reviewed
  -> endpoint_angle_tested
  -> evidence_added
  -> verdict_set
  -> chain_candidate_added / attack_path_expanded
```

This prevents AI from reading a few grep hits and pretending it understands the
target. Source files must be read one by one, connected to runtime endpoints,
and converted into multi-angle tests.

## Recommended Integration

Use this folder as the operator-facing final workflow.

When deeper recon automation is needed, run `hunterweb/recon-framework` from its
own workspace and import or mirror its output into this workflow as events.

When attack-path methodology is needed, use `hunterweb` live-behavior-first
hunting plus `GPTxOPUS` source-grounded test cards. Keep all attack paths split
between hypothesized, queued, tested, evidence-backed, and reportable states.

When report quality is needed, apply `GPTxOPUS` source/evidence discipline.

When endpoint depth is needed, run `bbf angle-plan full` or `bbf owasp-plan`
without `--skip-angle-plan`. The graph must show `planned_angles`; otherwise
multi-angle coverage is only a written rule, not executable workflow state.

When runtime validation is needed, run `bbf angle-exec` through HTTP, browser,
Burp, or Caido. It writes evidence and `endpoint_angle_tested`, then rebuilds the
graph so `tested_angles` reflects executed work.

When evidence is ready for review, run `bbf evidence-score`. It writes
`evidence_reviewed`, creates a review artifact, and updates quality metrics in
the dashboard.

When reportability needs a judgement, run `bbf judge`. It reads the same
evidence package, checks baseline/mutation/negative/read-back/redaction/verdict
coherence, writes `evidence_judged`, and separates reportable evidence from
candidate or needs-evidence state.

When source is available, run `bbf source-verify --source-root <path>`. It
checks important-file inventory against per-file review artifacts and source
events, writes `source_completeness_reviewed`, and updates source completeness
metrics in the dashboard.

When endpoint count is high, run `bbf risk-prioritize`. It reads the same event
ledger, ranks endpoints by testing value, writes `endpoint_prioritized` and
`risk_prioritization_reviewed`, updates `priority-testing-plan.md`, and exposes
P0/P1 work in the dashboard.

When the target is domain-specific, run `bbf domain-plan` and
`bbf domain-verify`. The domain layer ports Hunterflowx internal profile rules
into the same control plane:

```text
wp      -> hunterflowx-domain-profile -> platform routing, WP hooks, nonce/capability, sanitizer, local lab
onprem  -> hunterflowx-domain-profile -> target-intel, sandbox, source/current, ranked one-file artifacts
mobile  -> hunterflowx-domain-profile -> app package, device proxy, decompile, mobile API, WebView, Frida/device proof
```

Domain checks become graph nodes and dashboard metrics. They still feed into the
same runtime evidence, scorer, judge, and verdict gates.
