# Manual Browser + Caido/Burp Loop

Workflow ini mengutamakan browser langsung agar fitur, state, dan UI behavior tidak terlewat.

Setiap replay harus punya `source_refs` dari source material dan `evidence_refs` dari hasil manual jika status ingin naik.

## Loop

| Step | Action |
|---:|---|
| 1 | Buka target di browser dengan akun tester |
| 2 | Jalankan normal workflow |
| 3 | Capture request di Caido/Burp HTTP history |
| 4 | Pilih request dengan object, tenant, role, state, auth, upload, export, webhook, async, atau cache |
| 5 | Redact cookie, token, secret, PII, dan data pihak ketiga |
| 6 | Minta GPT review request summary dengan source refs |
| 7 | GPT membuat source-grounded baseline coverage update dan creative/off-checklist leads |
| 8 | Hunter replay satu perubahan aman |
| 9 | Simpan evidence |
| 10 | Update findings/checklists/report |

## Request Review Checklist

| Field | Notes |
|---|---|
| Method + route |  |
| Actor role |  |
| Tenant |  |
| Object |  |
| State |  |
| Side effect |  |
| Content type |  |
| Cache headers |  |
| Redirect/origin |  |
| Expected secure behavior |  |
| Source refs |  |
| Evidence refs |  |
| Tested status |  |
| Stop condition |  |

## Evidence

Simpan evidence di `engagement/evidence/evidence_index.md`. Gunakan screenshot/video hanya jika UI state penting. Tanpa evidence refs, status tetap `queued`, `needs_manual`, atau `blocked_*`.
