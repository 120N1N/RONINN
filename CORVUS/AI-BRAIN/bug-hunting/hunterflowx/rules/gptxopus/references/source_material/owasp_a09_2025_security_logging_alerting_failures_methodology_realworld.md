# OWASP A09:2025 Security Logging and Alerting Failures — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **Evidence-aware logging bugs** fokus pada event yang bisa dilihat tester atau dibuktikan dari user-visible audit/notification.
- **Critical event matrix** login, MFA, reset, role, API key, export, payment, webhook, admin.
- **Log integrity** injection, XSS in log viewer, delete/edit audit, missing actor/target/tenant.
- **Alert blind spots** small safe suspicious sequences, no load testing.
- **Report framing** jelaskan detection/forensics/response impact, bukan spekulasi SOC internal.

---

## Core Rule A09

A09 valid bila aplikasi tidak mencatat, tidak melindungi, tidak memonitor, atau tidak mengalert event keamanan penting seperti auth failure, access denial, privilege change, API key use, export, admin action, suspicious automation, webhook failure, or audit tampering.

---

## Attack Surface Mapping

```text
Mapping A09:
→ event: login, reset, MFA, role, API key, export, delete, payment, webhook, admin action, access denial
→ context: actor, target, tenant, role, IP/device, session, request ID, outcome, before/after
→ channel: audit log UI, account security activity, email alert, admin log, SIEM, webhook, API event log
→ failure: missing event, unclear event, sensitive data in log, injection, tamper/delete, no alert threshold
→ proof: visible audit/history, expected notification, product docs, test tenant, sanitized logs
→ impact: undetected takeover, untraceable admin action, secret leak, audit evasion, compliance risk
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Security activity page exists | can compare logged vs unlogged variants |
| Admin actions no audit | forensics gap for high privilege changes |
| Logs render user input | log injection or XSS path |
| Export/API key/payment action | critical events should be durable |
| Async/system actor only | real actor may be lost |
| Sensitive logs accessible | logging becomes data leak |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Missing event coverage | 1-15 | auth, access, admin, export, API key, payment |
| Alerting and detection | 16-22 | automation, suspicious sequences, thresholds |
| Log quality and integrity | 23-32 | context, tamper, injection, sensitive data |
| Async/cloud/integration logging | 33-38 | webhook, worker, CI/CD, tenant |
| Reporting | 39-42 | evidence, severity, retest |

---

## Universal Testing Logic

```text
Find A09:
select high-value security event with expected audit value →
perform event using tester account and timestamp precisely →
check user/admin-visible log, notification, or documented audit surface →
compare logged and unlogged variants across UI/API/mobile/GraphQL →
test log injection/tamper safely with harmless marker →
explain incident response or forensic impact →
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

> A09 sulit dibuktikan karena tester jarang melihat SIEM internal. Fokus pada event yang user/admin bisa lihat, notifikasi yang seharusnya muncul, audit UI, atau bukti bahwa alternate path melewati audit. Jangan melakukan high-volume alert testing.

## A09 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| UI action logged | API v1/mobile/GraphQL/bulk/import/export equivalent | cek audit middleware tidak mencakup semua path |
| Success logged | failed attempt, denied access, partial failure, webhook signature failure, rate-limit event | cek negative security event |
| Actor logged | async worker, webhook, support impersonation, scheduled job, delegated admin | cek real actor attribution |
| Target logged | tenant/object/role before-after, API key ID, export filename, payment ID | cek forensic completeness |
| Alert muncul untuk login | new device, reset, MFA change, API key creation, role change, mass export | cek high-risk event coverage |
| Log viewer escapes input | newline/control marker, filename/user-agent/comment, JSON field, webhook field | cek log forging tanpa merusak log |
| Log entry immutable | user/admin delete/edit/export audit, retention, tenant admin visibility | cek tamper evidence |
| Sensitive logging ditolak | error page, client log, build log, webhook log, analytics payload, crash report | cari token/PII leak surface |
| Internal SIEM tidak terlihat | nyatakan limitasi; gunakan user-visible absence, documented expected behavior, timestamp proof | hindari spekulasi |
| A09 terasa low | chain dengan A01/A07/A08: action sensitif bisa dilakukan tanpa audit/alert | naikkan impact deteksi/forensik |

