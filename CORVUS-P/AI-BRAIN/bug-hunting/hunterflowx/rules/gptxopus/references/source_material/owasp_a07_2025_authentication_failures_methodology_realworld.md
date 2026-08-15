# OWASP A07:2025 Authentication Failures — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **Auth surface complete** register, login, reset, magic link, MFA, SSO, API key, session, device.
- **Lifecycle testing** logout, password change, MFA enable, revoke, role removal, account deletion.
- **MFA bypass branches** alternate flow, remember-device, backup code, reset auto-login, OAuth path.
- **OAuth/OIDC/SAML real-world** state/nonce/PKCE/aud/iss/account linking/redirect strictness.
- **Safe testing** no credential stuffing, no CAPTCHA bypass, no third-party account takeover.

---

## Core Rule A07

A07 valid bila sistem dapat diyakinkan bahwa actor yang tidak sah adalah user sah, atau bila login, session, recovery, MFA, OAuth/OIDC/SAML, API key, device trust, or token lifecycle gagal membuktikan identitas dengan benar.

---

## Attack Surface Mapping

```text
Mapping A07:
→ entry: register, login, SSO, OAuth/OIDC, SAML, magic link, password reset, MFA, device trust
→ credential: password, OTP, TOTP, WebAuthn/passkey, recovery code, API key, session, refresh token
→ lifecycle: issue, rotate, refresh, logout, revoke, timeout, password change, email/phone change
→ actor state: anonymous, logged-in, locked, suspended, invited, deleted, unverified, partially authenticated
→ trust proof: state, nonce, PKCE, aud, iss, signature, session binding, device binding
→ impact: account takeover, MFA bypass, session replay, token reuse, enumeration, cross-tenant SSO
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Different messages/timing | enumeration and targeted attack |
| Alternate login path | often misses MFA/rate/session policy |
| Long-lived refresh token | revocation failures are high impact |
| Email-only account linking | SSO/OAuth takeover risk |
| Remember-device cookie | can become MFA bypass |
| Mobile legacy auth | old flows may skip modern controls |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Enumeration and rate limit | 1-8 | login/reset/MFA/OTP abuse resistance |
| Recovery and MFA | 9-18 | reset, magic link, backup code, remember device |
| Session lifecycle | 19-27 | fixation, logout, revoke, token refresh |
| Federated auth | 28-38 | OAuth/OIDC/SAML/account linking |
| API/device/auth edge | 39-44 | API key, websocket, mobile, service account |

---

## Universal Testing Logic

```text
Find A07:
map every path that creates or resumes identity →
compare success/failure behavior with tester accounts →
test rate/lockout safely with low counts →
test session/token lifecycle after invalidation events →
test MFA/recovery/federated alternate paths →
prove auth failure without touching third-party accounts →
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

> A07 harus diuji hanya dengan akun tester. Jangan credential stuffing, jangan bypass CAPTCHA, dan jangan takeover akun pihak ketiga. Bypass di sini berarti mencari auth path yang tidak menerapkan policy yang sama.

## A07 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| Login utama aman | register, reset, magic link, invite, mobile API, OAuth, SAML, API token, websocket | cari alternate identity entry |
| Enumeration tidak terlihat | timing, response size, email sent behavior, reset/register/MFA prompt, rate-limit difference | cek reliable account discovery |
| Rate limit ada | per endpoint/account/IP/device/tenant, reset vs login, MFA vs password, mobile vs web | cek coverage tanpa high-volume test |
| MFA prompt muncul | direct API after password, remember-device, reset auto-login, OAuth/social login, backup code, old session | cek MFA enforcement everywhere |
| Reset token aman | host header, expiry, one-time use, old session, email change, token replay, mobile flow | cek recovery lifecycle |
| Session logout aman | refresh token, websocket, API key, remember-me, signed URL, mobile session | cek full session invalidation |
| OAuth redirect ketat | open redirect chain, path normalization, subdomain trust, state/nonce/PKCE, app/client confusion | cek token/code binding |
| SAML signature ada | audience/recipient, assertion vs response signature, replay, RelayState, IdP-initiated flow | cek federated validation gap |
| API key revoked | old key cache, scoped endpoint, GraphQL/websocket, mobile SDK, service account | cek machine auth lifecycle |
| Auth bug low impact | chain enumeration → reset/MFA gap, token replay → BAC, OAuth link → takeover | naikkan impact dengan safe tester-victim account |

