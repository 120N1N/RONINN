# OWASP A01:2025 Broken Access Control — Methodology v3 Advanced Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian yang sah. Fokus dokumen ini adalah membangun alur pikir testing, validasi impact, dan pelaporan yang kuat, bukan menyerang sistem tanpa izin.

## Ringkasan Revisi v3

Versi ini meningkatkan metodologi A01 dengan insight dari praktik bug bounty, OWASP Top 10:2025, PortSwigger Web Security Academy, Intigriti, HackerOne, dan pendekatan code/route mapping ala bug bounty modern. Tambahan paling penting adalah:

- **Route-to-policy matrix** untuk memaksa setiap endpoint dipetakan ke subject, object, action, role, tenant, state, dan trust boundary.
- **HTTP Parameter Pollution dan parser confusion** ketika middleware authorization membaca satu nilai, tetapi handler bisnis memakai nilai lain.
- **Static keyword alias bypass** seperti `me`, `my`, `current`, `self`, `default`, atau `active` yang bisa diganti menjadi ID eksplisit tenant/user lain.
- **Cross-tenant object binding** untuk parent-child mismatch, workspace/org/project boundary, dan object global resolver.
- **Proxy/backend parser mismatch** pada path normalization, suffix, case, trailing slash, override header, dan method override.
- **SSRF-as-access-boundary** karena OWASP Top 10:2025 memasukkan SSRF ke A01 ketika server dapat dipakai melewati boundary akses.
- **Header bypass dan method mismatch** sebagai cabang khusus setelah `403/404`.
- **Conditional/cache header bypass** seperti `If-Modified-Since`, `If-None-Match`, dan stale cache behavior.
- **HMAC-versus-cookie enforcement mismatch** pada metadata/signature validation.
- **Race condition + IDOR** untuk workflow top-up, voucher, subscription, dan ownership transfer.
- **POC-to-report checklist** agar temuan A01 tidak berhenti sebagai teori, tetapi punya bukti confidentiality, integrity, atau availability impact.
- **Contoh real-world pattern** dari bug bounty: user low-privilege dapat memicu action high-privilege, IDOR pada object user lain, dan bypass enforcement berbasis header atau method.

---

## Core Rule A01

**Authentication** menjawab: siapa user ini?

**Authorization** menjawab: apakah user ini boleh melakukan action tertentu pada object tertentu dalam state tertentu?

A01 valid bila user, service, tenant, atau workflow bisa melakukan **read, create, update, delete, export, approve, execute, share, invite, bill, refund, top-up, revoke, atau administer** di luar policy yang seharusnya.

---

## Attack Surface Mapping

Sebelum mencari payload, buat peta akses. A01 jarang ditemukan dari satu request acak; biasanya muncul ketika policy yang benar dibandingkan dengan implementasi nyata.

```text
Mapping minimal:
→ subject: anonymous, user, admin, service account, integration, worker, support, finance
→ object: user, org, tenant, workspace, project, file, invoice, order, token, API key, webhook, job
→ action: read, create, update, delete, export, approve, execute, invite, share, refund, revoke
→ role/scope: owner, admin, manager, member, viewer, external collaborator, suspended user
→ ownership: creator, owner, assignee, billing owner, delegated admin, inherited permission
→ tenant boundary: org_id, workspace_id, team_id, account_id, project_id, region, environment
→ object state: draft, pending, approved, archived, deleted, restored, expired, locked, transferred
→ request surface: path, query, body, header, cookie, multipart field, GraphQL variable, websocket message
→ trust boundary: browser, API gateway, reverse proxy, backend service, queue worker, CDN, object storage
```

**Route-to-policy matrix:**

| Route/Action | Expected actor | Object binding | Tenant binding | State rule | Alternate surfaces |
|---|---|---|---|---|---|
| `GET /api/projects/{id}` | project member | `project.id` | `project.tenant_id` | active/archived allowed? | export, search, GraphQL |
| `PATCH /api/users/{id}/role` | org owner/admin | target user | same org | target not owner? | bulk, invite, admin API |
| `POST /api/refunds` | finance/admin | order/refund | merchant/org | paid and refundable | async job, webhook |

Jika satu route tidak bisa dijelaskan dengan matrix ini, route tersebut adalah kandidat testing A01.

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Core authorization | 1–6 | Role, privilege, IDOR |
| Endpoint/API enforcement | 7–13 | Method, API, frontend, force browsing |
| Metadata/session | 14–17 | JWT, cookie, HMAC, replay |
| Cross-origin/request abuse | 18–21 | CORS, CSRF, redirect, confused deputy |
| Files/resources | 22–29 | Path, storage, listing, ownership |
| Data exposure | 30–33 | Response, export, GraphQL, overexposure |
| Advanced real-world | 34–40 | Race, cache, second-order, headers |
| Cloud/service boundary | 41–43 | SSRF, dangerous function, internal proxy |
| Advanced bug bounty branches | Appendix G–M | HPP, static alias, route matrix, parser mismatch |
| Reporting & triage | 44–46 | Severity, evidence, retest |

---

## Universal Testing Logic

```text
Find A01:
pahami policy akses yang benar →
mapping subject, object, action, role, tenant, ownership, state, workflow, dan trust boundary →
buat baseline dari user berhak dan user tidak berhak →
ubah satu variabel akses pada satu waktu →
uji read/write/delete/export/execute/approve/share/invite/bill/refund/top-up/revoke/administer →
jika unauthorized action berhasil, valid.

Jika gagal:
jangan langsung simpulkan aman.
Turunkan ke decision tree status code, request shape, endpoint alternatif, method, header, cache, object state, dan side effect.
```

---

## Decision Tree

### Jika respons `401`

```text
401 berarti identitas tidak valid atau tidak ada.
Cek:
→ apakah session/token benar-benar expired
→ apakah endpoint alternatif tidak butuh auth
→ apakah file/export/static resource tetap terbuka
→ apakah direct download link tetap hidup
→ apakah remember-me token masih valid
→ apakah websocket/gRPC/API key tetap aktif
→ apakah token lama masih bisa dipakai setelah logout/password change
```

### Jika respons `403`

