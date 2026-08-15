# OWASP A10:2025 Mishandling of Exceptional Conditions — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **Fail-closed testing** cek apakah error menjadi allow/default/system actor.
- **Parameter abnormality** missing, null, empty, wrong type, duplicate, extra, invalid enum.
- **Transaction failure** partial commit, rollback failure, retry/idempotency, timeout.
- **State edge** deleted, expired, revoked, suspended, cancelled, archived.
- **Async/dependency realism** webhook, queue, payment, storage, email, search, cache.

---

## Core Rule A10

A10 valid bila kondisi error, missing/extra parameter, timeout, partial failure, dependency failure, invalid state, revoked permission, null/wrong type, or abnormal response membuat sistem fail open, bocor, crash, corrupt state, melewati kontrol, or commit transaksi yang seharusnya rollback.

---

## Attack Surface Mapping

```text
Mapping A10:
→ abnormal input: missing param, extra param, null, wrong type, duplicate, invalid enum, boundary value
→ abnormal state: expired, deleted, revoked, cancelled, partial, suspended, locked, retrying
→ dependency failure: timeout, webhook failure, payment callback, storage error, email failure, queue delay
→ transaction phase: validate, reserve, charge, commit, notify, log, rollback, cleanup
→ failure mode: fail open, partial commit, stale state, sensitive error, crash, cleanup failure
→ impact: auth bypass, data leak, duplicate processing, financial inconsistency, persistent corrupted state
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Try/catch with default allow | classic fail-open path |
| Optional/nullable security field | missing value can skip policy |
| Multi-step transaction | partial commit/rollback bugs |
| Webhook/payment callback | abnormal status often mishandled |
| Async job retry | duplicate or stale processing |
| Deleted/expired/revoked object | edge state can bypass normal checks |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Input abnormality | 1-13 | missing, null, type, duplicate, enum, boundary |
| Fail-open and error disclosure | 14-22 | permission errors, default branch, verbose error |
| Transaction and state | 23-32 | partial commit, rollback, idempotency, stale state |
| Dependency and async | 33-39 | timeout, webhook, worker, cleanup |
| Reporting | 40-43 | severity, evidence, retest |

---

## Universal Testing Logic

```text
Find A10:
identify critical flow with validation, authorization, dependency, or transaction phases →
introduce one safe abnormal condition at a time →
observe response, side effect, rollback, retry, logs, and final state →
compare expected fail-closed behavior with actual behavior →
prove impact with tester-owned data and no DoS/destructive action →
jika impact nyata terbukti dengan cara aman, valid.

