# OWASP A04:2025 Cryptographic Failures — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **Data-flow first** trace sensitive data in transit, at rest, browser, cache, log, export, and backup.
- **Token and signature coverage** cek method/path/body/timestamp/audience/issuer/resource binding.
- **JWT/JWE/JWS real-world branches** algorithm confusion, kid/jku/x5u, audience/issuer, encrypted token replay.
- **Signed URL lifecycle** expiry, revocation, user binding, CDN cache, and permission removal.
- **Crypto triage** bedakan checksum/cache hash dari security crypto yang benar-benar melindungi data.

---

## Core Rule A04

A04 valid bila data sensitif, credential, token, session, signed URL, backup, webhook, update, or trust proof dapat dibaca, ditebak, dipalsukan, di-replay, di-downgrade, or dimanipulasi karena crypto tidak ada, salah konfigurasi, lemah, bocor, atau tidak diverifikasi penuh.

---

## Attack Surface Mapping

```text
Mapping A04:
→ data: password, PII, payment, health, token, API key, session, backup, cookie, signed URL
→ state: transit, rest, browser storage, logs, cache, analytics, export, database, object storage
→ primitive: TLS, HSTS, encryption, hashing, MAC, signature, JWT/JWS/JWE, random token
→ key lifecycle: generation, storage, rotation, scope, revocation, leakage, environment reuse
→ trust proof: certificate chain, audience, issuer, signature, nonce, timestamp, expiry, resource binding
→ impact: confidentiality leak, integrity tamper, account takeover, payment tamper, cross-tenant replay
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Secret in JS/log/source | may allow token forge, API access, or decrypt/sign |
| JWT accepts weak validation | claims can become authorization input |
| Signed URL survives permission removal | private data becomes bearer-link access |
| Weak randomness | reset/invite/API token can be guessed |
| Client-side encrypted blob only | often encoding or encryption without integrity |
| HTTP/mixed content | session or token can leak on network |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Transport and storage | 1-8 | TLS, HSTS, at-rest, logs, cache |
| Token and session crypto | 9-18 | JWT, signed URL, randomness, reset tokens |
| Integrity and signatures | 19-27 | HMAC, webhook, JWE, MAC, downgrade |
| Key lifecycle | 28-33 | leak, reuse, rotation, environment separation |
| Reporting and retest | 34-38 | severity, evidence, false positive control |

---

## Universal Testing Logic

```text
Find A04:
classify sensitive data and security decisions protected by crypto →
trace where data travels and rests →
identify primitive, key, token, and verification point →
test safe tamper, replay, downgrade, and lifecycle events with tester-owned data →
connect crypto failure to read, forge, replay, or tamper impact →
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

> Fokus A04 adalah membuktikan data atau trust decision dapat dibaca, dipalsukan, di-replay, atau diubah. Gunakan token/data tester, redaksi secret, dan jangan crack credential user nyata.

## A04 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| JWT manipulasi ditolak | cek `aud`, `iss`, `exp`, `nbf`, client lain, tenant lain, environment lain, refresh flow | cari validation gap selain signature |
| Signature/HMAC validasi ketat | missing vs invalid signature, body/path/method/timestamp coverage, replay old signature | cek fail-open atau signature tidak menutup action penuh |
| Signed URL masih 403 | logout, permission removal, other browser, CDN cache, old link, range request, filename/path tamper | cek lifecycle dan resource binding |
| Token tampak random | generate banyak token tester, cek length/charset/time/order, reuse, expiry, scope | cek entropy dan lifecycle tanpa brute force |
| Data encrypted | cek deterministic ciphertext, replay antar user, tamper error oracle, missing MAC, client-side key | bedakan confidentiality vs integrity |
| TLS terlihat baik | HTTP redirect chain, mixed content, cookie Secure, old API/download host, mobile base URL | cek transport gap di surface lain |
| Secret tidak di repo | JS bundle, source map, mobile app, CI log, error, analytics, env/debug endpoint | cari key leakage surface lain |
| Webhook signature ada | raw body vs parsed body, timestamp freshness, event type, account binding, retry | cek event integrity penuh |
| Key rotated | token lama, signed URL lama, cached key, staging key, kid/keyset cache | cek revocation propagation |
| Crypto issue tampak low | chain ke token forge, signed URL read, webhook fake event, payment tamper, tenant replay | validasi impact nyata |

## A04 Chaining Playbook

