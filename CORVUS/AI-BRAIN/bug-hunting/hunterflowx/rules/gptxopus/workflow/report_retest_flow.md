# Report And Retest Flow

## Finding Candidate

Finding candidate harus punya:

| Field | Required |
|---|---|
| Source refs | Ya |
| Root cause | Ya |
| Affected asset | Ya |
| Affected role/tenant/object | Jika relevan |
| Reproduction steps | Ya |
| Expected vs actual | Ya |
| Evidence refs | Ya |
| Impact | Ya |
| Scope proof | Ya |
| Redaction notes | Ya |

## Report QA

GPT harus menghapus klaim yang tidak punya evidence. Severity harus mengikuti impact yang terbukti, bukan payload atau confidence.

Source refs wajib menjelaskan inspirasi test, tetapi source refs bukan evidence. `tested_secure`, `finding_candidate`, dan `confirmed` membutuhkan evidence refs.

## Retest

Saat fix diklaim:

| Retest area | Action |
|---|---|
| Original path | Re-run old manual test-card |
| Alternate surface | UI, REST, GraphQL, mobile, SDK, worker, webhook, cache |
| Creative variants | Re-run lead yang dulu belum tuntas |
| Logging | Cek blocked action terlihat |
| Evidence | Update evidence index |
| Source coverage | Update source refs dan status ledger |

## Report Files

- Draft report: `engagement/reports/report_template.md`
- Triage replies: `engagement/reports/triage_reply_template.md`
- Retest report: `engagement/reports/retest_report_template.md`