Jika hasil awal terlihat aman:
jangan langsung simpulkan aman. Turunkan ke decision tree: status code, request shape, endpoint alternatif, legacy/mobile/API, GraphQL, cache, async job, object state, and side effect.
```

---

## Decision Tree

### Jika respons `401`

```text
401 berarti identity/session tidak diterima.
Cek:
→ endpoint alternatif yang tidak membutuhkan auth
→ signed URL/API key/remember-me token tetap valid
→ mobile/API v1/websocket tetap menerima token lama
→ file/export/static resource tetap terbuka setelah logout
→ refresh token berbeda perilaku dari access token
```

### Jika respons `403`

```text
403 berarti ada deny path, tetapi belum tentu semua layer aman.
Cek:
→ method lain: GET/POST/PUT/PATCH/DELETE/OPTIONS
→ content-type lain: JSON, form-urlencoded, multipart, XML
→ header override, host override, method override, or path rewrite
→ API gateway vs origin/backend final
→ bulk/export/import/async endpoint yang menjalankan fungsi sama
→ response gagal tetapi side effect tetap terjadi
```

### Jika respons `404`

```text
404 bisa berarti resource tidak ada, masking, atau route/env berbeda.
Cek:
→ akses dari akun/role/environment yang seharusnya bisa
→ API v1/v2/mobile/internal route
→ trailing slash, case, suffix, extension, locale prefix
→ ID di path/query/body/header/cookie/GraphQL variable
→ source map, OpenAPI, GraphQL schema, mobile bundle
```

### Jika respons `302/307/308`

```text
Redirect bisa menyembunyikan flow asli.
Cek:
→ API response asli dengan Accept: application/json
→ redirect membawa token/code/state/return_url
→ action diproses sebelum redirect
→ redirect cache or open redirect chain
→ callback/RelayState/continue parameter
```

### Jika respons `200/204` kosong

```text
Jangan hanya lihat body.
Cek:
→ side effect pada data, file, email, webhook, role, job, queue, or billing
→ response kosong tetapi audit log/job status berubah
→ cache/CDN/service worker menyimpan data private
→ status sukses pada endpoint yang seharusnya internal
→ response berbeda antar tenant/role
```

### Jika respons `500/timeouts`

```text
Error sering membuka bug second-order.
Cek:
→ verbose error, stack trace, path, secret name, version
→ partial commit atau rollback gagal
→ async retry memproses action belakangan
→ error beda antara valid dan invalid object
→ jangan memicu DoS; cukup bukti kecil yang aman
```

### Jika UI aman

```text
UI bukan sumber kebenaran final.
Cek:
→ request privileged dari akun berhak lalu replay dengan akun rendah
→ JS bundle/source map/API docs/schema
→ mobile/API v1/GraphQL operation
→ feature flag and entitlement response
→ raw JSON/preloaded state/hidden fields
```

---

# Bypass & Chaining Workflow

> A10 bypass berarti mencari kondisi abnormal yang membuat sistem fail-open atau commit state yang salah. Jangan melakukan DoS; gunakan satu request kecil, data tester, dan bukti before/after.

## A10 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| Normal request aman | missing param, null, empty, wrong type, duplicate key, invalid enum, boundary value | cek parser/validator/handler mismatch |
| 400 terlihat aman | JSON vs form vs multipart, nested field, array instead scalar, boolean string, Unicode normalization | cek alternate parser |
| 403 saat permission kurang | trigger policy service error, stale cache, async job, service account fallback, fail-open feature flag | cek insufficient privilege handling |
| 500 muncul | cek side effect, partial commit, error disclosure, job retry, cleanup artifact | jangan berhenti di status code |
| Payment/webhook timeout | sandbox/test flow, malformed callback, duplicate retry, idempotency key, delayed success | cek transaction failure handling |
| Delete/revoke/expire aman | old link/token, websocket, worker queue, cache, mobile API, GraphQL resolver | cek stale state |
| Upload/import failure | temp file, partial extraction, public URL, quota lock, background processor | cek cleanup failure |
| GraphQL partial error | mixed allowed/denied fields, nullable field, resolver exception, batch alias | cek partial data leak |
| Circuit breaker aktif | dependency down/default config, cached allow, stale identity, fallback mode | cek fail-open design |
| Impact belum jelas | chain exception → side effect → partial state → A01/A06/A07 impact | ubah error menjadi business/security proof |

## A10 Chaining Playbook

```text
Missing/null/duplicate parameter →
validator and handler disagree →
default tenant/role/object chosen →
A01/A06 impact.

500/error during transaction →
first step committed →
rollback/cleanup failed →
credit/quota/order/file state exploitable.

Timeout/retry →
same action processed twice or marked success incorrectly →
payment/refund/webhook business impact.

