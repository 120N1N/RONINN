# Recon Framework Assessment

Date: 2026-04-30

## Scope Reviewed

- `/home/hunterweb/AGENTS.md`
- `/home/hunterweb/docs/web2-bounty-agent-operating-plan.md`
- `/home/hunterweb/docs/massive-recon-framework.md`
- `/home/hunterweb/docs/massive-recon-framework-execution-plan.md`
- `/home/hunterweb/.codex/skills/bounty-recon/references/recon-workflow.md`
- `/home/hunterweb/recon-framework/`
- `/home/hunterweb/templates/target/`

Secret files under `/home/hunterweb/secrets/` were not read.

## Baseline Assessment

The framework was already functional and conservative. Before changes:

- `uv run pytest` passed with 66 tests.
- `uv run ruff check .` passed.
- The package implemented policy-gated local milestones beyond the README's
  stated "Milestones 0 through 4" status.
- Active behavior was dry-run or fixture-backed by default.
- The policy engine enforced in-scope decisions, exclusions, third-party review,
  required headers, rate profiles, and stale-policy blockers.

The framework still needed improvement because:

- The README understated actual capabilities and did not document later
  milestones or handoff-quality controls.
- `reconfw init-target` did not create the full durable recon deliverable set
  required by the local workflow reference.
- `/home/hunterweb/templates/target/` was missing root-level deliverables such as
  `scope.md`, `business.md`, `architecture.md`, `assets.md`,
  `security-model.md`, `attack-surface.md`, `coverage-matrix.md`, `unknowns.md`,
  and `priority-testing-plan.md`.
- The execution plan required coverage and handoff gates, but the CLI had no
  first-class `coverage check` or `handoff` command.
- There was no automated workspace-level check for missing program-kb fields,
  missing workflow files, normalized-object provenance gaps, live-baseline
  coverage gaps, queued active work, metrics presence, or likely secret leakage
  in notes/reports.

## Improvement Plan Executed

1. Make target scaffolding complete.
   - Add missing recon workflow files to `reconfw init-target`.
   - Preserve existing user-authored notes and only create missing files.
   - Add `features/` to required workspace directories.

2. Make target templates match the workflow.
   - Add root-level target template files and `features/README.md`.

3. Add workspace audit and handoff gates.
   - Add a coverage audit module that checks required directories, required
     deliverables, program-kb validity, normalized-object provenance, baseline
     coverage, active queues, metrics, and likely secret leakage.
   - Write audit findings to `coverage/audit-findings.jsonl`.
   - Render `coverage/coverage-matrix.md` and update generated
     `coverage-matrix.md`.
   - Add handoff behavior that blocks when audit blockers remain unless the
     operator explicitly allows blockers.

4. Expose the checks through the CLI.
   - Add `reconfw coverage check --workspace <path>`.
   - Add `reconfw coverage check --workspace <path> --fail-on-blockers`.
   - Add `reconfw handoff --workspace <path>`.

5. Update documentation and tests.
   - Rewrite `recon-framework/README.md` to match implemented capabilities.
   - Add tests for the new scaffold and audit/handoff behavior.
   - Add cache/coverage paths to `.gitignore`.

## Verification

After implementation:

- `uv run pytest` passed with 70 tests.
- `uv run ruff check .` passed.
- CLI help showed the new `coverage` command group and top-level `handoff`
  command.

## Residual Gaps

- The framework still relies heavily on fixture-backed or dry-run execution for
  active-adjacent capabilities. That is appropriate for safety, but real target
  runners should remain behind explicit policy wrappers.
- The audit is intentionally conservative. It may flag older manually created
  workspaces as incomplete until they are brought onto the standard scaffold.
- The implementation plan still lists future command names such as crawl or
  inventory variants that are not exact aliases in the current CLI.
