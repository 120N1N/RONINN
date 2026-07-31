# Source Audit Playbook

Use the Hunterflowx source/on-prem domain gates for source-heavy audits.

For on-prem or source-heavy products, make the specialized gates explicit:

```bash
../../../bin/bbf onprem-plan
../../../bin/bbf source-verify --source-root <extracted-source-root> --queue-missing
../../../bin/bbf domain-verify --domain onprem
```

## Rules

- one file at a time
- artifact before next file
- read the whole current file, not only grep hits
- link file -> endpoint -> data flow -> sink/source before planning exploit tests
- target-intel citations before claims
- at least five hypotheses per file
- at least one multi-angle endpoint plan per linked endpoint when applicable
- at least one chaining question per meaningful primitive
- PoC before report
- source reading alone is not confirmed
- vendor binary or product install runs only in a sandbox
- target-intel citations are mandatory before claims
- evidence-score and judge are mandatory before report

## One-File Gate

Before opening the next file, the current file must have an artifact in:

```text
source-reviews/<file-id>.md
```

The artifact must include:

```text
RESTATE-OK
FILE-PURPOSE
ENTRYPOINTS
TRUST-BOUNDARIES
ROUTES-ENDPOINTS
DATA-FLOW
SINKS-SOURCES
AUTHZ-AUTHN
ATTACK-SURFACE
MULTI-ANGLE-PLAN
CHAIN-CANDIDATES
EVENTS-WRITTEN
OPEN-GAPS
```

If any section is unknown, write `unknown` and create a concrete `gap_found` or
`blocked` event. Do not silently skip it.

After a source-review batch, run:

```bash
../../../bin/bbf source-verify --source-root <extracted-source-root> --queue-missing
```

The verifier checks file inventory, source events, review artifact completeness,
flow linkage, attack-surface mapping, and endpoint angle planning. Do not call
source coverage complete while it reports `source_incomplete` or missing review
artifacts.

## Flow Linking

For every meaningful source file, connect it to the target flow:

```text
request/route
  -> middleware/auth/session
  -> controller/handler
  -> service/business logic
  -> model/query/cache/file/external call
  -> response/template/client state
```

For frontend files:

```text
page/component
  -> user action
  -> client route
  -> API call
  -> parameter/body/header
  -> backend endpoint
  -> state/evidence to verify
```

For config/infrastructure files:

```text
config
  -> exposed service/secret/routing behavior
  -> reachable endpoint or trust boundary
  -> attack surface or hardening note
```

## Source-To-Endpoint Events

Use these events while auditing source:

```text
source_file_queued
source_file_read
source_flow_linked
attack_surface_mapped
endpoint_angle_planned
chain_candidate_added
source_completeness_reviewed
```

Runtime proof still needs:

```text
test_started
payload_attempted
control_request_sent
evidence_added
verdict_set
```

Domain-specific proof also needs:

```text
domain_check_completed
domain_depth_reviewed
```

## Source Structure

```text
artifacts/        raw installers/configs
source/current/   extracted source to audit
source/previous/  previous version for diff
target-intel/     scope, docs, known risks, by-design behavior
findings/         per-file artifacts
source-reviews/   one-file source reading artifacts
reports/          drafts/submitted/archived
```

## Best Use

Use this when AI scan becomes generic. Narrow the unit to one file, one flow,
and one proof path.