Revoked/deleted/expired state →
normal path denies →
async/cache/mobile path still allows →
auth/access lifecycle bypass.
```

**Rule chaining:** report A10 bukan "ada 500"; report A10 adalah "500/timeout/abnormal input membuat sistem fail-open, leak, partial commit, atau cleanup gagal".

---

# Methodology Patterns

## 1. Missing Parameter Fail Open

**Find Missing Parameter Fail Open:** remove object/tenant/role/amount/confirmation parameter.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server defaults to broader access or unsafe action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 2. Null Parameter Confusion

**Find Null Parameter Confusion:** send null for required security/business field.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** check bypasses or default branch selected.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 3. Empty String Confusion

**Find Empty String Confusion:** send empty string instead of ID/status/token.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** resolver maps empty to current/default/global.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 4. Wrong Type Confusion

**Find Wrong Type Confusion:** send array/object/boolean where scalar expected.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** validator and handler disagree.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 5. Duplicate Parameter Ambiguity

**Find Duplicate Parameter Ambiguity:** duplicate query/body/header key with safe and unsafe values.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** validator reads one, handler uses another.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 6. Extra Parameter Side Effect

**Find Extra Parameter Side Effect:** add unexpected protected field.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** handler uses field despite schema expectation.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 7. Invalid Enum Default

**Find Invalid Enum Default:** send unknown status/type/action.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** default branch grants allow/privileged behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 8. Boundary Number Abuse

**Find Boundary Number Abuse:** zero/negative/max/fractional amount/limit.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** state or business calculation becomes unsafe.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 9. Date/Time Edge

**Find Date/Time Edge:** expired/future/past timezone value.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** expiry, cooldown, or schedule check bypassed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 10. Boolean String Confusion

**Find Boolean String Confusion:** send `false` as string or `0`/`1`.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** truthiness changes security branch.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 11. JSON/Form Parser Mismatch

**Find JSON/Form Parser Mismatch:** same fields in JSON vs form-urlencoded behave differently.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** one content-type skips validation.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 12. Multipart Edge Case

**Find Multipart Edge Case:** metadata field/filename/content-type parsed differently.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** handler accepts unsafe field.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 13. Unicode Normalization Edge

**Find Unicode Normalization Edge:** visually same ID/email/path normalizes differently.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** identity/object comparison bypassed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 14. Permission Error Fail Open

**Find Permission Error Fail Open:** trigger downstream permission error.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** system falls back to public/system/default actor.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 15. Auth Service Timeout Fail Open

**Find Auth Service Timeout Fail Open:** identity/permission service timeout.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** request allowed or cached as authorized.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 16. Feature Flag Service Failure

**Find Feature Flag Service Failure:** flag lookup fails.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** restricted feature defaults on.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 17. Policy Engine Exception

**Find Policy Engine Exception:** authorization/policy evaluation errors.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** handler proceeds instead of deny.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 18. Sensitive Error Disclosure

**Find Sensitive Error Disclosure:** safe malformed input reveals stack/path/secret/query/version.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** information useful for exploit chain leaks.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 19. Error Response Includes Private Data

**Find Error Response Includes Private Data:** exception body contains object/user/payment data.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** unauthorized sensitive data exposed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 20. Different Error for Valid Object

**Find Different Error for Valid Object:** error distinguishes valid IDs/users/tenants.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** enumeration possible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 21. Crash on Single Malformed Request

**Find Crash on Single Malformed Request:** one small request crashes critical flow.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** targeted availability/security impact without volumetric DoS.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 22. Exception Swallowing

**Find Exception Swallowing:** action returns success while security step failed.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** user/admin believes revoke/delete/MFA completed but it did not.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 23. Partial Commit

**Find Partial Commit:** multi-step flow commits first step then fails later.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** inconsistent exploitable state remains.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 24. Rollback Failure

**Find Rollback Failure:** forced failure after reserve/debit/approval.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** resource/credit/quota not restored.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 25. Idempotency Missing

**Find Idempotency Missing:** retry request duplicates payment/refund/order/action.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** same operation processed twice.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 26. Idempotency Key Reuse Across Users

**Find Idempotency Key Reuse Across Users:** same key used by another user/tenant.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** request collision or data leak.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 27. Retry After Failure Commits Later

**Find Retry After Failure Commits Later:** failed response eventually processes async.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** user can trigger unexpected delayed action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 28. Approve/Cancel Race Error

**Find Approve/Cancel Race Error:** exception between conflicting transitions.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** object reaches impossible state.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 29. Deleted Object Still Actionable

**Find Deleted Object Still Actionable:** use ID/link after delete/archive.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** action/data remains available.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 30. Revoked Token Still Accepted on Error Path

**Find Revoked Token Still Accepted on Error Path:** normal path denies, error/legacy path accepts.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** revocation bypass.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 31. Expired Invite/Link Edge

**Find Expired Invite/Link Edge:** expired object triggers alternate branch.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** sensitive action still completes.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 32. Suspended Account Edge

**Find Suspended Account Edge:** suspended/deleted user can use token/API path.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account status not enforced everywhere.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 33. Payment Gateway Timeout

**Find Payment Gateway Timeout:** payment/capture/refund timeout handled as success.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** financial state wrong.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 34. Webhook Malformed Response

**Find Webhook Malformed Response:** callback returns 204/302/500/malformed JSON.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** app treats failure as success or retries dangerously.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 35. Storage Failure Cleanup Gap

**Find Storage Failure Cleanup Gap:** upload/import/render failure leaves temp/private file accessible.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** leftover artifact leaks data.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 36. Email/SMS Failure State Gap

**Find Email/SMS Failure State Gap:** verification/notification failure still marks completed.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** identity/security notification guarantee false.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 37. Queue Worker Exception

**Find Queue Worker Exception:** worker marks failed job complete or repeats action.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** state inconsistent or duplicated.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 38. Cache Error Stale Allow

**Find Cache Error Stale Allow:** policy/cache failure uses stale allow.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** revoked permission still works.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 39. GraphQL Partial Error Leakage

**Find GraphQL Partial Error Leakage:** resolver error returns partial data that should be denied.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** exception path leaks sensitive fields.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 40. Circuit Breaker Fail Open

**Find Circuit Breaker Fail Open:** dependency outage defaults to allow/skip validation.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** security control absent during failure.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 41. Resource Limit Without DoS

**Find Resource Limit Without DoS:** small oversized field/file triggers error and side effect.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** cleanup/state/security failure shown without load.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

## 42. Reportability Filter

**Find Reportability Filter:** show expected fail-closed behavior and actual side effect/state.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** finding proves exceptional condition impact, not just 500.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** fail closed, validate parsed values consistently, make transactions atomic, use idempotency, handle dependency failures explicitly, clean up artifacts, and regression-test edge states.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai abnormal state and failure handling
→ uji parent-child mismatch dengan akun tester
→ cek shared resource, shared key, shared cache, shared index, and cross-region boundary

API v1/mobile:
→ bandingkan web modern vs API v1/mobile/legacy
→ cek endpoint lama yang belum menerima hardening baru
→ cek old SDK, beta build, and deprecated route

GraphQL:
→ cek node/global ID, nested resolver, alias, fragments, batching
→ cek apakah resolver memakai validator berbeda dari REST
→ cek introspection/schema yang membocorkan operation lama

CDN/cache:
→ cek Vary, Cache-Control, ETag, 304, stale response
→ cek CDN/origin behavior and personalized response cache
→ cek service worker/browser back cache after logout or state change

CI/CD:
→ cek build artifact, source map, logs, preview env, secrets masking
→ cek untrusted PR/build metadata masuk ke privileged workflow
→ cek deploy artifact/provenance/signature

OAuth/webhook/integration:
→ cek OAuth callback, webhook signature, app marketplace, connector scope
→ cek event replay and callback retry
→ cek delegated identity/service account confusion

Worker async/background job:
→ cek job payload, retry endpoint, delayed execution, queue dashboard
→ cek worker revalidates actor/object/state before commit
→ cek stale permission after role/session/revocation changes

Parser/proxy mismatch:
→ cek JSON vs form vs multipart vs XML parser behavior
→ cek duplicate parameter and nested object binding
→ cek proxy/backend path normalization, method override, and content-type confusion
```

