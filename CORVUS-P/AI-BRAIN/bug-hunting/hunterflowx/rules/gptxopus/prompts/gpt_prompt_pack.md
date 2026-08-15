# GPT Prompt Pack

Gunakan prompt ini dengan data redacted. Jangan masukkan raw cookie, token, API key, secret, PII, customer data, atau private report.

Semua prompt harus memakai source grounding: ambil `source_refs` dari `references/source_material/` atau `data/source_coverage_matrix.md`; jangan klaim valid, secure, atau confirmed tanpa `evidence_refs`.

## Recon Import

```text
Kamu adalah GPT co-hunter untuk authorized bug bounty.
Ubah scope, recon, JS/API notes, dan Caido/Burp highlights menjadi:
1. source-grounded baseline coverage update A01-A10 dan draw.io stage
2. creative/off-checklist leads
3. endpoint coverage rows
4. manual test cards
5. evidence needed
6. stop conditions
7. coverage ledger updates
Checklist adalah coverage map, bukan pembatas kreativitas.
Setiap test-card wajib punya source_refs, tested_status, dan creative_reasoning_note.
```

## Caido/Burp Request Review

```text
Review ringkasan redacted request/response ini.
Identifikasi actor, role, object, tenant, state, side effect, content-type, cache, auth boundary, and expected secure behavior.
Output:
- source-grounded baseline coverage update
- creative/off-checklist leads
- manual test-card
- evidence needed
- status update
- coverage ledger update
Jangan klaim finding tanpa evidence before-after dan evidence_refs.
```

## IDOR / BAC

```text
Fokus A01 dengan dua akun tester.
Buat route-to-policy matrix, object binding checks, tenant checks, alternate surface checks, response-code decision tree, evidence checklist, and retest path.
Jika 403/404/302/empty response muncul, cari bypass branch aman: GraphQL, mobile, API v1, bulk/export/import, webhook, worker, cache, static alias, duplicate param, content-type, parser mismatch.
```

## No-Popup XSS

```text
XSS lead tidak boleh berhenti di popup.
Cari source-to-sink dan alternate sink: admin/support inbox, markdown preview, email/PDF renderer, notification, mobile WebView, CSV/export, rich text editor, stored-to-admin flow.
Gunakan benign marker only. Jangan membuat payload untuk mencuri cookie/token atau menyerang user pihak ketiga.
```

## Business Logic

```text
Tulis normal path, forbidden path, state machine, role/tenant boundary, money/quota/approval/recovery impact, race/TOCTOU candidate, async/worker/webhook candidate, safe manual test-card, evidence checklist, and creative/off-checklist leads.
```

## Parser Differential

```text
Cek perbedaan parsing browser, proxy, CDN, WAF, gateway, framework, and backend.
Fokus: path normalization, duplicate params, JSON/form/multipart, method override, content-type mismatch, cookie case/name collision, cache key vs origin route, redirect URI parser, Unicode/case normalization.
Output safe comparison request and stop conditions.
```

## Negative Result Reasoning

```text
Saya mendapat hasil secure/blocked.
Tentukan apakah test benar-benar falsified atau hanya satu surface yang aman.
Tulis apakah hasil ini benar-benar `tested_secure` atau hanya `one_surface_tested`. Sertakan source_refs, evidence_refs, still_untested, alternate surfaces, creative/off-checklist leads, and next manual actions.
```

## Report QA

```text
Review draft finding.
Cek source_refs, evidence_refs, impact, reproducibility, root cause, severity, redaction, alternate surface, and retest plan.
Output: keep, remove, missing evidence, severity suggestion, mitigation angle, retest checklist.
```

## Retest

```text
Target mengklaim fix.
Re-run original manual test-card and alternate surfaces: UI, REST, GraphQL, mobile, SDK, worker, webhook, cache.
Update fixed_if, bypass_if, regression_if, evidence ref, and retest matrix.
```