```text
403 berarti server mengklaim ada authorization check.
Jangan berhenti.

Cek:
→ role
→ ownership
→ tenant
→ object state
→ workflow step
→ method berbeda: GET, POST, PUT, PATCH, DELETE, OPTIONS
→ method override: X-HTTP-Method-Override
→ URL override: X-Original-URL, X-Rewrite-URL
→ host/proxy header: X-Forwarded-Host, X-Forwarded-For
→ conditional/cache header: If-Modified-Since, If-None-Match
→ content-type: JSON, form-urlencoded, multipart
→ Accept header: HTML vs JSON
→ endpoint versi lama/mobile/bulk/export/import
→ GraphQL mutation/query alternatif
→ apakah 403 dari frontend/proxy, bukan backend final
→ apakah response gagal tapi side effect tetap terjadi
```

### Jika respons `404`

```text
404 bisa berarti object tidak ada, atau access denied dimasking.
Jangan langsung simpulkan aman.

Cek:
→ akses object yang sama dari akun owner
→ apakah 404 masking policy
→ format ID: numeric, UUID, hash, slug, encoded, base64-like
→ ID di path/query/body/header/cookie/multipart/GraphQL variable
→ child resource: attachment, invoice, comment, export, audit log
→ parent-child mismatch: tenant_id A + object_id B
→ endpoint list/search/export/autocomplete
→ API v1/v2/mobile/internal
→ trailing slash, case sensitivity, suffix, extension, locale prefix
```

### Jika respons `302`

```text
302 bisa hanya redirect browser flow.
Cek:
→ API response asli dengan Accept: application/json
→ apakah redirect body tetap mengandung data
→ apakah redirect membawa token/code/return_url
→ apakah open redirect bisa mengubah flow auth
→ apakah API tetap memproses action sebelum redirect
```

### Jika respons `200/204` kosong

```text
Jangan hanya lihat response body.
Cek side effect:
→ data berubah
→ file terhapus
→ invite terkirim
→ email/webhook terkirim
→ role/status/ownership berubah
→ voucher/top-up/refund diproses
→ job async dibuat
→ audit log/job status menunjukkan action jalan
```

### Jika UI menolak

```text
UI bukan access control.
Cek:
→ request valid dari akun privileged
→ replay dengan akun low-privilege
→ API langsung
→ JS bundle/source map
→ GraphQL schema
→ mobile API
→ admin route hidden
→ feature flag response
```

---

# Bypass & Chaining Workflow

> Bypass di bagian ini berarti variasi pengujian untuk aset in-scope ketika kontrol terlihat aman. Jangan gunakan untuk memaksa akses di luar izin program; cukup buktikan dengan akun/data tester, response redacted, dan side effect non-destruktif.

## A01 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| `403` pada endpoint utama | method lain, `X-HTTP-Method-Override`, `X-Original-URL`, `X-Rewrite-URL`, trailing slash, case, suffix, `Accept: application/json` | cek proxy/router/frontend deny tetapi backend final tetap memproses |
| `404` pada object orang lain | bandingkan owner vs non-owner, child resource, export/download, list/search/autocomplete, GraphQL `node`, mobile/API v1 | cek 404 masking atau alternate resolver yang tidak enforce ownership |
| UI menyembunyikan menu | ambil request dari role berhak, replay role rendah, cek JS bundle/source map/feature flag/API docs | validasi frontend-only access control |
| IDOR ditolak | parent-child mismatch, alias `me/current/self`, duplicate param, ID di body/header/cookie, batch endpoint | cari resolver yang memakai binding object berbeda |
| Tenant check terlihat aman | `tenant_id` A + object B, workspace/project mismatch, global ID, export/search index, webhook/job ID | cek cross-tenant object binding |
| Role check terlihat aman | request admin alternatif, bulk action, invite/role workflow, support/finance API, old API | cari vertical escalation via surface lain |
| Signature/HMAC menolak | bandingkan missing vs invalid signature, body berubah tanpa signature, GET/OPTIONS/PATCH enforcement, fallback cookie | cek fail-open atau enforcement tidak konsisten |
| Token lama ditolak | refresh token, remember-me, websocket, signed URL, mobile session, API key | cek lifecycle gap setelah logout/revoke/password change |
| Response kosong | audit log, email/webhook, job status, object state, notification, billing/refund status | cek side effect walau body tidak menampilkan data |
| Cache/conditional aman | `ETag`, `If-None-Match`, `If-Modified-Since`, service worker, CDN Vary, stale response | cek authorization sebelum `304` dan cache key identity |

## A01 Chaining Playbook

```text
Info leak / JS route / docs →
temukan endpoint hidden →
replay dengan role rendah →
IDOR/BAC kecil →
child resource/export/search →
PII/token/billing/API key exposure →
account/tenant/business impact.

Frontend-only deny →
API replay →
bulk/import/export alternate path →
state change unauthorized →
audit evidence + before/after object state.

SSRF/internal proxy →
server bertindak sebagai actor lebih berhak →
internal function/service-to-service action →
tenant/admin/data boundary impact.

Race/TOCTOU →
authorization lolos pada check awal →
ownership/state berubah sebelum commit →
action terjadi pada object yang tidak lagi authorized.
```

**Rule chaining:** setiap step harus punya bukti sendiri. Jangan laporkan chain panjang bila step pertama belum valid secara aman.

---

# Methodology Patterns

## 1. Violation of Least Privilege / Deny-by-Default Failure

**Find Least Privilege Violation:** petakan role, permission, action, object, dan tenant → akses fungsi privileged dengan role lebih rendah → jika user biasa bisa menjalankan fungsi admin, manager, owner, finance, support, atau operator, maka valid.

**Jika 403/404:**

```text
→ cek endpoint alternatif
→ cek method lain
→ cek bulk action
→ cek API lama
→ cek frontend-only restriction
→ cek workflow step yang memanggil action sama
```

**Impact:** High–Critical bila mengubah konfigurasi, role, billing, payment, atau data user lain.

---

## 2. Parameter Tampering / User-Controlled Authorization Parameter

**Find Parameter Tampering:** cari parameter yang menentukan `role`, `permission`, `status`, `tenant_id`, `account_id`, `is_admin`, `price`, `quota`, `visibility`, atau `owner` → ubah nilai dalam request valid → jika server menerima nilai yang user tidak boleh kontrol, valid.

**Jika ditolak:**