---

## Severity Heuristic

Gunakan CIA + privilege + blast radius + exploitability + confidence.

```text
Info/Low:
→ generic crash/error without sensitive data or persistent impact

Medium:
→ limited sensitive error
→ stale state on own resource
→ minor cleanup failure

High:
→ fail-open authorization
→ partial financial/state commit
→ sensitive stack/config disclosure
→ duplicate processing

Critical:
→ account/payment/tenant compromise
→ persistent data corruption
→ bypass of revocation/security action
→ RCE-enabling error chain
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A10 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ critical flow and expected fail-closed behavior
→ abnormal condition used
→ response and side effect
→ before/after object state
→ whether rollback, retry, cleanup, or logging failed
→ tester-owned data and no DoS/destructive impact
```

**Jangan hanya laporkan:**

```text
→ volumetric DoS/load testing
→ corrupting real payment/order/user data
→ claiming every 500 as vulnerability
→ using destructive cleanup bypass
```

---

## Retest Checklist

```text
Retest after fix:
→ missing/extra/null/wrong type inputs fail closed
→ validation and handler use same parsed values
→ transactions atomic and rollback on failure
→ idempotency enforced for retryable actions
→ downstream failures do not become success
→ revoked/deleted/expired states rechecked before action
→ temp files/artifacts cleaned after exceptions
→ errors generic to users and detailed only in protected logs
→ async jobs do not mark incomplete action complete
```

