# OWASP A06:2025 Insecure Design — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **Invariant-first testing** tulis aturan bisnis sebelum request replay.
- **Workflow state machine** uji skip, repeat, reorder, stale, race, rollback, and alternate actor.
- **Money/quota/entitlement realism** fokus pada price, refund, coupon, usage, subscription, inventory, and limits.
- **Separation of duties** uji self-approval, delegated admin, support/finance boundaries.
- **Async and webhook design** cek worker/callback yang memindahkan state tanpa revalidation.

---

## Core Rule A06

A06 valid bila sistem secara desain mengizinkan alur, state transition, trust boundary, resource usage, or business action yang melanggar invariant domain, meskipun endpoint, input validation, dan auth teknis terlihat bekerja.

---

## Attack Surface Mapping

```text
Mapping A06:
→ asset: money, credit, order, seat, inventory, account, tenant, quota, entitlement, identity
→ actor: buyer, seller, admin, support, finance, guest, suspended user, integration, worker
→ state: draft, pending, paid, shipped, refunded, approved, cancelled, expired, locked, transferred
→ invariant: one-time, max amount, owner-only, sequence order, quota, cooldown, independent approval
→ workflow: create, review, confirm, pay, approve, fulfill, refund, cancel, retry, rollback
→ abuse: skip step, repeat step, reorder step, change object between steps, race, boundary values
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Multi-step flow | state machine often has unprotected transitions |
| Client sends price/role/risk | server may trust business decision from client |
| One-time reward/refund/coupon | race/replay produces direct value |
| Approval workflow | separation of duties bugs pay well |
| Async callback/worker | state may not be revalidated at commit |
| Suspended/expired/deleted states | edge state often bypasses design assumptions |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Workflow and state | 1-10 | skip, repeat, stale, impossible transition |
| Business value | 11-20 | price, coupon, refund, quota, inventory |
| Trust and identity design | 21-29 | delegation, recovery, tenant, support, SSO linking |
| Race and async | 30-36 | TOCTOU, webhook, worker, rollback |
| Reporting | 37-40 | impact, evidence, retest |

---

## Universal Testing Logic

```text
Find A06:
write intended business invariant in one sentence →
map actors, states, transitions, and trust boundaries →
execute normal baseline with tester-owned object →
try invalid sequence/value/state/actor/race safely →
prove before/after business impact without harming real users →
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

> A06 tidak selalu punya "payload"; bypass-nya adalah menemukan urutan, state, actor, atau invariant yang desainnya lupa dicek. Semua validasi harus memakai resource tester dan berhenti sebelum financial/destructive harm.

## A06 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| Step final ditolak | old draft, stale token, direct API, mobile route, GraphQL mutation, callback endpoint | cek workflow step skipping |
| One-time action aman | replay, retry, race kecil, alternate endpoint, different session, async job retry | cek idempotency dan locking |
| Price/quantity aman di UI | raw API, currency/locale, negative/zero/fractional, old quote, coupon stacking, tax/shipping field | cek business invariant server-side |
| Role separation aman | self-approve via bulk/import/API v1, delegated admin, support/finance endpoint, webhook transition | cek separation of duties |
| Tenant design aman | reseller/partner/support scope, shared object, inherited role, pending invite, archived project | cek boundary by design |
| Rate limit ada | alternate keying: account vs IP vs device vs tenant, endpoint variant, async export, reset/invite path | cek abuse-resistance tanpa load test |
| Recovery flow aman | fallback channel, support override, email/phone change, old session, SSO linking | cek weakest recovery path |
| State transition aman | cancelled/refunded/deleted/expired/suspended edge state, approve/cancel race, edit-after-lock | cek impossible state |
| Worker validates | delayed job after role removal, webhook replay, stale price/permission at job creation | cek revalidation at execution |
| Impact belum jelas | hubungkan ke money, quota, inventory, tenant integrity, account control, or compliance | naikkan reportability |

## A06 Chaining Playbook

```text
Small workflow bypass →
state moves to pending/approved incorrectly →
async worker commits later →
money/quota/inventory/account impact.

Client-trusted business value →
raw API changes field →
server persists value →
billing/entitlement/order integrity impact.

Weak recovery fallback →
identity proof bypass →
session created →
A07 account takeover or A01 tenant access.

Race on one-time action →
duplicate reward/refund/coupon →
business loss proof with tester-owned data.
```

**Rule chaining:** tulis invariant eksplisit: "user tidak boleh X sebelum Y". Tanpa invariant, temuan A06 sulit ditriage.

---

# Methodology Patterns

## 1. Workflow Step Skipping