```text
→ cek nested JSON
→ cek duplicate parameter
→ cek array/object injection
→ cek body vs query vs header
→ cek content-type berbeda
→ cek field yang hanya muncul pada request admin
→ cek parameter role_id, permissions[], scopes[], entitlements[]
```

**Real-world lesson:** banyak bug privilege escalation sederhana terjadi karena endpoint menerima `role=admin` atau `role_id` dari client tanpa server-side authorization.

---

## 3. IDOR / Insecure Direct Object Reference

**Find IDOR:** buat dua akun A dan B → ambil object milik B → akses object B dengan session A → uji read, update, delete, export, download, share, comment, dan approve → jika A bisa mengakses resource B, valid.

**Jika 403/404:**

```text
→ cek format ID: numeric, UUID, hash, slug, encoded
→ cek ID di path/query/body/header/cookie
→ cek parent_id dan child_id mismatch
→ cek nested route
→ cek attachment/download/export endpoint
→ cek list/search/autocomplete
→ cek GraphQL node/global ID resolver
→ cek mobile/API v1
```

**Valid bila:** data B terbaca, termodifikasi, terhapus, diekspor, atau dipakai untuk action oleh A.

---

## 4. Horizontal Privilege Escalation

**Find Horizontal Privilege Escalation:** dua user dengan role sama tapi ownership berbeda → akses resource user B memakai session user A → jika user A bisa membaca atau mengubah object B, valid.

**Jika blocked:**

```text
→ cek child resource
→ cek export
→ cek comment
→ cek attachment
→ cek audit log
→ cek notification
→ cek bulk operation
```

**Catatan:** role sama bukan berarti object sharing boleh. Ownership tetap harus dicek.

---

## 5. Vertical Privilege Escalation

**Find Vertical Privilege Escalation:** mapping fitur admin/owner/manager/support/finance → akses dengan role rendah → jika role rendah bisa menjalankan action role tinggi, valid.

**Jika 403:**

```text
→ cek endpoint admin alternatif
→ cek hidden route dari JS
→ cek GraphQL mutation
→ cek bulk endpoint
→ cek import/export
→ cek parameter role/status
→ cek HMAC/signature fallback
```

**Bug bounty lesson:** UI role hierarchy seperti staff → manager → owner harus diuji pada API, bukan hanya dilihat dari menu.

---

## 6. Horizontal-to-Vertical Privilege Escalation

**Find H2V Escalation:** mulai dari akses horizontal kecil → cari apakah object yang diambil bisa digunakan untuk action privileged → jika akses resource user lain membuka token, invite, role, billing, atau admin workflow, valid.

**Jika impact belum jelas:**

```text
→ cari chaining ke reset password
→ cari chaining ke invite/role
→ cari chaining ke payment/billing
→ cari chaining ke OAuth/SSO linking
→ cari chaining ke API key/export
```

---

## 7. Missing Authorization

**Find Missing Authorization:** cari endpoint yang hanya mengecek login, bukan permission → uji user authenticated tanpa hak → jika action berhasil, valid.

**Jika endpoint utama aman:**

```text
→ cek endpoint lain dengan fungsi sama
→ cek method lain
→ cek bulk/import/export
→ cek async job
→ cek API v1/mobile
→ cek GraphQL mutation
```

**Root rule:** setiap request harus punya authorization check. Satu endpoint lolos sudah cukup untuk valid.

---

## 8. Missing API Authorization pada POST/PUT/PATCH/DELETE

**Find Method-Based BAC:** petakan method di endpoint sama → cek apakah GET dilindungi tapi POST/PUT/PATCH/DELETE longgar → jika state-changing action berhasil tanpa izin, valid.

**Jika method utama 403:**

```text
→ cek PUT vs PATCH
→ cek DELETE vs status=deleted
→ cek archive endpoint
→ cek restore endpoint
→ cek batch endpoint
→ cek X-HTTP-Method-Override
```

---

## 9. Frontend-Only Access Control

**Find Frontend-Only Authorization:** baca JS, route guard, feature flag, disabled button, dan menu logic → ambil request dari role privileged → replay dengan role rendah → jika backend memproses, valid.

**Jika tombol/menu tidak muncul:**

```text
→ cari endpoint dari Network tab akun privileged
→ cari source map
→ cari API docs/schema
→ cari mobile API
→ cari GraphQL operation
→ replay request dengan session rendah
```

**Cross-reference:** ini biasanya manifestasi dari Missing Authorization.

---

## 10. Force Browsing / Direct Access Hidden URL

**Find Force Browsing:** kumpulkan route dari JS, robots, sitemap, source map, OpenAPI, GraphQL schema, mobile app, atau URL lama → akses langsung dengan role rendah atau tanpa login → jika resource privileged terbuka, valid.

**Jika 403/404:**

```text
→ cek trailing slash
→ cek case sensitivity
→ cek extension/suffix
→ cek locale prefix
→ cek API version
→ cek staging/internal path
→ cek header override
```

---

## 11. Unauthenticated Access

**Find Unauthenticated Access:** akses resource private tanpa session, setelah logout, dengan token invalid, atau token expired → jika data/aksi private tetap bisa dilakukan, valid.

**Jika redirect login:**

```text
→ cek API JSON
→ cek direct download
→ cek CDN cached file
→ cek export URL
→ cek websocket/gRPC
→ cek old signed URL
```

---

## 12. Incorrect Authorization

**Find Incorrect Authorization:** buat permission matrix berdasarkan role, object, tenant, state, dan action → bandingkan expected vs actual → jika rule salah, inheritance salah, atau state salah, valid.

**Jika normal state aman:**

```text
→ cek archived state
→ cek pending invite
→ cek suspended user
→ cek deleted/restored object
→ cek expired subscription
→ cek multi-role user
→ cek tenant admin A vs tenant B
```

---

## 13. Authorization Bypass Through User-Controlled Key

**Find Key-Based Bypass:** cari key seperti `user_id`, `account_id`, `org_id`, `tenant_id`, `email`, `username`, `invoice_id`, `team_id` → ubah key milik user lain → jika server mengikuti key tanpa binding ke session, valid.

**Jika blocked:**

```text
→ cek key di body
→ cek key di header
→ cek key di cookie
→ cek duplicate key
→ cek parent-child mismatch
→ cek GraphQL variable
```

---

## 14. JWT / Cookie / Hidden Field / Metadata Manipulation

**Fokus:** apakah server percaya metadata client-side untuk privilege?

