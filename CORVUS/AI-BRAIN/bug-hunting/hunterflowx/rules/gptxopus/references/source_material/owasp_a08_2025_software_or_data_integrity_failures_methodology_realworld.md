# OWASP A08:2025 Software or Data Integrity Failures — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **Integrity object mapping** serialized blob, cookie, import file, webhook, artifact, update, plugin, client state.
- **Tamper/replay workflow** ubah field aman, replay old event, remove signature, compare side effects.
- **Mass assignment depth** extra/nested/protected attributes and parser/model binder mismatch.
- **Webhook/update real-world** signature coverage, timestamp, nonce, event type, downgrade, provenance.
- **Async trust boundary** API validates but worker/importer trusts payload.

---

## Core Rule A08

A08 valid bila aplikasi mempercayai software, artifact, serialized object, client state, webhook event, update manifest, plugin, import, or dynamic attribute tanpa verifikasi integritas, provenance, signature, schema, allowlist, or trusted source yang benar.

---

## Attack Surface Mapping

```text
Mapping A08:
→ object: serialized blob, cookie, JWT-like state, webhook event, update manifest, plugin, artifact, import file
→ source: browser, mobile, third-party service, CDN, package, tenant upload, CI/CD, admin import
→ verifier: HMAC, signature, checksum, schema, allowlist, provenance, SRI, audit trail
→ sink: deserializer, object mapper, update installer, webhook handler, config loader, plugin engine, worker
→ failure: unsigned, weak signature, replay, mutable attributes, untrusted CDN, insecure deserialization
→ impact: privilege change, price/plan tamper, fake event, plugin execution, malicious update, data corruption
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Encoded client blob | may be trusted state without integrity |
| Extra JSON fields accepted | mass assignment risk |
| Webhook event changes state | signature/replay bugs have business impact |
| Import/restore feature | trusted data can overwrite protected fields |
| Update/plugin mechanism | software integrity path |
| Worker queue payload | API validation may not apply later |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Client/server state integrity | 1-12 | cookies, blobs, mass assignment, hidden fields |
| Deserialization/import | 13-21 | serialized object, import, archive, restore |
| Webhook/event integrity | 22-28 | signature, replay, context coverage |
| Software/update/plugin integrity | 29-36 | SRI, artifact, update, plugin, CI/CD |
| Reporting | 37-40 | severity, evidence, retest |

---

## Universal Testing Logic

```text
Find A08:
identify object/data/software artifact the system trusts →
check who can see, replay, modify, upload, or replace it →
test whether server verifies signature/schema/provenance before trust →
prove tamper or replay impact with tester-owned data →
avoid malicious code execution unless explicitly allowed →
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

> A08 bypass berarti mencari object/data/software yang dipercaya walau bisa diubah, di-replay, atau diganti. Jangan upload malicious plugin/artifact kecuali scope eksplisit; gunakan tamper field aman dan tester-owned object.

## A08 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| Extra field ditolak | nested object, array, JSON Patch, merge patch, form vs JSON, GraphQL input, multipart metadata | cek model binder/mapper lain |
| Client state signed | replay old signed state, missing vs invalid signature, timestamp, tenant/user/resource binding | cek lifecycle dan coverage |
| Webhook signature ada | raw body vs parsed body, event type, account binding, timestamp replay, retry endpoint | cek event integrity penuh |
| Deserialization blocked | alternate cookie/cache/queue/import endpoint, type discriminator, old format, worker payload | cari consumer lain |
| Import validates schema | protected fields nested, duplicate keys, backup restore, old importer, CSV header variations | cek schema/consumer mismatch |
| Plugin/update signed | manifest vs binary signature, downgrade, mutable CDN, beta channel, plugin source URL | cek apa yang benar-benar diverifikasi |
| SRI/CSP ada | script pada auth page, allowed CDN origin, dynamic import, legacy bundle, source map | cek script trust boundary |
| Queue job protected | retry job, delayed job after role removal, job IDOR, payload replay, admin queue UI | cek worker trust |
| Audit integrity ada | edit/delete own logs, log injection, async actor lost, export logs | cek tamper evidence |
| Impact belum jelas | chain tamper → role/price/tenant/webhook/update/deploy effect | buktikan trust decision rusak |

