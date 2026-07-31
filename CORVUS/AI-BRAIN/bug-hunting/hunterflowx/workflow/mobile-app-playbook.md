# Mobile App Playbook

Use the mobile profile when the target has Android, iOS, React Native, Flutter,
or mobile-only API behavior.

## Start

```bash
../../../bin/bbf mobile-plan
../../../bin/bbf domain-verify --domain mobile
```

## Mandatory Gates

- scope and app inventory: package, version, hash, store URL, test accounts
- device or emulator runtime capture through Burp/Caido when allowed
- static decompile and manifest inventory
- mobile-only API endpoint diff against web/runtime inventory
- token/session storage and logout behavior
- deep links, exported components, and intent/app-link handling
- WebView origin and JS bridge mapping
- local data, logs, screenshots, backups, clipboard, keychain/keystore
- Frida/runtime proof only when authorized
- evidence-score and judge before report

## Runtime Evidence

Prefer evidence that ties the mobile app to actual server impact:

```text
device action
-> proxy request/response
-> endpoint / source / static artifact
-> server read-back or browser-visible state
-> evidence-score
-> judge
```

## Safety

Do not bypass pinning, root/jailbreak checks, CAPTCHA, account controls, or
platform restrictions unless the program explicitly allows it. If not allowed,
record the domain check as `blocked` with the exact reason.

## Events

Use:

```text
domain_profile_loaded
domain_check_planned
domain_check_completed
source_file_read
source_flow_linked
endpoint_discovered
endpoint_seen_runtime
endpoint_angle_planned
endpoint_angle_tested
evidence_added
evidence_reviewed
evidence_judged
domain_depth_reviewed
```