```text
Secret/key leak →
sign/forge/decrypt capability →
JWT/webhook/API/signed URL abuse →
A01/A07/A08 impact.

Weak token lifecycle →
logout/password change/revoke tidak mematikan token →
session/account persistence →
account or tenant access.

Signed URL not bound →
permission removed but URL works →
private export/file/invoice still accessible →
confidentiality impact.

Webhook HMAC gap →
fake or replayed event accepted →
order/payment/subscription state changes →
business impact.
```

**Rule chaining:** jangan berhenti di "pakai base64" atau "header crypto lemah"; tunjukkan trust decision yang benar-benar rusak.

---

# Methodology Patterns

## 1. Cleartext Sensitive Data in Transit

**Find Cleartext Sensitive Data in Transit:** cek HTTP fallback, mixed content, API base URL lama, webhook callback, file download, mobile endpoint.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** session/token/PII/credential/private data dikirim tanpa TLS.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 2. Missing HSTS on Auth Domain

**Find Missing HSTS on Auth Domain:** cek auth domain and subdomains after HTTPS login.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** network attacker can downgrade or cookie Secure policy becomes insufficient.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 3. Weak TLS Protocol or Cipher

**Find Weak TLS Protocol or Cipher:** gunakan safe scanner or passive evidence untuk old TLS/cipher/cert issue.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** sensitive authenticated service supports materially weak transport.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 4. Cookie Without Secure on Auth Flow

**Find Cookie Without Secure on Auth Flow:** cek Set-Cookie session/state/remember-me.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** cookie auth can travel over HTTP or mixed redirect path.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 5. Sensitive Data in Browser Storage

**Find Sensitive Data in Browser Storage:** cek localStorage/sessionStorage/IndexedDB/cache for token/PII.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** XSS or local compromise impact becomes session/data theft.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 6. Sensitive Data in Logs or Analytics

**Find Sensitive Data in Logs or Analytics:** trigger safe request then inspect visible logs/error/analytics payload.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** token/password/OTP/API key/PII appears in logs.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 7. Unencrypted Backup or Export

**Find Unencrypted Backup or Export:** cek backup/export/download artifacts.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** sensitive dataset stored/downloaded without encryption or access binding.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 8. Cache Stores Decrypted Private Data

**Find Cache Stores Decrypted Private Data:** private data decrypted by app then cached by CDN/browser/service worker.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** another user/session/logout can read decrypted data.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 9. Weak Password Storage

**Find Weak Password Storage:** prove via config/hash format/test account evidence.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** plaintext, reversible encryption, unsalted fast hash, weak work factor.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 10. Deprecated Hash for Security

**Find Deprecated Hash for Security:** identify MD5/SHA1 or custom hash used for password/token/signature security.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** hash protects security decision, not harmless checksum.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 11. Static IV / Deterministic Encryption

**Find Static IV / Deterministic Encryption:** same plaintext creates same ciphertext for sensitive data.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** pattern leakage or tamper/replay impacts confidentiality/integrity.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 12. Encryption Without Integrity

**Find Encryption Without Integrity:** modify ciphertext/client blob and observe accepted altered state/error oracle.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server accepts tampered encrypted data or leaks oracle behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 13. JWT alg Confusion

**Find JWT alg Confusion:** test only tester-owned token for alg/header validation weakness.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server accepts forged claims or weak algorithm path.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 14. JWT kid/jku/x5u Header Trust

**Find JWT kid/jku/x5u Header Trust:** cek key lookup header controls or remote key trust.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker can influence verification key in safe proof.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 15. JWT Missing aud/iss Validation

**Find JWT Missing aud/iss Validation:** token from one client/tenant/environment accepted elsewhere.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** cross-client or cross-tenant token replay.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 16. JWT Expiry / nbf / iat Ignored

**Find JWT Expiry / nbf / iat Ignored:** modify/replay token around expiry with tester account.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** expired/not-yet-valid token accepted for sensitive action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 17. JWE Replay or Audience Gap

**Find JWE Replay or Audience Gap:** encrypted token cannot be read but can be replayed across user/session/resource.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** confidential token still lacks binding/integrity policy.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 18. Refresh Token Crypto Lifecycle Failure

**Find Refresh Token Crypto Lifecycle Failure:** old refresh token remains valid after rotation/logout/password change.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** session takeover persists after revocation event.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 19. Signed URL Missing Expiry

**Find Signed URL Missing Expiry:** download/export/invoice link remains valid too long.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** bearer link exposes private data after expected lifetime.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 20. Signed URL Not Bound to User/Permission