## A07 Chaining Playbook

```text
Enumeration →
targeted reset/MFA/social login behavior →
recovery or MFA bypass proof →
tester-victim account access.

Old refresh token →
password change/logout/revoke →
new access token still issued →
persistent session takeover impact.

OAuth account linking →
unverified email or issuer confusion →
wrong external identity binds →
account takeover.

MFA bypass →
full session →
A01 access to sensitive tenant/object →
impact beyond login.
```

**Rule chaining:** buat dua akun tester: attacker dan victim. Semua bukti takeover harus berhenti pada akun tester-victim.

---

# Methodology Patterns

## 1. Username / Email Enumeration

**Find Username / Email Enumeration:** compare login/register/reset responses, timing, email behavior.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** valid accounts can be reliably identified.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 2. Password Reset Enumeration

**Find Password Reset Enumeration:** reset flow reveals whether account exists.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** target list building becomes practical.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 3. MFA Enrollment Enumeration

**Find MFA Enrollment Enumeration:** MFA prompt differs for valid users.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** user security posture leaks.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 4. Weak Login Rate Limit

**Find Weak Login Rate Limit:** small controlled attempts show no throttling/lockout.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** credential attack feasible without large test.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 5. OTP Rate Limit Missing

**Find OTP Rate Limit Missing:** low-count proof shows no throttle on OTP verification.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** code guessing feasible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 6. Password Spraying Defense Gap

**Find Password Spraying Defense Gap:** lockout/rate limit keyed only per account/IP weakly.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** small distributed-like proof with own accounts indicates gap.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 7. Weak Password Policy

**Find Weak Password Policy:** obvious weak/breached password accepted in sensitive app.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** policy materially increases takeover risk.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 8. Credential Stuffing Detection Gap

**Find Credential Stuffing Detection Gap:** no alert/session notification after suspicious low-count attempts.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** defense visibility weak.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 9. Password Reset Token Reuse

**Find Password Reset Token Reuse:** reset link works more than once or after password changed.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account recovery token not one-time.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 10. Password Reset Token Expiry Failure

**Find Password Reset Token Expiry Failure:** old reset link remains valid too long.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** stolen email link remains dangerous.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 11. Host Header Poisoning in Reset

**Find Host Header Poisoning in Reset:** reset link uses attacker-controlled host/header.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** token delivered in link can be redirected in scope.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 12. Magic Link Replay

**Find Magic Link Replay:** passwordless link reusable or not bound to device/session.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** login can be replayed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 13. Invite Link Takeover

**Find Invite Link Takeover:** invite can be accepted by wrong identity or reused.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tenant/account access granted incorrectly.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 14. Email Change Confirmation Bypass

**Find Email Change Confirmation Bypass:** new email becomes active before old/current owner confirmation.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account recovery path can be hijacked.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 15. Phone/SMS Recovery Weakness

**Find Phone/SMS Recovery Weakness:** phone change or SMS recovery bypasses stronger auth.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account takeover path exists.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 16. MFA Direct Access Bypass

**Find MFA Direct Access Bypass:** after password step, protected route/API works without completing MFA.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** partial auth accepted as full auth.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 17. MFA Alternate Flow Bypass

**Find MFA Alternate Flow Bypass:** OAuth/mobile/reset/API path creates session without MFA.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** MFA policy inconsistent.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 18. Remember Device Cookie Abuse

**Find Remember Device Cookie Abuse:** remember-device cookie not bound or tamperable.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** MFA skipped on attacker-controlled context.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 19. Recovery Code Weakness

**Find Recovery Code Weakness:** backup codes shown/reused/not invalidated/guessable.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** MFA recovery bypass.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 20. WebAuthn/Passkey Downgrade

**Find WebAuthn/Passkey Downgrade:** strong auth account can downgrade to weaker factor silently.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** phishing-resistant control bypassed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 21. Session Fixation

**Find Session Fixation:** session ID before login remains after login or attacker can set it.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** known session becomes authenticated.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 22. Session Not Rotated After Privilege Change