**Find Workflow Step Skipping:** call final/confirm endpoint without required previous step.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** final state achieved without verification/payment/review.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 2. Step Reordering

**Find Step Reordering:** perform steps in unexpected order.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** workflow accepts impossible sequence.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 3. Stale Draft Reuse

**Find Stale Draft Reuse:** reuse old draft/order/form after policy or price changed.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** old state completes sensitive action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 4. Stale Token Reuse

**Find Stale Token Reuse:** reuse approval/reset/invite/checkout token after expiry/cancel.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** token still changes state.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 5. One-Time Action Replay

**Find One-Time Action Replay:** replay coupon/voucher/trial/reward/vote/redeem.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** one-time rule executes more than once.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 6. Double Submit / Race

**Find Double Submit / Race:** send two valid mutually exclusive requests in parallel.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** both commits succeed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 7. Approve and Cancel Conflict

**Find Approve and Cancel Conflict:** race approval/cancel/refund/capture.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** object reaches impossible state.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 8. Edit After Approval

**Find Edit After Approval:** modify locked/approved/shipped/paid object.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** post-approval data changes without re-review.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 9. Delete/Restore State Abuse

**Find Delete/Restore State Abuse:** restore deleted/archived object with old permissions.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** sensitive object/action reappears incorrectly.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 10. Expired/Suspended User Action

**Find Expired/Suspended User Action:** use suspended/expired account token or pending invite.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** restricted actor still performs action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 11. Price Tampering

**Find Price Tampering:** alter price/total/line item client-side or via API.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server charges/records attacker-controlled amount.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 12. Quantity Boundary

**Find Quantity Boundary:** use zero/negative/fractional/huge quantity.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** credit, free item, overflow, or inconsistent order.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 13. Currency Mismatch

**Find Currency Mismatch:** change currency/locale/tax/shipping fields.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** payment/order amount becomes inconsistent.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 14. Coupon Stacking

**Find Coupon Stacking:** combine discounts that should be mutually exclusive.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** discount exceeds intended policy.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 15. Refund Without Capture

**Find Refund Without Capture:** request refund on unpaid/failed/cancelled order.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** credit/refund state created without valid payment.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 16. Partial Refund Abuse

**Find Partial Refund Abuse:** repeat partial refunds or modify amount after approval.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** refund total exceeds paid amount.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 17. Subscription Plan Downgrade Abuse

**Find Subscription Plan Downgrade Abuse:** change plan/seat/quota around billing boundary.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** entitlement exceeds paid plan.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 18. Quota Reset Abuse

**Find Quota Reset Abuse:** trigger trial/reset/import/export to reset quota.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** usage limit bypassed.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 19. Inventory Reservation Abuse

**Find Inventory Reservation Abuse:** hold item/ticket/seat without payment or release.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** scarce inventory blocked or acquired unfairly.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 20. Reward/Credit Generation

**Find Reward/Credit Generation:** abuse referral/promo/loyalty flow.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** credit generated outside policy.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 21. Client Trust Decision

**Find Client Trust Decision:** client sends verified, risk_score, plan, entitlement, role, price.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server accepts client decision.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 22. Self-Approval

**Find Self-Approval:** same actor creates and approves/refunds/reviews.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** separation of duties missing.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 23. Support Override Abuse

**Find Support Override Abuse:** support/admin flow can bypass proof of ownership.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** account or data access granted with weak evidence.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 24. Account Recovery Weak Design

**Find Account Recovery Weak Design:** security questions/phone/email fallback too weak.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tester-victim account recoverable without strong proof.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 25. OAuth Account Linking Design

**Find OAuth Account Linking Design:** link external identity by email/weak normalization.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** wrong identity binds to account.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 26. Tenant Delegation Confusion

**Find Tenant Delegation Confusion:** partner/reseller/support can act outside explicit delegation.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tenant boundary violated by design.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 27. Shared Workspace Role Ambiguity

**Find Shared Workspace Role Ambiguity:** multi-role user inherits stronger permission unexpectedly.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** role composition grants unintended action.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 28. Visibility Default Too Broad

**Find Visibility Default Too Broad:** new object/link/project defaults public/shared.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** private data exposed by default design.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 29. Notification Spoofing Design

**Find Notification Spoofing Design:** user controls sender/tenant/event in notification.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** phishing or tenant spoofing inside trusted app.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 30. TOCTOU Ownership Change

**Find TOCTOU Ownership Change:** authorization checked before ownership/state changes.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** action commits after user loses right.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 31. Webhook State Transition

**Find Webhook State Transition:** external event moves order/account state without validating origin/context.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** fake/replayed event changes business state.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 32. Async Worker Stale State

