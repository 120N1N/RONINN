# Source File Queue

Use this when source code, JavaScript, PHP, Python, configs, templates, route
files, or archives are available.

| Priority | File ID | Path | Language/Type | Status | Review Artifact | Linked Endpoint/Flow | Next Action |
|---:|---|---|---|---|---|---|---|
| 1 | - | - | - | queued | - | - | read fully |

Allowed statuses:

```text
queued
reading
read
flow_linked
attack_surface_mapped
blocked
not_runtime_relevant
```

Verifier:

```bash
../../../bin/bbf source-verify --source-root <extracted-source-root> --queue-missing
```