**Find Session Not Rotated After Privilege Change:** role/MFA/login does not rotate session.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** old session retains or gains privilege.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 23. Logout Invalidation Failure

**Find Logout Invalidation Failure:** session/access/refresh token still works after logout.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** session theft remains useful.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 24. Password Change Invalidation Failure

**Find Password Change Invalidation Failure:** old sessions/tokens survive password change.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account recovery does not evict attacker.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 25. MFA Enable Invalidation Failure

**Find MFA Enable Invalidation Failure:** old sessions bypass newly enabled MFA.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** security upgrade ineffective.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 26. Device Revoke Failure

**Find Device Revoke Failure:** revoked device/session continues API access.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** device management false sense of security.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 27. Refresh Token Rotation Failure

**Find Refresh Token Rotation Failure:** old refresh token remains valid after rotation.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** stolen token can persist.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 28. JWT Session Cross-Client Replay

**Find JWT Session Cross-Client Replay:** token minted for one client/app accepted by another.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** audience/client binding missing.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 29. OAuth Redirect URI Weakness

**Find OAuth Redirect URI Weakness:** callback allowlist accepts attacker-controlled redirect/open redirect.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** code/token leakage possible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 30. OAuth State Missing

**Find OAuth State Missing:** login CSRF or account binding confusion possible.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** victim session can be linked to attacker identity.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 31. OIDC Nonce Missing

**Find OIDC Nonce Missing:** ID token replay/substitution possible.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** auth response not bound to session.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 32. PKCE Missing for Public Client

**Find PKCE Missing for Public Client:** mobile/SPA code interception risk.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** auth code can be redeemed by attacker.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 33. Issuer/Audience Confusion

**Find Issuer/Audience Confusion:** token from other issuer/client/tenant accepted.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** federated token replay.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 34. Account Linking by Email Only

**Find Account Linking by Email Only:** unverified external email links to existing account.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tester-victim account takeover possible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 35. SAML Signature Validation Failure

**Find SAML Signature Validation Failure:** assertion/response/signature location/audience weak.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** forged or replayed assertion accepted.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 36. SAML RelayState Abuse

**Find SAML RelayState Abuse:** RelayState/open redirect/session binding weak.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** SSO flow can be hijacked or confused.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 37. IdP-Initiated SSO Weakness

**Find IdP-Initiated SSO Weakness:** unsolicited assertion accepted without session binding.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** login CSRF or account confusion.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 38. API Key Scope Failure

**Find API Key Scope Failure:** API key accesses beyond intended tenant/scope.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** machine auth bypass.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 39. API Key Revocation Failure

**Find API Key Revocation Failure:** revoked key remains valid.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** long-lived unauthorized access.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 40. WebSocket Auth Lifecycle Gap

**Find WebSocket Auth Lifecycle Gap:** socket remains authenticated after logout/revoke.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** real-time data/action continues.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 41. Mobile Legacy Login

**Find Mobile Legacy Login:** old mobile endpoint skips MFA/rate/token policy.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** modern auth controls bypassed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 42. Partially Authenticated State Abuse

**Find Partially Authenticated State Abuse:** pre-MFA/pre-verification session can access sensitive API.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** partial identity treated as full user.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 43. Suspended/Deleted Account Login

**Find Suspended/Deleted Account Login:** disabled account token/session still works.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account status not enforced.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

## 44. Reportability Filter

**Find Reportability Filter:** prove identity/session control impact with tester accounts only.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** finding shows auth bypass, not just cosmetic inconsistency.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** centralize auth policy, enforce MFA/session lifecycle across all flows, validate OAuth/OIDC/SAML strictly, rotate sessions, throttle risky endpoints, and bind tokens to audience/client/tenant/device.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai identity proof and session lifecycle
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
→ minor message inconsistency without practical enumeration

Medium:
→ reliable account enumeration
→ weak throttling on low-risk auth

High:
→ MFA bypass
→ reset token replay
→ refresh token not revoked
→ OAuth account linking to tester victim