---

# Real-World Bug Bounty Insight Appendix

## A. Refund Timeout Treated as Success

**Pattern:** payment provider timeout makes app mark refund complete.

```text
Find:
→ use sandbox/test order
→ simulate safe timeout if scope allows
→ observe refund state
```

**Lesson:** Exceptional payment states require reconciliation, not optimistic success.

---

## B. Missing tenant_id Defaults Global

**Pattern:** removing tenant parameter makes report use global/default tenant.

```text
Find:
→ create tester tenant data
→ remove tenant param
→ compare report output
```

**Lesson:** Missing security context must fail closed, never default broad.

---

## C. GraphQL Partial Data on Resolver Error

**Pattern:** one field errors but sibling sensitive data returns.

```text
Find:
→ request mixed allowed/denied fields
→ trigger safe resolver error
→ observe partial response
```

**Lesson:** Exceptional resolver paths need same authorization and redaction rules.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A10 harus melihat error sebagai state transition, bukan hanya stack trace.

## Recent Bypass Branches

- **Fail-open dependency:** authz service timeout, policy service error, cache miss, payment gateway timeout, webhook parse failure, storage error, and SSO callback failure harus gagal tertutup.
- **Duplicate/missing parameter parser drift:** first-value vs last-value parser, JSON duplicate key, form vs JSON fallback, null vs absent, empty array vs missing array, and encoded delimiter dapat mengubah policy branch.
- **Cache/origin discrepancy:** private response, error response, redirect, or 404/403 masking dapat tercache salah jika CDN dan origin berbeda membaca path/key.
- **Partial transaction:** upload succeeds but DB fails, payment capture succeeds but order rollback, refund timeout, email/SMS failure, worker retry, and idempotency conflict.
- **Race + exception chain:** satu request memicu sub-state/error, request lain mengambil state sebelum rollback. Gunakan request rendah dan akun tester.

## Evidence Upgrade

Report harus menunjukkan before/after state, request ID, expected fail-closed behavior, actual fail-open behavior, dan bagaimana kondisi error bisa direproduksi aman tanpa DoS atau merusak data.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **Fallback parser:** malformed protobuf/JSON/XML/form input harus fail closed; jangan sampai backend pindah parser dan melewati policy.
- **Cache/ETag exception:** conditional request, stale cache, ETag oracle, and cache validator dapat mengubah privacy/auth state tanpa response body jelas.
- **Agent/worker exception:** AI/MCP/tool/worker failure tidak boleh mengekspos raw prompt, token, connector output, internal stack, atau partial state.
- **WAF/app differential:** WAF bypass bukan impact final; tunjukkan bagaimana discrepancy melewati app validation dengan marker aman dan request pembanding.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **WAF/app differential:** WAF block, page-notfound, redirect, atau canonical URL path dapat membuat parser mismatch; gunakan marker aman dan request pembanding.
- **SSRF boundary proof:** buktikan server-side fetch lewat controlled callback; jangan eskalasi ke command execution kecuali program mengizinkan eksplisit.
- **Mobile component exception:** malformed intent, deep link, content URI, atau broadcast harus fail closed tanpa expose internal state.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A10 Mishandling of Exceptional Conditions: https://owasp.org/Top10/2025/A10_2025-Mishandling_of_Exceptional_Conditions/
- OWASP Error Handling Cheat Sheet: https://cheatsheetseries.owasp.org/
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- PortSwigger Race conditions: https://portswigger.net/web-security/race-conditions
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