## A08 Chaining Playbook

```text
Mass assignment →
protected field persists →
role/tenant/price/verified state changes →
A01/A06 business impact.

Webhook integrity gap →
fake/replayed event accepted →
payment/order/subscription state changes →
business impact.

Unsigned update/plugin/artifact →
trusted code path can be replaced/downgraded →
execution or supply-chain impact.

Client state tamper →
server trusts modified entitlement/plan/quota →
feature or billing abuse.
```

**Rule chaining:** bukti terbaik A08 adalah before/after state yang menunjukkan trusted data berubah karena tamper/replay.

---

# Methodology Patterns

## 1. Unsigned Client State

**Find Unsigned Client State:** cart/plan/role/quota stored in client without MAC.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tamper changes server decision.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 2. Base64 State Trusted

**Find Base64 State Trusted:** encoded cookie/hidden field decodes to security data.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server accepts modified decoded value.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 3. Encrypted State Without MAC

**Find Encrypted State Without MAC:** ciphertext can be replayed/tampered or oracle appears.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** integrity missing despite confidentiality.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 4. Cookie Role Tamper

**Find Cookie Role Tamper:** role/tenant/feature flag cookie affects backend.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** cookie change alters privilege/entitlement.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 5. Hidden Field Price Tamper

**Find Hidden Field Price Tamper:** form field controls price/discount/owner/status.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server persists modified value.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 6. Mass Assignment is_admin

**Find Mass Assignment is_admin:** extra protected boolean/role accepted in JSON.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** privileged attribute persists.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 7. Mass Assignment tenant_id

**Find Mass Assignment tenant_id:** extra tenant/owner/account ID accepted.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** object crosses tenant/ownership boundary.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 8. Nested Object Assignment

**Find Nested Object Assignment:** protected field hidden inside nested object/array.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** model binder persists nested protected field.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 9. GraphQL Input Overposting

**Find GraphQL Input Overposting:** mutation accepts fields not present in UI.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** protected field changes.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 10. Patch Merge Integrity Gap

**Find Patch Merge Integrity Gap:** JSON Patch/Merge Patch updates fields not allowed.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** restricted property changes.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 11. Duplicate Key Model Confusion

**Find Duplicate Key Model Confusion:** validator reads one key, mapper stores another.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tampered protected value accepted.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 12. Client Feature Flag Trusted

**Find Client Feature Flag Trusted:** server accepts client-side beta/entitlement flag.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** restricted feature/action enabled.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 13. Insecure Deserialization

**Find Insecure Deserialization:** serialized data from client/session/cache/queue deserialized unsafely.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker-controlled object changes behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 14. Type Confusion Deserialization

**Find Type Confusion Deserialization:** type discriminator/class name controlled by user.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** unexpected type instantiated or branch chosen.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 15. Queue Payload Tamper

**Find Queue Payload Tamper:** job ID/payload can be modified or replayed.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** worker processes unintended object/action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 16. Import Protected Field

**Find Import Protected Field:** CSV/JSON/XML import sets role/status/owner/balance.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** import bypasses UI restrictions.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 17. Backup Restore Trust Failure

**Find Backup Restore Trust Failure:** restore file overwrites protected config/users/roles.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** user-controlled backup changes security state.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 18. Archive Extraction Integrity

**Find Archive Extraction Integrity:** zip/tar import trusts paths/links/metadata.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** file placed or referenced outside intended boundary safely proven.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 19. Plugin Manifest Tamper

**Find Plugin Manifest Tamper:** plugin metadata controls permissions/update URL/code path.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tamper changes trusted install behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 20. Config Upload Trust

**Find Config Upload Trust:** tenant/admin uploads config consumed by higher-privileged service.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** config changes global or cross-tenant behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 21. Template/Theme Active Content

