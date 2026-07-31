# WordPress Plugin Playbook

Use the Hunterflowx WordPress domain gates for full WP plugin audits.

In this final workflow, start by making the WP-specific gates visible:

```bash
../../../bin/bbf wp-plan
../../../bin/bbf domain-verify --domain wp
```

## Pre-Audit

- route platform: Patchstack, Wordfence, both, or OOS
- check install count and updated date
- check known CVEs
- spawn local WP lab

## Entry Points

- `add_action`
- `add_filter`
- `add_shortcode`
- `admin_init`
- `rest_api_init`
- `wp_ajax_*`
- `wp_ajax_nopriv_*`

## Core Checks

- capability check
- nonce check
- REST `permission_callback`
- `$wpdb->prepare`
- context-correct escaping
- sanitizer body and bypass attempts
- file upload handling
- option/usermeta update
- unserialize and POP chain
- local WP lab PoC
- evidence-score and judge before report

## Domain Completion

For every completed WP check, write a linked completion event:

```bash
../../../bin/bbf event domain_check_completed \
  --domain wp \
  --check-id wp-capability-nonce \
  --status domain_complete \
  --evidence-path evidence/burp/wp-capability-nonce.txt
```

The dashboard must show WP domain depth moving from missing to partial or
complete. A plugin finding is not reportable just because source has a missing
nonce; it still needs runtime evidence and judge approval.

## Verdict Rule

No invalid verdict just because a sanitizer exists. Test bypass attempts first.