## A09 Chaining Playbook

```text
Sensitive action via alternate API →
no audit event →
attacker can perform A01/A06 action quietly →
forensics/detection impact.

API key created silently →
persistent machine credential →
no owner alert →
long-lived unauthorized access risk.

Log injection →
fake event/hide actor →
privileged action investigation misled →
audit integrity impact.

Sensitive token in log →
log access becomes credential access →
A04/A07 takeover chain.
```

**Rule chaining:** A09 report harus jelas: event apa, expected log/alert apa, bukti tidak ada/kurang, dan kenapa itu menghambat detection atau response.

---

# Methodology Patterns

## 1. Missing Failed Login Event

**Find Missing Failed Login Event:** perform small failed login set on own account.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** user/admin cannot review high-risk failures.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 2. Missing Successful Login Event

**Find Missing Successful Login Event:** new device/browser login not shown.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account owner lacks session visibility.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 3. Missing Password Reset Event

**Find Missing Password Reset Event:** reset request/complete not logged or notified.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account recovery abuse harder to detect.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 4. Missing MFA Event

**Find Missing MFA Event:** MFA enable/disable/failure/recovery not logged.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** factor changes not auditable.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 5. Missing Session Revocation Event

**Find Missing Session Revocation Event:** device/session revoke not recorded.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker cleanup less visible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 6. Missing Access Denial Event

**Find Missing Access Denial Event:** repeated 403 to sensitive route not logged.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** probing cannot be investigated.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 7. Missing Privilege Change Audit

**Find Missing Privilege Change Audit:** role/permission update lacks actor/target/before-after.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** admin abuse untraceable.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 8. Missing Membership Change Audit

**Find Missing Membership Change Audit:** invite/remove/org join not logged.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tenant access changes hidden.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 9. Missing API Key Lifecycle Log

**Find Missing API Key Lifecycle Log:** create/view/rotate/revoke API key not logged.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** machine credential abuse hidden.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 10. Missing Secret View Audit

**Find Missing Secret View Audit:** view/download token/secret not recorded.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** sensitive read impossible to investigate.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 11. Missing Bulk Export Audit

**Find Missing Bulk Export Audit:** CSV/PDF/backup/user export not logged.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** mass data access invisible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 12. Missing Billing/Payment Audit

**Find Missing Billing/Payment Audit:** refund/credit/invoice/coupon action lacks durable event.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** financial abuse hard to trace.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 13. Missing Admin Impersonation Log

**Find Missing Admin Impersonation Log:** support/admin impersonates user without clear audit.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** privileged access hidden.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 14. Missing Settings/Security Policy Log

**Find Missing Settings/Security Policy Log:** SSO/CORS/webhook/security setting change not logged.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** control changes untraceable.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 15. Missing Delete/Destructive Action Log

**Find Missing Delete/Destructive Action Log:** delete/archive/purge lacks actor/target/outcome.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** destructive abuse uninvestigable.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 16. No Alert for Suspicious Login Attempts

**Find No Alert for Suspicious Login Attempts:** small safe suspicious attempts trigger no notification/lock signal.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** credential attack may go unnoticed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 17. No Alert for New Device/Login Location

**Find No Alert for New Device/Login Location:** new browser/device login no user notification.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** takeover detection weak.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 18. No Alert for Privilege Escalation

**Find No Alert for Privilege Escalation:** admin/owner role grant no alert.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** critical privilege change quiet.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 19. No Alert for API Key Creation

**Find No Alert for API Key Creation:** new API key no notification.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** silent persistence path.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 20. No Alert for Mass Export

**Find No Alert for Mass Export:** large export no alert or approval signal.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** data exfiltration quiet.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 21. No Alert for Webhook Signature Failures

**Find No Alert for Webhook Signature Failures:** failed or repeated webhook verification not visible.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** integration attack blind spot.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 22. No Alert for Rate/Abuse Threshold