**Find Template/Theme Active Content:** theme upload allows active server/client code unexpectedly.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** code/data executes in trusted context.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 22. Webhook Missing Signature

**Find Webhook Missing Signature:** fake event accepted without HMAC/signature.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** state changes from unauthenticated event.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 23. Webhook Signature Not Raw Body

**Find Webhook Signature Not Raw Body:** signature validates parsed/transformed body incorrectly.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** body tamper accepted.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 24. Webhook Timestamp Replay

**Find Webhook Timestamp Replay:** old valid event replayed after freshness window.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** duplicate or stale state change.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 25. Webhook Event Type Confusion

**Find Webhook Event Type Confusion:** signature valid for one event type used as another.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** handler performs wrong action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 26. Webhook Resource Binding Missing

**Find Webhook Resource Binding Missing:** event for account A applied to account B.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** cross-tenant or wrong object state change.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 27. Webhook Retry Abuse

**Find Webhook Retry Abuse:** retry endpoint replays completed event.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** duplicate processing or rollback issue.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 28. Third-Party Event Trust

**Find Third-Party Event Trust:** payment/identity/shipping status trusted without server-side lookup.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** fake status alters order/account.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 29. SRI Missing on Sensitive Page

**Find SRI Missing on Sensitive Page:** third-party script on auth/admin page lacks SRI/CSP pinning.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** script integrity compromise affects sensitive context.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 30. Mutable CDN Asset

**Find Mutable CDN Asset:** critical JS loaded from mutable URL/version.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** asset can change outside release review.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 31. Unsigned Update Manifest

**Find Unsigned Update Manifest:** client/agent/plugin updater trusts unsigned manifest.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** update path can be tampered/downgraded.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 32. Artifact Digest Missing

**Find Artifact Digest Missing:** deploy pulls artifact/image without digest/checksum.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** mutable artifact trusted.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 33. Plugin Source Not Verified

**Find Plugin Source Not Verified:** marketplace/install accepts unverified plugin source.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** low-trust code gets high privilege.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 34. CI Artifact Integrity Gap

**Find CI Artifact Integrity Gap:** artifact from untrusted job consumed by privileged job.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** untrusted data crosses deploy boundary.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 35. Provenance Missing

**Find Provenance Missing:** release cannot be tied to source/build identity.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** software trust cannot be verified.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 36. Client-Side Integrity Only

**Find Client-Side Integrity Only:** frontend blocks tamper but backend accepts raw request.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server trusts absent client integrity.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 37. Audit Integrity Failure

**Find Audit Integrity Failure:** user can edit/delete audit/log entries for sensitive action.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** evidence trail tampered.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 38. Replay of Approval Token

**Find Replay of Approval Token:** signed/opaque approval token reusable after state change.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** old trusted data changes current state.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 39. Parser/Schema Mismatch

**Find Parser/Schema Mismatch:** schema rejects field but downstream mapper uses it.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** integrity validation not aligned with consumer.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

## 40. Reportability Filter

**Find Reportability Filter:** show trusted data/software object and accepted tamper/replay result.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** finding proves integrity failure, not just editable field.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use strict allowlists, server-side state, signature/HMAC with replay protection, safe serialization, schema validation at consumer, artifact signing, SRI/CSP, and provenance.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai trusted data/software integrity
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
→ missing SRI on low-risk public static page

Medium:
→ client state tamper on low-value setting
→ minor replay with no sensitive state

High:
→ mass assignment role/tenant/price
→ webhook event forgery
→ deserialization state tamper

