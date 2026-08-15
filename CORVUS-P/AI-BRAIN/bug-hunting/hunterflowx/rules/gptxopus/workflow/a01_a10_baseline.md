# A01-A10 Baseline

Urutan ini menjaga struktur, bukan membatasi kreativitas.

Ambil source refs dari `data/source_coverage_matrix.md` dan source lengkap di `references/source_material/`. Source refs wajib untuk test-card, tetapi verdict butuh evidence refs.

| Order | Category | Baseline question | Evidence |
|---:|---|---|---|
| 1 | A01 Broken Access Control | Apakah actor, role, object, tenant, state, dan route policy konsisten? | Two tester accounts, request A/B, state diff |
| 2 | A02 Security Misconfiguration | Apakah service/config/env exposed lebih luas dari intended audience? | Screenshot, headers, config snippet redacted |
| 3 | A03 Supply Chain | Apakah dependency, CI/CD, artifact, registry, atau CDN trust lemah? | Manifest/ref, workflow ref, passive proof |
| 4 | A04 Crypto | Apakah token/secret/signature terikat ke actor, object, tenant, purpose, expiry? | Token behavior summary, no raw secret |
| 5 | A05 Injection | Apakah source mencapai sink tanpa validation/encoding/binding? | Marker-only proof, rendered context |
| 6 | A06 Insecure Design | Apakah invariant bisnis bisa dilanggar? | Normal vs forbidden workflow |
| 7 | A07 Authentication | Apakah auth/session/MFA/OAuth lifecycle konsisten? | Login/reset/session state |
| 8 | A08 Integrity | Apakah client state/webhook/update/import bisa ditamper/replay? | Before-after state, replay notes |
| 9 | A09 Logging & Alerting | Apakah event penting tercatat dan aman? | Audit screenshot/log absence proof |
| 10 | A10 Exceptional Conditions | Apakah error/timeout/malformed input fail-open? | Status code plus side-effect state |

## Baseline Output

```text
source-grounded baseline coverage:
- A01:
- A02:
- A03:
- A04:
- A05:
- A06:
- A07:
- A08:
- A09:
- A10:
- source_refs_used:

creative/off-checklist leads:
- source_signal:
- source_refs:
- hypothesis:
- manual_test_card:
- creative_reasoning_note:
- tested_status:
```