Critical:
→ full account takeover
→ admin auth bypass
→ SSO assertion forgery
→ cross-tenant token acceptance
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A07 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ tester accounts and roles used
→ auth flow and endpoint
→ baseline expected behavior
→ bypass/failure behavior
→ token/session before and after invalidation event
→ impact: account access, MFA bypass, token replay, enumeration, tenant crossing
→ proof no third-party account touched
```

**Jangan hanya laporkan:**

```text
→ credential stuffing against real users
→ CAPTCHA bypass attempts
→ claiming enumeration from one ambiguous response
→ taking over third-party accounts
```

---

## Retest Checklist

```text
Retest after fix:
→ generic auth failure messages/timing where needed
→ rate limits on login/reset/MFA/OTP
→ MFA enforced on all auth paths
→ session rotates after login and privilege changes
→ logout/password change/revoke invalidate sessions and refresh tokens
→ OAuth validates redirect_uri/state/nonce/PKCE/iss/aud
→ SAML validates signatures/audience/recipient
→ account linking requires verified ownership
```

---

# Real-World Bug Bounty Insight Appendix

## A. MFA Bypass via Password Reset Auto-Login

**Pattern:** reset flow creates full session without MFA.

```text
Find:
→ enable MFA on tester account
→ complete reset
→ access protected route without MFA
```

**Lesson:** MFA policy must apply after recovery flows too.

---

## B. Refresh Token Survives Password Change

**Pattern:** old refresh token keeps issuing access tokens.

```text
Find:
→ save token
→ change password
→ call refresh
→ access sensitive API
```

**Lesson:** Credential reset must revoke refresh tokens and sessions.

---

## C. OAuth Email Linking Takeover

**Pattern:** external account with same unverified email links to local account.

```text
Find:
→ create tester-victim account
→ link external identity path
→ show session maps to wrong account
```

**Lesson:** Account linking requires verified identity and issuer-specific stable subject.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A07 paling sering naik severity saat alternate auth path melewati kontrol utama.

## Recent Bypass Branches

- **MFA bypass outside OTP page:** cek password reset auto-login, magic link, invite accept, remember-device, recovery code, mobile login, OAuth linking, session restore, dan partially authenticated direct route.
- **GraphQL auth bypass:** cari mutation seperti create user, update role, reset password, link identity, change email, issue token, dan admin setting. Valid bila mutation bisa dipanggil tanpa auth state yang sama dengan UI.
- **OAuth/OIDC account takeover:** cek redirect URI parser mismatch, missing state/nonce, PKCE downgrade, issuer/audience confusion, account linking by email, IdP-initiated SSO, dan domain claim trust.
- **Session lifecycle:** token harus invalid setelah logout, password change, MFA enable/disable, device revoke, user suspension, dan tenant removal.
- **Evidence-driven auth claims:** siapkan device/session list, MFA enabled state, request IDs, login history, email alert, dan replay table. Hindari credential stuffing atau brute force OTP.

## Evidence Upgrade

Gunakan dua akun tester dan tabel lifecycle:

```text
Action | Expected invalidation | Actual session/token state | Evidence
```

Triage auth bug biasanya menolak klaim yang tidak menunjukkan state sebelum/sesudah.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **MCP/OAuth:** uji dynamic client registration, redirect URI controls, localhost callback, PKCE downgrade, token audience, tool connector scope, and delegated auth.
- **OAuth gadget correlation:** iframe, clickjacking, open redirect, CSPT, JSONP, upload origin, and referrer gadget baru bernilai jika dapat menyentuh auth flow.
- **Passkey/session edge:** enroll, revoke, fallback auth, device move, recovery flow, old session survival, and token invalidation.
- **SAML/XPath confusion:** jika SAML muncul, test parser/canonicalization mismatch, XPath selection, signature wrapping class, RelayState, and IdP-initiated flow.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Deep link auth path:** custom scheme/app link/intent URL harus bind user state, trusted origin, action confirmation, dan redirect target.
- **Mobile token lifecycle:** logout/password reset/MFA change harus menghapus WebView/local/session storage dan revoke refresh token server-side.
- **Support impersonation:** fake CS/social-account risk harus diterjemahkan ke official support verification, warning UX, dan anti-abuse controls.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A07 Authentication Failures: https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/
- OWASP Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- PortSwigger Authentication: https://portswigger.net/web-security/authentication
- PortSwigger OAuth: https://portswigger.net/web-security/oauth
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