**Find No Alert for Rate/Abuse Threshold:** small burst of reset/invite/email not detected.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** automation abuse likely.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 23. Audit Event Missing Actor

**Find Audit Event Missing Actor:** log says system/unknown instead of real initiator.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** forensics cannot attribute action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 24. Audit Event Missing Target

**Find Audit Event Missing Target:** event lacks object/user/tenant affected.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** incident scope cannot be determined.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 25. Audit Event Missing Outcome

**Find Audit Event Missing Outcome:** failure/success not recorded.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** ambiguous investigation.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 26. Audit Event Missing Source Context

**Find Audit Event Missing Source Context:** IP/device/session/request ID absent for auth/admin event.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** correlation weak.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 27. Sensitive Token in Logs

**Find Sensitive Token in Logs:** logs expose password/token/OTP/API key/session.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** log access becomes credential compromise.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 28. PII Overlogging

**Find PII Overlogging:** logs include excessive PII/payment/health data.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** privacy and breach impact increases.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 29. Log Injection Newline

**Find Log Injection Newline:** user-controlled field injects newline/fake event marker.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** audit trail can be forged.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 30. Log Severity Injection

**Find Log Severity Injection:** attacker controls severity/status/message field.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** alert routing or investigation misled.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 31. XSS in Log Viewer

**Find XSS in Log Viewer:** log viewer renders attacker-controlled value as HTML/JS.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** privileged analyst/admin context compromised.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 32. Audit Log Deletion

**Find Audit Log Deletion:** user/admin can delete their own critical audit entries.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** evidence can be removed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 33. Audit Log Editing

**Find Audit Log Editing:** event fields mutable after action.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** evidence integrity lost.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 34. Ephemeral Container Logs

**Find Ephemeral Container Logs:** critical logs only local/pod and lost on restart.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** incident reconstruction impossible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 35. GraphQL Mutation Bypasses Audit

**Find GraphQL Mutation Bypasses Audit:** REST action logged but equivalent GraphQL mutation not.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** alternate API avoids audit.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 36. Mobile/API v1 Bypasses Audit

**Find Mobile/API v1 Bypasses Audit:** legacy endpoint performs action without logging.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attackers choose quiet path.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 37. Webhook/Worker Actor Lost

**Find Webhook/Worker Actor Lost:** async job logs only system actor.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** original user/request not traceable.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 38. Cross-Tenant Support Action Invisible

**Find Cross-Tenant Support Action Invisible:** support action on tenant data not visible to tenant/admin audit.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** customer cannot detect privileged access.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 39. CI/CD Security Event Missing

**Find CI/CD Security Event Missing:** deploy/secret view/runner change not auditable.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** supply-chain incident detection weak.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 40. Logging Failure Swallowed

**Find Logging Failure Swallowed:** log pipeline failure lets critical action continue silently.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** audit guarantee false.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

## 41. Reportability Filter

**Find Reportability Filter:** anchor finding to a critical event and visible evidence gap.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** A09 report avoids unsupported SOC speculation.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define security event taxonomy, centralize append-only audit, include actor/target/tenant/outcome/context, redact secrets, encode log output, protect logs, and alert on critical thresholds.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai security event visibility and audit integrity
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
→ missing low-value activity event

Medium:
→ missing failed login/access denial logging for normal user

High:
→ missing audit for admin/API key/export/billing/privilege changes
→ logs expose tokens

