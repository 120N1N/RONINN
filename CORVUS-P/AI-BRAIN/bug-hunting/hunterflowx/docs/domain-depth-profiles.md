# Domain Depth Profiles

Generic Web/API coverage is not enough for every target. `bbf domain-plan` adds
domain-specific gates for surfaces that need their own methodology:

```bash
../../../bin/bbf domain-plan wp
../../../bin/bbf domain-plan onprem
../../../bin/bbf domain-plan mobile
../../../bin/bbf domain-plan all
```

Shortcut commands:

```bash
../../../bin/bbf wp-plan
../../../bin/bbf onprem-plan
../../../bin/bbf mobile-plan
```

## Profiles

| Profile | Source workflow | What it adds |
|---|---|---|
| `wp` | Hunterflowx internal domain gate | Patchstack/Wordfence routing, hook inventory, nonce/capability checks, REST permission callback, sanitizer context, SQL/data layer, upload/URL handling, options/usermeta writes, local WP lab PoC |
| `onprem` | Hunterflowx internal domain gate | target-intel, sandbox install, source/current extraction, ranked one-file triad, config/defaults, auth/session model, admin API/service ports, file/import/export/command surfaces, version diff, lab proof |
| `mobile` | Hunterflowx internal domain gate | app/package inventory, device proxy capture, static decompile, mobile-only API diff, token storage, deep links/exported components, WebView bridge, local data/secrets, Frida/runtime proof, mobile evidence package |

## Endpoint-Aware Planning

When a domain profile is tied to an endpoint, it also creates endpoint-specific
angle events:

```bash
../../../bin/bbf domain-plan wp \
  --asset-id asset-plugin \
  --endpoint-id ep-wp-ajax-export \
  --method POST \
  --path /wp-admin/admin-ajax.php
```

This writes:

```text
domain-depth/<domain>-plan.md
data/events.jsonl       # domain_profile_loaded, domain_check_planned, endpoint_angle_planned
data/graph_state.json
```

## Completing A Check

A planned check is incomplete until linked evidence exists or the operator marks
it complete:

```bash
../../../bin/bbf event domain_check_completed \
  --domain wp \
  --check-id wp-capability-nonce \
  --status domain_complete \
  --evidence-path evidence/burp/wp-capability-nonce.txt
```

If a check is blocked or out of scope, close it honestly:

```bash
../../../bin/bbf event domain_check_completed \
  --domain mobile \
  --check-id mobile-frida-runtime-proof \
  --status blocked \
  --reason "program disallows instrumentation"
```

## Verification

Run the verifier after every domain batch:

```bash
../../../bin/bbf domain-verify --domain wp
../../../bin/bbf domain-verify --domain onprem
../../../bin/bbf domain-verify --domain mobile
../../../bin/bbf domain-verify --domain all
```

The verifier writes:

```text
domain-depth/domain-depth-review.md
domain-depth/<domain>-review.md
data/domain_depth.json
data/events.jsonl       # domain_depth_reviewed
data/graph_state.json
```

Dashboard metrics:

```text
domain_profiles_total
domain_checks_planned
domain_checks_complete
domain_checks_partial
domain_checks_missing
domain_depth_avg
domain_wp_score
domain_onprem_score
domain_mobile_score
```

## Rule

Domain profiles do not replace the final evidence gate.

```text
domain-plan -> domain-specific checks -> evidence -> evidence-score -> judge
```

Do not call a WP/on-prem/mobile finding reportable until the domain check and
the normal evidence judge both support it.
