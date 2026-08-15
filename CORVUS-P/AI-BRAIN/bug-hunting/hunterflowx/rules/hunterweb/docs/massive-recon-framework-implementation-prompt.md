# Massive Recon Framework Implementation Prompt

Use this prompt to execute `/home/hunterweb/docs/massive-recon-framework-execution-plan.md` properly.

```text
You are implementing the massive authorized bug bounty recon framework in /home/hunterweb.

Primary documents:
- Read first: /home/hunterweb/docs/massive-recon-framework-execution-plan.md
- Also use: /home/hunterweb/docs/massive-recon-framework.md
- Also use: /home/hunterweb/docs/web2-bounty-agent-operating-plan.md
- Do not modify /home/hunterweb/docs/massive-recon-framework.md unless explicitly asked.

Goal:
Execute the implementation plan carefully, milestone by milestone, building /home/hunterweb/recon-framework/ into a practical, testable, policy-gated recon framework.

Execution rules:
1. Start by reading the execution plan and extracting the current milestone, dependencies, acceptance gates, and safety requirements.
2. Build in strict milestone order. Do not skip ahead to active collectors, fuzzing, authenticated testing, or reporting before policy, schemas, storage, evidence, metrics, and tests are working.
3. Preserve the safety model:
   - unknown assets are passive-only
   - out-of-scope assets are blocked
   - active requests require in_scope plus an allowed action
   - fuzzing requires explicit profile, calibration, rate limits, and stop conditions
   - authenticated testing requires owned-account context
   - scanner-only output cannot become a finding
4. Prefer small, complete implementation slices over broad unfinished scaffolding.
5. For each milestone:
   - define/update schemas first
   - add fixtures
   - add tests for success, blocked, rejected, stale, and safety cases
   - implement storage and normalization
   - add CLI dry-run behavior before live behavior
   - emit metrics and rejected-object records
   - update recent-state/coverage outputs where applicable
   - run acceptance tests
6. Never run live target-touching commands unless the program-kb, safe-actions, rate-limits, headers/user-agent, scope decision, and dry-run policy decision all allow it.
7. Do not store secrets in notes, reports, normalized summaries, command logs, or fixtures. Store only env var names or secret file paths.
8. Preserve raw evidence before normalization. Normalized objects must include source_refs, raw_evidence_paths, scope_status, testability, confidence, state, next_action, and schema_version.
9. Keep JSONL append-friendly and SQLite rebuildable from JSONL/raw evidence.
10. All CLI commands that can touch a target must support --dry-run and print allow/block policy reasoning.
11. If any safety invariant fails, stop the affected run, quarantine output, write the blocker to notes/recent-state.md and metrics/phase-quality.jsonl, and do not continue that path automatically.
12. Treat missing provider API keys as provider_unavailable, not as a framework failure.
13. Do not create findings directly from tool output. Use notes -> leads -> primitives -> findings -> reports with the six-step gate.

Initial target implementation slice:
Implement the first safe vertical slice:
- init-target
- program-kb ingest and validate
- classify passive subdomain fixture data
- write normalized host objects
- generate safe_probe_queue only for in-scope assets
- run mocked liveness baseline
- write metrics, evidence refs, rejected records, and recent-state

Quality bar:
- The code must be executable locally.
- Tests must cover the design acceptance tests from the execution plan.
- Each milestone must pass its acceptance gates before moving on.
- Keep changes scoped and avoid unrelated refactors.
- Use existing repo patterns if present.
- Use clear module boundaries matching the proposed layout.
- After each implementation slice, report:
  - files changed
  - milestone progress
  - tests run and results
  - acceptance gates passed
  - blockers or safety constraints
  - exact next recommended step

Start now by inspecting the current workspace, checking whether /home/hunterweb/recon-framework/ exists, reading the execution plan, and implementing Milestone 0 plus the smallest necessary foundation for Milestone 1 only if Milestone 0 passes.
```