**Find Metadata Manipulation:** identifikasi claim/field `role`, `scope`, `is_admin`, `tenant_id`, `plan`, `entitlement`, `org_id` → cek apakah server memverifikasi integritas dan policy server-side → jika privilege naik karena metadata client-side, valid.

**Jika manipulasi JWT gagal:**

```text
→ cek role juga dikirim di body
→ cek tenant_id di header
→ cek org_id di cookie
→ cek hidden field
→ cek localStorage/sessionStorage gating
→ cek refresh-token flow
→ cek backend decode tanpa verify
```

---

## 15. HMAC-vs-Cookie / Missing Signature Verification Fallback

**Find Signature Fallback BAC:** cari endpoint yang memakai session cookie **dan** header signature/HMAC/API-key/internal header → hapus atau ubah header signature dalam request yang valid → amati apakah server tetap memproses berdasarkan cookie saja → jika action privileged tetap berjalan tanpa signature yang seharusnya wajib, valid.

**Jika 403:**

```text
→ cek apakah header signature hanya dicek pada route tertentu
→ cek apakah OPTIONS/GET/PATCH punya enforcement berbeda
→ cek apakah proxy menambahkan header internal
→ cek apakah missing header membuat fallback ke session
→ cek apakah invalid signature beda perilaku dengan no signature
→ cek apakah body berubah tapi signature tidak ikut divalidasi
```

**Valid bila:** signature/HMAC yang semestinya menjadi mandatory proof dapat dihilangkan, dipalsukan, atau tidak divalidasi konsisten, sehingga user biasa menjalankan action privileged.

**Mitigation angle:** fail closed bila signature hilang/invalid; signature harus mengikat method, path, body hash, timestamp, tenant, dan user/session.

---

## 16. JWT Invalidation / Token Replay / Session Lifecycle Failure

**Find Token Replay:** login → simpan token/session → logout, reset password, downgrade role, remove user dari org, revoke device → gunakan token lama → jika token lama masih bisa akses resource sensitif melewati policy, valid.

**Jika access token mati:**

```text
→ cek refresh token
→ cek remember-me token
→ cek API key
→ cek websocket session
→ cek signed URL
→ cek mobile session
```

---

## 17. Sensitive Cookie SameSite / Cookie Scope Access Control Weakness

**Find Cookie Scope Weakness:** identifikasi cookie session/state → cek `Domain`, `Path`, `SameSite`, `Secure`, `HttpOnly` → jika cookie terlalu luas membuat subdomain atau cross-site flow bisa memicu state-changing action tanpa proteksi, valid bila impact terbukti.

**Jika tidak langsung valid:**

```text
→ cek CSRF chain
→ cek subdomain takeover chain
→ cek SameSite=None + credentialed request
→ cek action tanpa CSRF token
```

---

## 18. CORS Misconfiguration

**Find CORS BAC:** cari API sensitif berbasis browser session → cek apakah origin tidak tepercaya bisa membaca response authenticated → jika data sensitif bisa dibaca oleh origin asing, valid.

**Jika hanya header terlihat longgar:**

```text
→ cek Access-Control-Allow-Credentials
→ cek wildcard vs reflected origin
→ cek cookie SameSite
→ cek preflight
→ cek endpoint sensitif
→ cek response benar-benar readable
```

---

## 19. CSRF

**Find CSRF:** cari action state-changing berbasis cookie/session → cek anti-CSRF token, Origin/Referer validation, SameSite, dan re-auth → jika action berhasil dari origin eksternal tanpa consent valid, valid.

**Jika POST JSON gagal:**

```text
→ cek form-urlencoded
→ cek multipart
→ cek GET-like state change
→ cek endpoint lama
→ cek toggle/disable/delete ringan
```

---

## 20. Open Redirect in Authorization Flow

**Find Open Redirect BAC:** cari `next`, `return`, `redirect`, `callback`, `redirect_uri`, `continue`, `url` → cek apakah redirect eksternal terjadi pada login, OAuth, reset password, invite, atau payment flow → valid bila trust boundary berubah atau token/code bocor.

**Jika domain luar ditolak:**

```text
→ cek relative URL
→ cek encoded URL
→ cek scheme-relative URL
→ cek trusted-domain nested redirect
→ cek parsing difference
```

---

## 21. Confused Deputy

**Find Confused Deputy:** cari fitur yang membuat aplikasi/service bertindak atas nama user: webhook, import URL, OAuth connector, automation, proxy, integration → jika user low-privilege membuat sistem high-privilege melakukan action, valid.

**Jika user action langsung ditolak:**

```text
→ cek automation action
→ cek webhook-triggered action
→ cek service account execution
→ cek connector ownership
→ cek delegated permission
```

---

## 22. Path Traversal / File Access Outside Boundary

**Find Path Traversal:** cari fitur download/preview/import/export/template yang menerima path/nama file → valid bila user bisa membaca/menulis file di luar direktori atau object boundary yang diizinkan.

**Jika blocked:**

```text
→ cek encoding
→ cek normalization
→ cek preview vs download
→ cek file ID resolver
→ cek archive extraction
→ cek symlink
```

---

## 23. Symlink / Hardlink / Improper Link Resolution

**Find Link Resolution Issue:** cari upload/extract/backup/import/file processing → analisis apakah symlink/hardlink menuju resource di luar boundary diproses → jika target luar terbaca/tertulis, valid.

**Jika upload aman:**

```text
→ cek extract flow
→ cek async processing
→ cek preview
→ cek restore/import
→ cek validation sebelum final path resolve
```

---

## 24. Public File / Backup / Web Root Exposure

**Find Public File Exposure:** cari backup, log, export, temp, source map, `.git`, config, report, invoice, upload → jika file private bisa diakses tanpa authorization, valid.

**Jika listing tidak ada:**

```text
→ cek direct URL
→ cek predictable filename
→ cek CDN cache
→ cek source map reference
→ cek old export link
```

---

## 25. Directory Listing

**Find Directory Listing:** akses folder upload/backup/media/export/temp → jika daftar file sensitif terlihat, valid.

**Jika listing disabled:**

```text
→ cek subfolder
→ cek bucket listing
→ cek CDN origin
→ cek staging static host
→ cek folder dari JS bundle
```

---

## 26. Files/Directories Accessible to External Parties