**Find Signed URL Not Bound to User/Permission:** URL works after logout, permission removal, or from another account.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** private resource access ignores current authorization.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 21. Signed URL Path Tamper

**Find Signed URL Path Tamper:** change object/path/size/disposition while preserving signature.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** signature does not cover full resource decision.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 22. Predictable Reset Token

**Find Predictable Reset Token:** generate multiple tester tokens and compare entropy/time/sequence.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** token can be guessed or narrowed enough for realistic takeover.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 23. Predictable Invite / Magic Link

**Find Predictable Invite / Magic Link:** analyze tester invite or magic link tokens.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** login/account join token guessable, reusable, or not bound.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 24. Weak OTP / Recovery Code Space

**Find Weak OTP / Recovery Code Space:** test low-count rate-limited behavior, not brute force.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** code space plus no throttling makes guessing practical.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 25. API Key Entropy or Prefix Leak

**Find API Key Entropy or Prefix Leak:** create tester keys, inspect length/charset/prefix and logs.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** key is guessable, overexposed, or prefix leaks tenant/user.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 26. Webhook HMAC Not Verified

**Find Webhook HMAC Not Verified:** modify body/event/timestamp/signature on tester webhook.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** fake or replayed event accepted.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 27. Signature Does Not Cover Body

**Find Signature Does Not Cover Body:** change body while keeping valid signature from old body.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** integrity proof does not protect action data.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 28. Timestamp Replay in Signed Request

**Find Timestamp Replay in Signed Request:** replay old signed request after expected freshness.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server does not enforce nonce/timestamp/idempotency.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 29. Crypto Downgrade Version

**Find Crypto Downgrade Version:** force legacy token/signature/cipher format.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server accepts weaker legacy format for sensitive action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 30. Hardcoded Secret in Client

**Find Hardcoded Secret in Client:** inspect JS/mobile/source map for keys used server-side.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** secret allows API access, signing, decrypting, or tenant action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 31. Environment Key Reuse

**Find Environment Key Reuse:** staging/dev key signs tokens accepted by prod or vice versa.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** lower-trust env can mint prod-trusted artifacts.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 32. Missing Key Rotation / Revocation

**Find Missing Key Rotation / Revocation:** old API key/JWT signing key/signed URL remains valid after rotation event.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** compromise window remains unbounded.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 33. KMS/IAM Key Overpermission

**Find KMS/IAM Key Overpermission:** cloud role can decrypt/sign more resources than intended.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tenant/service can access crypto operation outside scope.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 34. Public Certificate or Pinning Misuse

**Find Public Certificate or Pinning Misuse:** mobile/client pinning disabled or trusts user-added cert for sensitive endpoint.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** practical only if program recognizes client transport risk.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 35. Crypto Error Oracle

**Find Crypto Error Oracle:** different error/timing reveals padding/decryption/signature validation states.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** oracle enables data recovery or token validity probing.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 36. Custom Crypto Scheme

**Find Custom Crypto Scheme:** identify homegrown encryption/signing/obfuscation for sensitive state.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** scheme fails standard properties or accepts tamper/replay.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

## 37. Reportability Filter

**Find Reportability Filter:** prove protected data/security decision and exact broken crypto property.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** finding is not just “uses base64” without sensitive impact.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use modern vetted primitives, strong key management, full signature coverage, strict token validation, rotation, and lifecycle-bound authorization.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai crypto-protected state
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
→ missing HSTS on static-only domain
→ base64 encoding noted without sensitive impact

Medium:
→ weak token lifecycle on low-risk feature
→ sensitive data in limited browser storage

High:
→ JWT claim forge for user data
→ signed URL bypass
→ password hash weakness
→ webhook forgery changing business state

