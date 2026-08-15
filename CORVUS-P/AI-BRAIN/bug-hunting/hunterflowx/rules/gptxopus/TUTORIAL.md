# Tutorial Penggunaan GPT Bug Bounty Hunting Kit

Panduan ini dipakai untuk hunting manual dengan GPT, browser, Caido/Burp, dan metodologi OWASP A01-A10. Semua aktivitas harus authorized, in-scope, non-destruktif, dan memakai akun/data tester.

Kit ini memakai source mirror penuh di `references/source_material/`. Source tersebut adalah checklist dan metodologi, bukan bukti vulnerability. Gunakan source untuk coverage dan ide, lalu gunakan evidence manual untuk verdict.

## 1. Setup Engagement

Isi folder engagement sebelum testing:

| File | Isi |
|---|---|
| `engagement/rules_and_scope/program_scope.md` | Program name, scope, asset tier, bounty rules |
| `engagement/rules_and_scope/testing_rules.md` | Forbidden actions, rate limit, test account, safe data |
| `engagement/documentation/target_notes.md` | Product notes, roles, tenants, workflows |
| `engagement/documentation/recon_summary.md` | Recon result, JS/API notes, endpoints, tech stack |
| `engagement/evidence/evidence_index.md` | Index request/response, screenshots, timestamps |
| `engagement/findings/findings_tracker.md` | Candidate, confirmed, invalid, duplicate |
| `engagement/reports/report_template.md` | Draft report format |

Sebelum import recon, cek juga:

| File | Isi |
|---|---|
| `references/source_material/manifest.json` | Hash, ukuran, kategori, dan owner source material |
| `data/source_coverage_matrix.md` | Gate coverage untuk 27 diagram draw.io dan OWASP A01-A10 |
| `data/source_pattern_registry.md` | Registry semua diagram/heading/pattern source untuk mengurangi risiko terlewat |
| `workflow/source_grounding_protocol.md` | Aturan source refs, evidence refs, status promotion, dan creative lane |

## 2. Import Recon Ke GPT

Berikan GPT ringkasan redacted:

```text
Scope:
Recon:
Roles/accounts:
Routes/API:
JS observations:
Caido/Burp highlights:
Known constraints:
```

Minta output:

```text
source-grounded baseline coverage:
creative/off-checklist leads:
endpoint coverage rows:
manual test cards:
evidence needed:
coverage ledger updates:
```

## 3. Jalankan Baseline A01-A10

Mulai dari A01 karena access control sering menjadi root cause paling reportable. Lanjutkan A02 sampai A10 untuk coverage. Untuk tiap kategori, ambil source refs dari `data/source_coverage_matrix.md` dan source material terkait.

Jangan tunggu baseline selesai jika ada high-signal anomaly. Jika saat A01 terlihat XSS sink, business logic flaw, OAuth issue, parser mismatch, atau cache leak, buat creative test-card langsung dan tetap update coverage.

Setiap test-card harus menyebut `source_refs`, `tested_status`, dan `creative_reasoning_note`. Tanpa evidence manual, status maksimal adalah `queued`, `needs_manual`, atau `blocked_*`.

## 4. Browser + Caido/Burp Loop

1. Buka target di browser dengan akun tester.
2. Jalankan workflow normal seperti user asli.
3. Capture traffic di Caido/Burp HTTP history.
4. Pilih request penting: auth, role, object, tenant, state-changing, export/import, upload, webhook, async, cache.
5. Redact cookie, token, PII, secret, dan data pihak ketiga.
6. Minta GPT membuat test-card manual.
7. Validasi satu perubahan per replay.
8. Simpan evidence ref dan update checklist, source coverage matrix, dan findings tracker jika relevan.

## 5. Evidence

Setiap evidence harus punya:

| Field | Wajib |
|---|---|
| Evidence ID | Ya |
| Timestamp | Ya |
| Account/role | Ya |
| Tenant/object | Jika relevan |
| Request ref | Ya |
| Response ref | Ya |
| Screenshot/video | Jika UI/state penting |
| Redaction notes | Ya |
| Expected vs actual | Ya |
| Source refs | Ya |
| Tested status | Ya |

## 6. Finding Dan Report

Jika ada kandidat bug:

1. Catat di `engagement/findings/findings_tracker.md`.
2. Buat detail di `templates/finding_candidate.md`.
3. Kumpulkan evidence di `engagement/evidence/evidence_index.md`.
4. Draft report memakai `engagement/reports/report_template.md`.
5. Jalankan report QA memakai prompt di `prompts/gpt_prompt_pack.md`.

Jangan menaikkan status ke `finding_candidate` atau `confirmed` kalau hanya ada source refs tanpa evidence refs.

## 7. Retest

Saat program mengklaim fix:

1. Jalankan original manual test-card.
2. Cek alternate surface: UI, REST, GraphQL, mobile, SDK, worker, webhook, cache.
3. Cek creative variants yang dulu muncul.
4. Update `engagement/reports/retest_report_template.md`.
5. Update `checklists/retest_matrix.md`.

## 8. Install Skill Opsional

Kit ini sudah menyediakan repo-local skill di `.agents/skills/gpt-bug-bounty-hunter/` untuk workspace ini. Jika ingin skill yang sama auto-discovered dari semua workspace, salin folder:

```text
gpt_bug_bounty_hunting_kit/skill/gpt-bug-bounty-hunter
```

ke:

```text
~/.codex/skills/gpt-bug-bounty-hunter
```

Validasi skill:

```text
python3 /Users/raihan/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/gpt-bug-bounty-hunter
```