Critical:
→ attacker can tamper/delete audit trail for high-impact actions
→ log system leaks secrets enabling takeover
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A09 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ security event tested
→ expected log/alert according to product risk/docs
→ exact tester action and timestamp
→ observed audit/log/notification absence or weakness
→ impact on detection, incident response, forensics, compliance
→ limits of tester visibility clearly stated
```

**Jangan hanya laporkan:**

```text
→ claiming internal SIEM missing without evidence
→ large-volume alert testing
→ injecting disruptive log payloads
→ exposing raw secrets in report
```

---

## Retest Checklist

```text
Retest after fix:
→ login/failure/MFA/reset/session events logged
→ access denial and suspicious sequences logged with context
→ privileged actions log actor/target/tenant/before-after/outcome
→ logs redact secrets and sensitive PII
→ log data encoded to prevent injection/XSS
→ audit logs append-only or tamper-evident
→ alerts exist for critical thresholds/actions
→ async/API/GraphQL paths use same audit pipeline
```

---

# Real-World Bug Bounty Insight Appendix

## A. GraphQL Role Change Has No Audit

**Pattern:** REST role update logs correctly, GraphQL mutation does not.

```text
Find:
→ perform REST baseline
→ perform GraphQL equivalent
→ compare audit surface
```

**Lesson:** Audit middleware must cover all execution paths.

---

## B. API Key Created Silently

**Pattern:** new persistent credential does not notify owner/admin.

```text
Find:
→ create tester API key
→ check security activity/email/audit
→ use key once
→ check logs again
```

**Lesson:** Credential lifecycle events need durable logs and alerts.

---

## C. Log Injection Hides Actor

**Pattern:** username/newline creates fake audit event.

```text
Find:
→ set harmless marker in profile/header
→ trigger logged action
→ inspect own visible log
```

**Lesson:** Logs are user interfaces and security records; encode and structure them.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A09 harus dibuktikan sebagai blind spot yang memengaruhi deteksi, investigasi, atau accountability.

## Recent Bypass Branches

- **Alternate API bypasses audit:** GraphQL mutation, mobile API, bulk endpoint, support action, webhook worker, and CI/CD integration harus menghasilkan event setara UI.
- **Auth/MFA logging:** cek login success/fail, MFA enable/disable, recovery code use, device revoke, password reset, session revoke, and suspicious login alert.
- **Sensitive telemetry:** reset link, token, API key, OAuth code, signed URL, PII, and secrets sering bocor di URL logs, analytics, APM traces, frontend error tracking, and support ticket.
- **Log injection/XSS:** gunakan marker aman untuk membuktikan newline/severity spoofing atau log viewer sink. Jangan mencoba menyembunyikan aktivitas nyata.
- **Evidence hardening:** jika tim punya audit UI, screenshot absence. Jika tidak ada UI, gunakan timestamp/request ID dan jelaskan expected event dari security-sensitive action.
- **AI/agent audit gap:** prompt submission, retrieved context, tool call request, approval decision, connector scope, model response, blocked prompt-injection event, dan failed/partial tool action harus punya event yang bisa diinvestigasi. Valid jika action penting terjadi lewat agent/MCP/worker tanpa actor, tenant, tool, scope, request ID, atau alert yang jelas.

## Evidence Upgrade

Gunakan format:

```text
Security event | Triggered by | Expected log/alert | Actual | Timestamp/request ID
```

Severity naik jika missing log menutup A01/A07/A08 high-impact chain.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **Evidence-first reporting:** setiap finding security-sensitive harus punya timestamp, request ID, before-after state, expected event, actual log/alert, and redacted proof.
- **Triage clarity:** chain panjang harus dibuka dengan root cause, primitive, affected boundary, and final impact dalam satu screen.
- **AI report risk:** AI-assisted report wajib diedit manual; hapus klaim tidak terbukti, noise, discovery-doc confusion, and public-key false positive.
- **Research opsec logs:** saat memakai collaborator/platform flow, perhatikan apakah report sharing, duplicate handling, Slack integration, atau audit trail membocorkan chain.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Timeline evidence:** report harus mencatat report date, fix date, affected tester account, test request, business state before/after, dan redacted proof.
- **Secret exposure audit:** validasi apakah exposed secret dirotasi, dicabut, dicari reuse-nya, dan diinvestigasi aksesnya.
- **Responsible disclosure friction:** saat birokrasi lambat, evidence harus tetap non-destruktif, timestamped, dan mudah diverifikasi.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A09 Security Logging and Alerting Failures: https://owasp.org/Top10/2025/A09_2025-Security_Logging_and_Alerting_Failures/
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- OWASP ASVS: https://github.com/OWASP/ASVS
- NIST Computer Security Incident Handling Guide: https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