**Find External File Access:** akses attachment, invoice, report, export, generated PDF tanpa session atau dengan user lain → jika URL saja cukup, valid.

**Jika signed URL:**

```text
→ cek expiry
→ cek binding ke user/session
→ cek revocation setelah logout/remove access
→ cek CDN cache
→ cek permission dicabut tapi URL masih hidup
```

---

## 27. Incorrect Default Permissions

**Find Default Permission Failure:** buat resource baru → cek default visibility, sharing, invite, export, API access → jika default terlalu luas, valid.

**Jika UI aman:**

```text
→ cek API create
→ cek clone/copy
→ cek import template
→ cek inherited permission
→ cek public link default
```

---

## 28. Improper Ownership Management / Unverified Ownership

**Find Ownership Failure:** cari action owner-only seperti edit profile, delete file, manage team, cancel order, change billing, approve request, transfer ownership → lakukan sebagai non-owner → jika berhasil, valid.

**Jika endpoint utama aman:**

```text
→ cek child object
→ cek transfer flow
→ cek delegated admin
→ cek bulk operation
→ cek parent/object mismatch
```

---

## 29. Exposed Dangerous Method or Function

**Find Dangerous Function Exposure:** cari debug, impersonation, cache purge, job trigger, test email, internal report, maintenance action → akses dengan role tidak sah → jika fungsi berjalan, valid.

**Jika route utama 403:**

```text
→ cek internal route exposed
→ cek API v1
→ cek method lain
→ cek staging route
→ cek feature flag
```

---

## 30. Sensitive Information Exposure to Unauthorized Actor

**Find Unauthorized Sensitive Exposure:** akses PII, token, invoice, email, address, internal note, audit log, config, metadata dari role/user tidak berhak → jika data terlihat, valid.

**Jika UI aman:**

```text
→ cek raw JSON
→ cek export
→ cek search
→ cek autocomplete
→ cek notification
→ cek webhook payload
→ cek GraphQL field
```

---

## 31. Sensitive Information Through Sent Data

**Find Sensitive Data in Response:** cek response mentah, HTML source, preloaded state, hidden field, localStorage, GraphQL, mobile API, export → jika field sensitif dikirim ke user yang tidak berhak/butuh, valid.

**Jika tidak terlihat di UI:**

```text
→ cek JSON raw
→ cek preloaded state
→ cek hidden input
→ cek GraphQL nested object
→ cek export CSV/PDF
```

---

## 32. GraphQL Field-Level / Object-Level Authorization Failure

**Find GraphQL BAC:** identifikasi query/mutation yang menerima ID, global ID, node resolver, nested relation, atau field sensitif → uji akun A mengakses object/field akun B → jika resolver mengembalikan data/aksi unauthorized, valid.

**Jika query utama blocked:**

```text
→ cek nested relation
→ cek alias
→ cek fragments
→ cek node/nodes resolver
→ cek mutation response
→ cek list/search/filter
→ cek batch query
```

**Note:** GraphQL sering gagal bukan karena endpoint `/graphql` terbuka, tetapi karena field/resolver tidak enforce authorization per object.

---

## 33. API Overexposure / List-Search-Export BAC

**Find API Overexposure:** cek endpoint list/search/autocomplete/export/filter/include/expand → jika data lintas user/tenant muncul karena response terlalu luas, valid.

**Jika detail aman:**

```text
→ cek list endpoint
→ cek export
→ cek search
→ cek include=*
→ cek expand=owner,permissions,billing
→ cek pagination/filter tenant
```

---

## 34. Race Condition / TOCTOU Access Control

**Find Access Control Race:** cari workflow yang memisahkan permission/state check dari action execution → uji concurrency aman pada voucher, top-up, refund, withdraw, invite, role change, ownership transfer, one-time token, delete/restore → jika dua action yang seharusnya mutually exclusive sama-sama berhasil, valid.

**Jika single request aman:**

```text
→ cek dua request bersamaan
→ cek dua session akun sama
→ cek role revoked saat request jalan
→ cek approve dan cancel bersamaan
→ cek transfer ownership dan update permission bersamaan
→ cek top-up/voucher/refund double processing
→ cek job async yang memakai state lama
```

**Bug bounty style example:**

```text
User A hanya boleh top-up/voucher/refund satu kali.
Jika request paralel membuat action diproses dua kali, valid.

User A mengganti target resource/nomor/order tepat saat workflow memproses payment.
Jika sistem memproses resource yang bukan hak A, valid.

User A dicabut dari project.
Jika request race tetap bisa update resource setelah removal, valid.
```

**Mitigation angle:** atomic transaction, row-level locking, idempotency key, server-side recheck tepat sebelum commit, dan fail closed pada state mismatch.

---

## 35. Cache-Based Access Control Bypass

**Find Cache BAC:** akses resource privileged sebagai user berhak → cek apakah response tersaji dari browser/CDN/proxy/service worker cache ke user lain, user logout, atau unauthenticated actor → jika data private terbaca dari cache, valid.

**Jika live API 403:**

```text
→ cek cached response
→ cek browser back/history
→ cek CDN edge
→ cek stale response
→ cek missing Vary: Authorization/Cookie
→ cek public cache pada personalized response
```

---

## 36. Second-Order Access Control

**Find Second-Order BAC:** cari data yang bisa diset user low-privilege lalu diproses worker/admin/system/integration dengan privilege lebih tinggi → jika input low-privilege menyebabkan read/write/export/send/execute di luar izin user asal, valid.

**Jika request awal aman:**

```text
→ cek report generator
→ cek webhook
→ cek notification
→ cek search index
→ cek audit log viewer
→ cek billing engine
→ cek approval worker
```

---

## 37. Header and Method Authorization Bypass

**Find Header/Method BAC Bypass:** ketika route admin atau object protected mengembalikan 403, cek apakah enforcement terjadi di proxy/router/frontend sementara backend menerima path/method berbeda → valid bila header/method mismatch membuat backend menjalankan action protected.

**Cek aman dalam scope:**

```text
→ X-Original-URL
→ X-Rewrite-URL
→ X-Forwarded-Host
→ X-Forwarded-For
→ X-HTTP-Method-Override
→ OPTIONS vs POST
→ GET action fallback
→ trailing slash/case/suffix
→ Accept: application/json
```

