# Operating Model

## Core Rule

GPT boleh kreatif dalam reasoning, tetapi tidak boleh memperluas izin. Semua ide harus menjadi source-grounded test-card manual, coverage update, evidence request, atau report QA.

## Output Wajib Per Sesi

| Output | Tujuan |
|---|---|
| `source-grounded baseline coverage` | Menandai A01-A10 dan draw.io stage mana yang sudah dites, blocked, atau belum |
| `creative/off-checklist leads` | Menjaga kreativitas di luar checklist |
| `manual test cards` | Mengubah ide menjadi langkah aman |
| `evidence needed` | Menentukan bukti triage-friendly |
| `stop conditions` | Mencegah tindakan out-of-scope atau destruktif |
| `coverage ledger updates` | Menulis source refs, evidence refs, dan status terbaru |

## Guardrails

- Cek `engagement/rules_and_scope/` sebelum test.
- Cek `workflow/source_grounding_protocol.md`, `references/source_material/manifest.json`, dan `data/source_coverage_matrix.md` sebelum membuat test-card.
- Gunakan akun/data tester.
- Redact sensitive data sebelum dimasukkan ke GPT.
- Validasi manual di browser + Caido/Burp.
- Catat semua finding candidate dan evidence.
- Jangan naikkan status ke `tested_secure`, `finding_candidate`, atau `confirmed` tanpa evidence refs.

## Status

| Status | Arti |
|---|---|
| `untested` | Belum diuji |
| `queued` | Masuk antrian |
| `in_progress` | Sedang divalidasi manual |
| `tested_secure` | Skenario aman |
| `needs_manual` | Butuh klik/role/state manual |
| `blocked_by_scope` | Tidak boleh diuji |
| `blocked_by_auth` | Butuh akun/role |
| `blocked_by_captcha` | Stop automation |
| `creative_lead` | Ide di luar baseline |
| `variant_candidate` | Varian dari pattern |
| `chain_candidate` | Primitive bisa dirangkai |
| `finding_candidate` | Ada bukti awal |
| `confirmed` | Siap report |
| `retest_required` | Perlu uji ulang |

## Source-Grounded Status Rule

Source material dapat membuat status `queued`, `needs_manual`, `blocked_by_scope`, `blocked_by_auth`, `blocked_by_captcha`, `creative_lead`, `variant_candidate`, atau `chain_candidate`.

Source material tidak cukup untuk `tested_secure`, `finding_candidate`, atau `confirmed`. Status tersebut membutuhkan evidence manual yang redacted dan tester-owned.