**Find Async Worker Stale State:** worker processes job with old permission/price/state.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** delayed action ignores current policy.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 33. Rollback Failure Design

**Find Rollback Failure Design:** failure after reserve/debit/approve leaves partial state.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker gains resource/credit or blocks object.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 34. Idempotency Missing

**Find Idempotency Missing:** retry payment/refund/order without idempotency.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** duplicate processing occurs.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 35. Rate Limit as Design Control

**Find Rate Limit as Design Control:** high-value action lacks abuse-resistance by design.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** small proof shows practical automation path.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 36. Anti-Automation Gap

**Find Anti-Automation Gap:** ticket/promo/signup/vote flow lacks bot/fairness controls.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** automation defeats business fairness with low effort.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 37. Upload Processing Trust

**Find Upload Processing Trust:** uploaded file processed with privileged service or active content allowed.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** user data influences higher-privileged processor.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 38. Plausibility Check Missing

**Find Plausibility Check Missing:** impossible time/location/amount/identity accepted.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** domain model accepts harmful impossible state.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

## 39. Reportability Filter

**Find Reportability Filter:** tie design flaw to money, account, data integrity, quota, inventory, or tenant impact.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** finding is business impact, not only “weird behavior”.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** define invariants server-side, enforce state machines, use transactions/locks/idempotency, revalidate at commit, and add abuse-case tests.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai business invariant and workflow state
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
→ weird state with no sensitive or business impact

Medium:
→ limited quota/discount/workflow bypass on own account

High:
→ unauthorized refund/credit, inventory abuse, self-approval, tenant data integrity issue