Critical:
→ RCE deserialization
→ malicious update/plugin path
→ CI/CD deploy integrity compromise
→ signing key misuse
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A08 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ artifact/data that should be integrity-protected
→ baseline valid object/event/state
→ tampered or replayed variant
→ server accepted result or error proving unsafe trust
→ tester-owned before/after state
→ no malicious code execution outside explicit scope
```

**Jangan hanya laporkan:**

```text
→ uploading malicious plugin/code without permission
→ destructive deserialization payloads
→ claiming mass assignment if field ignored
→ replaying real payment/user events
```

---

## Retest Checklist

```text
Retest after fix:
→ untrusted serialized data disabled or safely parsed
→ mass assignment allowlist enforced
→ client state signed or moved server-side
→ webhook HMAC validates raw body/timestamp/nonce/event/path
→ update/artifact/plugin signed and verified
→ SRI/CSP or trusted self-hosted scripts used
→ async jobs revalidate state/signature
→ import schema rejects protected attributes
```

---

# Real-World Bug Bounty Insight Appendix

## A. Mass Assignment Role Change

**Pattern:** profile update accepts hidden `role` field.

```text
Find:
→ capture normal profile update
→ add role field to tester account
→ verify privilege/status changed
```

**Lesson:** Model binding needs explicit allowlist, not denylist.

---

## B. Fake Payment Webhook

**Pattern:** payment status changed by unsigned event.

```text
Find:
→ send tester event to webhook endpoint
→ set status paid/refunded safely
→ observe order state
```

**Lesson:** Webhook trust requires signature and server-side provider verification.

---

## C. Untrusted PR Artifact Signed

**Pattern:** release job signs artifact built from fork context.

```text
Find:
→ map workflow
→ show artifact boundary
→ prove signed output derives from untrusted source
```

**Lesson:** Integrity must span source, build identity, artifact, and release.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A08 harus menguji siapa/apa yang dipercaya server saat menerima data, event, artifact, atau state dari client/channel lain.

## Recent Bypass Branches

- **GraphQL/REST mass assignment:** cari field yang tidak ada di UI tetapi ada di schema/response/mobile API: role, owner, tenant, price, status, verified, admin, feature flag, dan workflow state.
- **Webhook integrity:** signature harus mengikat raw body, timestamp, event type, tenant, endpoint secret, dan replay window. Valid bila event tester dapat direplay/diubah untuk mengubah state yang tidak semestinya.
- **Unsigned client state:** cek cart, role flag, local storage, signed cookie, mobile config, dan JWT claims. Server harus menghitung ulang keputusan penting.
- **Import/worker trust:** CSV/JSON/XML import, bulk update, dan async worker sering percaya owner/tenant/status dari file client. Gunakan marker aman dan data tester.
- **Update/plugin/artifact integrity:** cek manifest signature, digest, rollback, mutable CDN, plugin registry ownership, dan admin install decision.

## Evidence Upgrade

Tunjukkan field diff sebelum/sesudah, request valid/invalid pembanding, event replay dengan test secret bila ada izin, dan proof bahwa server menerima data yang seharusnya authoritative dari backend.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **SDK-to-REST integrity:** SDK dapat expose path/field/scope yang tidak ada di UI. Trace argumen SDK sampai REST call dan validasi server-side.
- **Client primitive to API action:** DOM/CSPT/iframe gadget menjadi A08 jika bisa membuat credentialed API action yang mengubah state.
- **Artifact/source-map integrity:** build output dapat membocorkan hidden field, endpoint, package name, and stale authorization assumptions yang lalu dipakai untuk mass assignment.
- **AI/tool output integrity:** tool output, model response, generated file, and connector result harus dianggap untrusted input sebelum dipakai worker/action.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Client flag trust:** `isPro`, role, paid, verified, status, dan entitlement flag tidak boleh dipercaya dari local DB/client payload.
- **AI answer integrity:** jika AI/search summary menampilkan instruksi support, produk harus punya canonical verification channel dan monitoring poisoning.
- **Secret remediation integrity:** rotate, revoke, and audit exposed secrets; menghapus commit tidak cukup.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A08 Software or Data Integrity Failures: https://owasp.org/Top10/2025/A08_2025-Software_or_Data_Integrity_Failures/
- OWASP Deserialization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html
- OWASP Mass Assignment Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- PortSwigger Insecure deserialization: https://portswigger.net/web-security/deserialization
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