**Valid bila:** user yang tidak berhak bisa mencapai endpoint/action yang semestinya blocked karena parser proxy dan parser backend tidak konsisten.

**Mitigation angle:** normalize path sebelum authorization, block override headers kecuali trusted proxy, enforce auth di backend final, dan jangan mengandalkan route deny rule di satu layer saja.

---

## 38. Conditional Header / 403 Cache Bypass

**Find Conditional Header BAC:** ketika endpoint protected mengembalikan 403, uji apakah conditional request atau cache metadata mengubah response authorization → valid bila header cache/conditional membuat resource protected tersaji sebagai 200/304/stale response kepada user tidak berhak.

**Cek:**

```text
→ If-Modified-Since
→ If-None-Match
→ ETag reuse
→ Cache-Control mismatch
→ stale-while-revalidate
→ proxy/CDN cache key tidak memasukkan user/session/tenant
→ 304 tanpa authorization ulang
```

**Valid bila:** response sebelumnya dari user berhak bisa dibaca user lain, atau endpoint protected menjadi readable karena conditional/cache behavior salah.

**Mitigation angle:** private resource memakai `Cache-Control: no-store`, authorization tetap dicek sebelum 304, cache key wajib memasukkan identity/tenant bila personalized.

---

## 39. Workflow / Multi-Step Process Authorization Failure

**Find Workflow BAC:** cari proses multi-step seperti checkout, withdrawal, invite, approval, KYC, password reset, email change, transfer ownership → lompat step, ulang step lama, ubah object antar step, atau pakai token step dari user lain → valid bila workflow selesai di luar policy.

**Jika step langsung blocked:**

```text
→ cek token step reuse
→ cek draft object
→ cek pending state
→ cek old approval link
→ cek callback endpoint
→ cek async job
→ cek state transition race
```

---

## 40. Feature Flag / Dark Launch Authorization Failure

**Find Feature Flag BAC:** cari feature flag response, beta endpoint, disabled UI, dark-launch route → panggil API langsung dengan user non-eligible → valid bila feature restricted dapat digunakan.

**Jika UI hidden:**

```text
→ cek JS bundle
→ cek route name
→ cek API request akun eligible
→ replay session non-eligible
→ cek mobile/staging route
```

---

## 41. SSRF as Access Boundary Failure

**Find SSRF BAC:** cari fitur server-side fetch/callback/import/preview/webhook → gunakan endpoint controlled tester untuk membuktikan server membuat request → valid bila server bisa dipakai melewati boundary akses sesuai scope.

**Jika external URL blocked:**

```text
→ cek redirect handling
→ cek allowlist string matching
→ cek protocol restriction
→ cek DNS resolution
→ cek webhook/callback fitur lain
```

**Note:** jangan menyentuh internal target tanpa izin eksplisit.

---

## 42. Confused Internal Proxy / Service-to-Service Access Abuse

**Find Internal Proxy BAC:** cari endpoint yang meneruskan request ke internal service dengan credential backend → jika user bisa membuat backend mengakses service/tenant/action yang user tidak boleh, valid.

**Cek:**

```text
→ proxy endpoint
→ service mesh route
→ internal API gateway
→ tenant header
→ service account scope
→ audit log actor
```

---

## 43. Exposed Internal Dangerous Function

**Find Internal Dangerous Function:** cari route internal yang terpanggil publik karena reverse proxy/gateway rule salah → jika user publik bisa memicu action internal, valid.

**Cek:**

```text
→ /internal/*
→ /admin/*
→ /debug/*
→ /jobs/*
→ /actuator/*
→ /maintenance/*
→ /impersonate/*
```

---

## 44. Severity Heuristic

Gunakan CIA + privilege + blast radius.

```text
Info/Low:
→ public data, no sensitive impact, no state change.

Medium:
→ limited unauthorized read/write pada satu object non-kritis.

High:
→ PII/billing/order/invoice/user data exposure.
→ unauthorized state change.
→ horizontal/vertical privilege escalation terbatas.
→ cache/export/search leak banyak data.

Critical:
→ admin/owner takeover.
→ payment/refund/withdraw/top-up abuse.
→ tenant-wide compromise.
→ arbitrary internal action.
→ mass deletion/export.
→ token/session/API key exposure yang memungkinkan takeover.
```

---

## 45. Bug Bounty POC Evidence Checklist