Critical:
→ account takeover by recovery design
→ payment/withdrawal abuse
→ mass business impact
→ cross-tenant compromise by design
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A06 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ intended business rule/invariant
→ normal baseline flow
→ abnormal sequence/value/state/actor used
→ before/after state on tester-owned resource
→ business impact: money, account, quota, inventory, tenant, integrity
→ confirmation no real user or production financial harm
```

**Jangan hanya laporkan:**

```text
→ claiming design flaw without stating expected invariant
→ real purchases/refunds/spam without permission
→ load testing anti-automation
→ edge behavior with no impact
```

---

## Retest Checklist

```text
Retest after fix:
→ invariants documented and enforced server-side
→ state transitions validate actor/object/tenant/amount/prior state
→ one-time actions idempotent and locked
→ race-safe transaction and pre-commit check
→ stale tokens expire and bind actor/object/state
→ client trust values ignored or rederived
→ async/webhook jobs revalidate state at execution
```

---

# Real-World Bug Bounty Insight Appendix

## A. Coupon + Race Gives Extra Credit

**Pattern:** one-time coupon redemption has no atomic lock.

```text
Find:
→ create tester coupon/order
→ send two redemptions safely
→ show duplicate credit on own account
```

**Lesson:** Business invariant must be enforced transactionally.

---

## B. Self-Approval in Finance Flow

**Pattern:** same user submits and approves refund through alternate endpoint.

```text
Find:
→ map normal two-person flow
→ replay approve as requester
→ show refund status changed
```

**Lesson:** Authorization can be technically present while design misses separation of duties.

---

## C. Stale Checkout Price

**Pattern:** price captured at draft creation and not revalidated at payment.

```text
Find:
→ create draft at price A
→ change product/plan state
→ complete old draft
→ show charged/entitled mismatch
```

**Lesson:** Critical business data must be revalidated at commit.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A06 harus membaca aplikasi sebagai state machine dengan invariant bisnis yang bisa diuji aman.

## Recent Bypass Branches

- **Hidden sub-state race:** cari state sementara di checkout, refund, reset password, account linking, subscription, invite, file processing, webhook consume, dan approval. Valid bila state sementara bisa dipakai sebelum rollback/final policy.
- **Multi-endpoint race:** endpoint A membuat state, endpoint B memakai state, endpoint C membatalkan atau mengubah owner/role. Gunakan jumlah request rendah dan akun tester.
- **Business invariant testing:** tulis aturan yang tidak boleh dilanggar: satu kupon sekali, saldo tidak negatif, user tidak self-approve, MFA wajib sebelum app, email change butuh konfirmasi, quota tidak reset manual.
- **Deferred worker design:** cek apakah worker menggunakan role/tenant/object state lama saat job diproses belakangan.
- **Fix bypass:** jika satu step difix, coba step reorder, stale draft, mobile endpoint, API v1, webhook event, and idempotency key reuse.

## Evidence Upgrade

Report kuat memakai timeline: request ID, waktu, state sebelum/sesudah, invariant yang dilanggar, dan dampak bisnis dengan data tester. Jangan load test; jelaskan bahwa race window terbukti dari state transition minimal.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **Notes funnel as design review:** pisahkan scope, credentials, behavior, tech stack, risks, high-signal endpoints, error oracles, attack paths, dan tracker.
- **Consent design mismatch:** jika UI/consent menjanjikan satu permission tapi backend memberi lebih, treat sebagai design flaw yang bisa chain ke A01/A07.
- **AI feature design:** agent yang punya akses data user harus punya boundary eksplisit terhadap rendered content, tool output, connector, and delegated token.
- **Live-hacking hit list:** buat daftar target high-signal sebelum test: new feature, acquisition asset, auth flow, billing, import/export, SDK, and admin/support workflow.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Real-risk severity:** jelaskan uang, akun, data, tenant, anti-abuse, atau operational impact; jangan berhenti di label CVSS.
- **Simulated UI trust:** fake dashboard/order/support flow menunjukkan kebutuhan desain verifikasi official channel dan anti-impersonation.
- **Platform validation design:** backend tidak boleh percaya platform/client claim tanpa server-side binding ke session, attestation, role, dan tenant.

## TegalSec Business Logic Error Playbook

Gunakan playbook ini untuk menurunkan case TegalSec menjadi test A06 yang aman:

```text
1. Tulis invariant: "harga tidak bisa dikontrol client", "withdraw hanya ke rekening approved", "platform iOS tidak boleh memakai entitlement Android", "support resmi harus terverifikasi".
2. Identifikasi value yang dikontrol client: harga, rekening, platform, status paid, isPro, email target, deep link action, support instruction.
3. Cari decision point backend: checkout commit, withdraw submit, monitor email add/read, mobile API gateway, support verification, AI/search answer.
4. Jalankan request dengan akun/data tester dan side effect minimal.
5. Buktikan before/after business state, bukan hanya response `200`.
6. Retest alternate surface: UI, raw API, mobile, old version, hidden form, worker, and support flow.
```

**High-signal cases dari TegalSec:**

- **Parameter harga:** server menerima harga client → invariant gagal: price harus dihitung server saat checkout/payment commit.
- **Hidden withdraw/add-bank form:** UI menyembunyikan action → invariant gagal: role/state harus dicek server-side.
- **Cross-platform API reuse:** backend tidak memvalidasi platform/app identity → invariant gagal: capability harus terikat session dan trusted client context.
- **Local `isPro`/entitlement:** client/local DB mengubah status → invariant gagal: entitlement harus berasal dari server.
- **Fake support/fake order/simulated UI:** user trust diarahkan ke channel palsu → invariant gagal: official action dan payment instruction harus dapat diverifikasi.
- **Persistent secret:** secret dihapus dari repo tapi masih aktif → invariant gagal: remediation harus rotate, revoke, audit, dan cari reuse.

## Non-TegalSec Business Logic Error Playbook

Gunakan file [`non_tegalsec_business_logic_inventory_2023_2026.md`](./non_tegalsec_business_logic_inventory_2023_2026.md) untuk pola selain TegalSec. High-signal invariant:

- **GraphQL alternate workflow:** mutation/query tidak boleh punya policy lebih lemah daripada REST/UI.
- **OAuth/MCP delegated authority:** redirect, state, PKCE, consent scope, tool connector, dan token audience harus bind ke user/client/action yang benar.
- **Race/state-machine:** one-time action, approval, entitlement, ownership, payment, dan recovery harus atomic dan idempotent.
- **Cache/ETag state:** cache validator tidak boleh membocorkan login state, object existence, tenant data, atau private workflow.
- **AI/agent action boundary:** rendered content/tool output tidak boleh menjadi instruction yang memakai delegated token tanpa user intent.
- **SDK/API downgrade:** SDK wrapper, legacy API, JSONP, method rewrite, dan archived endpoint harus enforce policy yang sama dengan surface baru.
- **Acquisition/supply-chain lifecycle:** newly acquired asset, orphaned commit, package identity, dan CI/CD artifact harus masuk governance sebelum dipercaya.

```text
Invariant →
alternate surface →
state before →
action with tester data →
state after →
business impact →
fix coverage across UI/API/mobile/SDK/worker/cache/AI.
```

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A06 Insecure Design: https://owasp.org/Top10/2025/A06_2025-Insecure_Design/
- PortSwigger Business logic vulnerabilities: https://portswigger.net/web-security/logic-flaws
- PortSwigger Race conditions: https://portswigger.net/web-security/race-conditions
- OWASP ASVS: https://github.com/OWASP/ASVS
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