Critical:
→ signing key leak
→ admin token forge
→ decrypt sensitive data at scale
→ payment/signature tamper
→ cross-tenant crypto key reuse
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A04 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ data or decision protected by crypto
→ where failure occurs: transit, storage, token, signature, key, randomness, lifecycle
→ baseline and tampered/replayed request with tester-owned data
→ before/after state or redacted data proof
→ impact mapped to confidentiality/integrity/authentication
→ no cracking of real user secrets or unauthorized data access
```

**Jangan hanya laporkan:**

```text
→ base64-only claim without sensitive data or server trust
→ weak cipher list on non-auth static host only
→ hash cracking against real user passwords
→ claiming JWT issue without accepted forged/replayed token
```

---

## Retest Checklist

```text
Retest after fix:
→ TLS/HSTS enforced on auth/data domains
→ passwords use adaptive salted hashing
→ secrets stored in secret manager and rotated
→ JWT validates signature, alg, kid source, aud, iss, exp, nbf, scope
→ signed URLs expire and bind to resource/user/permission
→ webhook signatures cover raw body, method/path, timestamp, nonce
→ tokens use CSPRNG and sufficient entropy
→ client-controlled encrypted state also has integrity or is server-side
```

---

# Real-World Bug Bounty Insight Appendix

## A. JWT Works Across Tenants

**Pattern:** token minted for tenant A accepted for tenant B because audience/tenant binding missing.

```text
Find:
→ create tester tenants A and B
→ obtain token for A
→ call B endpoint with A token
→ show accepted action/data
```

**Lesson:** Signature validity is not enough; token claims must bind to audience, issuer, tenant, and resource.

---

## B. Signed Export URL Survives Removal

**Pattern:** user removed from project can still download old report link.

```text
Find:
→ generate export as authorized tester
→ remove tester access
→ reuse signed URL
→ show private report still downloads
```

**Lesson:** Signed URLs need expiry, revocation semantics, and authorization-sensitive resource binding.

---

## C. Webhook Body Tamper

**Pattern:** signature validates header but not full raw body/action.

```text
Find:
→ capture tester webhook
→ change harmless field/action target
→ reuse signature
→ observe accepted event
```

**Lesson:** HMAC must cover raw body and context, and replay must be blocked.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A04 perlu menguji crypto sebagai binding problem antara token, route, parser, user, tenant, object, dan waktu.

## Recent Bypass Branches

- **OAuth/OIDC redirect parser mismatch:** cek exact match vs regex/wildcard, encoded delimiter, path normalization, query/fragment confusion, duplicate `redirect_uri`, punycode, trailing dot, mobile deep link, dan app-link fallback.
- **Signed URL/token binding:** pastikan signature mengikat method, path canonical, object, tenant, user, expiry, content-type, dan revocation state. Valid bila token tester bisa dipakai untuk object/tenant lain atau action berbeda.
- **JWT/JWK lifecycle:** cek issuer/audience confusion, stale JWKS, key rotation failure, accepting weak/none algorithm, kid confusion, dan token yang tetap valid setelah logout/password/MFA change.
- **Reset/magic link leakage:** cek entropy plus lifecycle: reuse, referrer/log/analytics exposure, host binding, tenant binding, auto-login without MFA, dan session invalidation.
- **CSP/crypto boundary:** CSP bukan pengganti token binding. Jika CSP bypass ditemukan, chain ke sink dan data/action yang benar-benar terdampak.

## Evidence Upgrade

Redaksikan token dan secret. Tunjukkan token A vs token B, claim/header non-sensitive, expected binding, actual bypass, dan request pembanding yang gagal ketika binding benar.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **Bcrypt truncation:** tambahkan test storage policy untuk input panjang, pre-hash strategy, normalization, and password-change invalidation.
- **ETag/cache privacy boundary:** treat ETag, cache validator, and conditional request sebagai cryptographic/privacy oracle jika bisa membedakan user state lintas origin.
- **OAuth consent vs token reality:** bandingkan consent screen, requested scope, token claims, actual API permission, and revocation behavior.
- **Encryption oracle:** jika ada decrypt/verify endpoint, buktikan oracle dengan marker aman dan timing/error diff minimal, bukan brute force.
- **AI connector secret lifecycle:** model API key, MCP token, vector DB credential, webhook secret, dan delegated OAuth token tidak boleh muncul di prompt trace, agent memory, tool logs, browser storage, atau support export. Validasi hanya dengan tester-owned connector/token dan redacted evidence.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Mobile secret storage:** token, refresh token, API key, dan session ID tidak boleh tersimpan plaintext di SharedPreferences, SQLite, file, log, backup, atau WebView storage.
- **Revocation evidence:** untuk secret lama/bocor, report aman harus menunjukkan scope/lifetime/rotation gap tanpa memakai secret untuk akses tidak sah.
- **Key lifecycle:** private key, signing key, TLS cert, dan webhook secret perlu owner, expiry, rotation, dan audit trail.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A04 Cryptographic Failures: https://owasp.org/Top10/2025/A04_2025-Cryptographic_Failures/
- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP JSON Web Token Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- PortSwigger JWT attacks: https://portswigger.net/web-security/jwt
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