Agar A01 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ akun A dan akun B
→ role masing-masing
→ resource milik siapa
→ expected policy
→ request valid baseline
→ request unauthorized
→ response atau side effect
→ bukti data/aksi milik actor tidak sah
→ business impact
→ batasan scope aman
```

**Jangan hanya laporkan:**

```text
→ endpoint 403 terlihat longgar tanpa data/action
→ ID terlihat bisa diganti tapi tidak ada resource valid
→ session cookie ditukar antar akun sendiri lalu data berubah sesuai session
→ data memang publik
→ no impact theoretical issue
```

---

## 46. Retest Checklist

```text
Retest after fix:
→ user A tidak bisa access object B
→ role rendah tidak bisa action role tinggi
→ semua method dilindungi
→ bulk/export/search/list ikut dilindungi
→ child resource ikut dilindungi
→ GraphQL field/resolver ikut dilindungi
→ header override tidak bypass
→ conditional/cache tidak bypass
→ token lama/session lama tidak lolos
→ race/concurrency tidak memproses double action
→ audit log menunjukkan deny
```

---

# Real-World Bug Bounty Insight Appendix

## A. Staff-to-Admin Privilege Escalation

**Pattern:** role hierarchy terlihat benar di UI, tetapi endpoint role/status menerima request dari staff.

```text
Find:
mapping role staff, manager, owner →
ambil request role-management dari owner →
replay dengan staff →
ubah target user/self role →
cek apakah role berubah.
```

**Lesson:** UI role guard tidak cukup. Endpoint role change harus memverifikasi actor punya permission untuk mengubah role target.

---

## B. IDOR pada User dan Document Object

**Pattern:** endpoint detail menerima `user_id` atau `doc_id`, tetapi tidak mengecek owner.

```text
Find:
login sebagai Alice →
akses /resource milik Alice →
ganti ID ke resource Bob →
jika response Bob terlihat, valid.
```

**Lesson:** object ID boleh dipakai untuk lookup, tetapi authorization harus membuktikan session user berhak atas object tersebut.

---

## C. Header Override / Method Mismatch

**Pattern:** proxy melarang `/admin/deleteUser`, tetapi backend menerima path override atau method berbeda.

```text
Find:
endpoint protected 403 →
cek method lain →
cek method override →
cek URL override header →
cek trailing slash/case/suffix →
jika backend menjalankan action protected, valid.
```

**Lesson:** authorization harus dilakukan setelah canonicalization dan di backend yang menjalankan action.

---

## D. Conditional Header / 403 Bypass

**Pattern:** endpoint protected menghasilkan 403, tetapi conditional/cache header menyebabkan response lama atau 200/304 salah tersaji.

```text
Find:
akses resource sebagai user berhak →
akses sebagai user tidak berhak →
uji cache/conditional state →
valid bila response protected tersaji tanpa authorization ulang.
```

**Lesson:** cache dan conditional response tetap bagian dari access control.

---

## E. HMAC Header vs Session Cookie

**Pattern:** sistem mengharuskan signature/HMAC, tetapi bila header hilang, backend hanya memakai session cookie.

```text
Find:
ambil request dengan HMAC valid →
hapus HMAC →
ubah body/action →
replay dengan role rendah →
valid bila action tetap diproses.
```

**Lesson:** missing security proof harus fail closed, bukan fallback ke mekanisme lain yang lebih lemah.

---

## F. IDOR + Concurrency

**Pattern:** object ownership/status dicek di awal workflow, tetapi berubah sebelum commit.

```text
Find:
buat dua request hampir bersamaan →
satu mengubah target/status/ownership →
satu memproses action →
valid bila action terjadi pada object yang tidak lagi authorized.
```

**Lesson:** authorization dan state harus dicek ulang tepat sebelum commit dalam transaksi atomic.

---

# Advanced Bug Bounty Branches

## G. Route-to-Policy Matrix Drift

**Pattern:** dokumentasi, UI, atau role matrix mengatakan satu policy, tetapi route tertentu tidak mengikuti policy yang sama.

```text
Find:
buat matrix route → actor → object → tenant → state →
ambil request dari role yang berhak →
replay dengan role tidak berhak →
bandingkan endpoint utama, bulk, export, mobile, GraphQL, dan async job →
valid bila satu surface menjalankan action di luar policy.
```

**Cek khusus:**

```text
→ route yang dibuat belakangan
→ API v1 yang masih hidup
→ endpoint admin yang dipakai UI internal
→ bulk/import/export yang melewati service berbeda
→ worker async yang hanya percaya job payload
→ GraphQL mutation yang reuse resolver lama
```

**Lesson:** policy harus menjadi kontrak backend, bukan asumsi di UI atau dokumentasi.

---

## H. HTTP Parameter Pollution / Duplicate Key Authorization Confusion

**Pattern:** middleware authorization membaca parameter pertama, sedangkan handler bisnis membaca parameter terakhir, array, atau merged object.

```text
Find:
identifikasi parameter authorization seperti user_id/org_id/role/status →
kirim duplicate key dengan nilai authorized dan unauthorized →
uji query, form-urlencoded, JSON nested, multipart, header, dan GraphQL variable →
valid bila authorization mengecek nilai aman tetapi action memakai nilai target lain.
```

**Contoh aman scoped:**

```text
GET /api/invoices?org_id=own_org&org_id=other_org
POST body: {"org_id":"own_org","invoice":{"org_id":"other_org"}}
multipart: org_id=own_org + metadata[org_id]=other_org
```

**Invalid bila:** server konsisten menolak duplicate key, memilih satu nilai yang tetap authorized, atau tidak ada data/action lintas boundary.

---

## I. Static Keyword Alias Replacement

**Pattern:** endpoint memakai alias seperti `me`, `my`, `current`, `self`, `default`, `active`, atau `primary`, lalu backend juga menerima ID eksplisit.

```text
Find:
akses /api/me/projects atau /api/my/workspace →
lihat response untuk ID eksplisit →
ganti alias dengan ID milik akun/tenant lain →
uji read, update, export, share, invite, dan delete →
valid bila alias resolver tidak mengikat ID eksplisit ke session.
```

**Cek:**

```text
→ /users/me → /users/{victim_id}
→ /orgs/current → /orgs/{other_org_id}
→ /workspaces/my/files → /workspaces/{other_workspace_id}/files
→ GraphQL viewer/currentUser/node(id:)
→ mobile endpoint yang memakai current_account_id
```

**Lesson:** alias boleh mempermudah client, tetapi ID eksplisit tetap wajib dicek terhadap subject dan tenant.

---

## J. Cross-Tenant Object Binding Failure

**Pattern:** child object valid, parent object valid, tetapi kombinasi parent A + child B tidak divalidasi sebagai satu graph.

```text
Find:
ambil parent milik A dan child milik B →
gabungkan pada route nested, query, body, atau GraphQL relation →
uji comment, attachment, invoice, member, role, export, audit log →
valid bila child B terbaca/diproses lewat parent A.
```

**Cek:**

```text
→ /orgs/own_org/projects/other_project
→ tenant_id=own_tenant&file_id=other_file
→ project_id milik A + issue_id milik B
→ invoice_id milik merchant lain pada refund endpoint
→ webhook_id milik tenant lain pada retry endpoint
```

**Impact tinggi:** cross-tenant data exposure, billing action, admin mutation, file export, atau workflow approval.

---

## K. Parser / Proxy / Backend Authorization Mismatch

**Pattern:** layer depan melakukan deny berdasarkan URL/method yang belum dicanonicalize sama seperti backend final.

```text
Find:
endpoint protected 403 →
ubah bentuk path tanpa mengubah maksud endpoint →
uji apakah proxy, framework, dan controller melihat route berbeda →
valid bila backend menjalankan action protected.
```

**Cek aman:**

```text
→ trailing slash: /admin/delete/ vs /admin/delete
→ case: /ADMIN/DeleteUser
→ suffix: /admin/delete.json, /admin/delete.anything
→ encoded slash/dot: %2f, %2e
→ duplicate slash: /admin//delete
→ semicolon/path parameter: /admin/delete;anything
→ X-Original-URL, X-Rewrite-URL
→ X-HTTP-Method-Override
```

**Lesson:** authorization harus terjadi setelah canonicalization dan pada backend yang benar-benar menjalankan action.

---

## L. Conditional Cache / 304 Authorization Drift

**Pattern:** user berhak membuat cache validator, lalu user tidak berhak mendapatkan `304`, stale response, atau response cache tanpa authorization ulang.

```text
Find:
akses resource private sebagai owner →
simpan ETag/Last-Modified/cache key →
akses sebagai user lain atau setelah logout dengan conditional header →
cek apakah data private tetap tersaji dari browser/CDN/proxy/service worker →
valid bila identity/tenant tidak menjadi bagian dari cache decision.
```

**Cek:**

```text
→ If-None-Match
→ If-Modified-Since
→ stale-while-revalidate
→ missing Vary: Authorization/Cookie
→ public cache pada response personalized
→ service worker cache setelah logout
```

**Lesson:** `304 Not Modified` tetap keputusan authorization. Private data tidak boleh menjadi public/stale cache.

---

## M. SSRF-as-Access-Boundary Failure

**Pattern:** fitur server-side fetch membuat backend berhak mengakses resource yang user tidak boleh akses langsung.

```text
Find:
cari import URL, webhook test, preview, callback, image fetch, PDF render, integration sync →
pakai endpoint milik tester untuk membuktikan server melakukan request →
uji hanya target yang diizinkan program →
valid bila server-side identity melewati boundary akses yang semestinya melindungi resource.
```

**Cek aman dalam scope:**

```text
→ redirect handling
→ allowlist string matching
→ DNS rebinding policy
→ cloud metadata hanya bila program mengizinkan eksplisit
→ internal admin path hanya bila scope mengizinkan eksplisit
→ service-to-service credential yang muncul di audit log
```

**Lesson:** SSRF menjadi A01 ketika server dipakai sebagai actor yang lebih berhak daripada user asal.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A01 harus dites sebagai masalah coverage policy di semua surface, bukan hanya mengganti `id=123`.

## Recent Bypass Branches

- **GraphQL as alternate channel:** jika REST/UI menolak akses, cari query/mutation yang merepresentasikan object/action sama. Valid bila akun tester non-owner bisa membaca nested field, menjalankan mutation, atau memicu worker yang mengubah object milik akun tester lain.
- **UUID bukan akhir testing:** jika ID sulit ditebak, cari sumber ID sah dari search, notification, email, export, GraphQL node, public profile, shared link, activity feed, atau referensi di mobile API. Report tetap kuat bila ID bisa diperoleh lewat flow normal.
- **Header/body/method tampering:** ulangi matrix dengan `GET/POST/PUT/PATCH/DELETE`, body JSON vs form, duplicate key, method override, route alias, trailing slash, encoded delimiter, dan static alias seperti `me`, `my`, `current`.
- **Parser/cache mismatch:** jika response terlihat benar, cek `304`, `If-None-Match`, cache key, CDN normalized path, dan beda interpretasi proxy/backend. Valid bila private object bisa direuse dari cache atau authorization check hilang pada conditional request.
- **Fix bypass:** setelah program memperbaiki endpoint utama, retest alternate path: mobile API, API v1, bulk export, import preview, webhook callback, background job, dan direct object binding.

## Evidence Upgrade

Gunakan tabel kecil di report:

```text
Actor | Endpoint/surface | Object/tenant | Expected | Actual | Evidence
```

Tambahkan request pembanding owner vs non-owner, screenshot object sebelum/sesudah, dan bukti bahwa data yang terlihat adalah akun tester, bukan pihak ketiga.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **Route/authz review first:** sebelum IDOR test, buat matrix route -> middleware -> policy -> actor -> object -> tenant -> state. Jangan baca handler tanpa tahu policy mana yang seharusnya mengunci route.
- **SDK/API downgrade:** jika UI dan REST utama aman, cek SDK wrapper, API versi lama, method downgrade, JSONP callback, whitelisted-domain gadget, dan referrer-based control.
- **OAuth/AI delegated access:** consent scope atau agent/AI connector dapat membuat actor baru. Validasi apakah action yang dilakukan agent tetap memakai boundary user/tenant yang benar.
- **Old report regression:** buka bug BAC lama, cari varian lewat parser, new client, new acquisition asset, route alias, dan new feature flag.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Business parameter authority:** harga, saldo, withdraw destination, paid status, entitlement, dan monitoring target harus dihitung/diotorisasi server-side, bukan diterima dari client.
- **Hidden frontend control:** jika DOM menyimpan form/action tersembunyi, submit action yang sama dengan akun tester dan pastikan backend menolak role/state yang tidak berhak.
- **Mobile shared backend:** bandingkan request Android/iOS/Flutter; platform berbeda tidak boleh menjadi bypass policy user/tenant/object.
- **IDOR acquisition path:** object ID dari UI monitoring, mobile response, notification, atau list internal tetap valid untuk horizontal access test dengan akun tester.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 — A01 Broken Access Control: https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- PortSwigger Web Security Academy — Access Control: https://portswigger.net/web-security/access-control
- Intigriti — Exploiting Broken Access Control Vulnerabilities: https://www.intigriti.com/researchers/blog/hacking-tools/exploiting-broken-access-control-vulnerabilities
- HackerOne — How To Find Broken Access Control Vulnerabilities in the Wild: https://www.hackerone.com/blog/how-find-broken-access-control-vulnerabilities-wild
- Critical Thinking Bug Bounty Podcast — code review methodology and auth mapping themes: https://blog.criticalthinkingpodcast.io/
- HackerOne public report — MTN Group Broken Access Control Horizontal Privilege Escalation: https://hackerone.com/reports/2319586
- Medium / InfoSec Write-ups — Race Condition & Broken Access Control case study: https://infosecwriteups.com/how-i-found-a-10-800-business-impact-bug-race-condition-broken-access-control-de40c9897e91
- Medium / InfoSec Write-ups — Privilege Escalation via Broken Access Control: https://infosecwriteups.com/privilege-escalation-how-broken-access-control-led-to-full-account-takeover-c7b42bb9f47b
- Medium — Hands-On Understanding of OWASP Top 10 Broken Access Control: https://medium.com/@yoshiyuki.watanabe/hands-on-understanding-of-owasp-top-10-broken-access-control-938dd7665848
- OWASP WSTG — Testing for Authorization Issues: https://owasp.org/www-project-web-security-testing-guide/
