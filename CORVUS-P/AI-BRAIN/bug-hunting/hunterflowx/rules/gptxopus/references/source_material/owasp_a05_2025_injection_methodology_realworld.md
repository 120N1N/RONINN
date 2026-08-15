# OWASP A05:2025 Injection — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **Context-first payloading** payload dipilih berdasarkan sink: SQL, NoSQL, shell, template, browser, XML, LDAP, search, header.
- **Safe proof strategy** gunakan boolean, error, timing kecil, tester-owned record, or harmless callback; hindari destructive payload.
- **Second-order coverage** input disimpan lalu dieksekusi di admin, export, email, PDF, log, webhook, or worker.
- **Parser mismatch** JSON/form/multipart/XML, duplicate param, encoding, and sanitizer-renderer mismatch.
- **Reportable impact** validasi dengan data/action nyata, bukan sekadar blocked WAF or syntax noise.

---

## Core Rule A05

A05 valid bila input attacker mencapai interpreter/parser/query/template/command/selector/header/document dan mengubah struktur eksekusi, data access, rendering, routing, or downstream request di luar maksud aplikasi.

---

## Attack Surface Mapping

```text
Mapping A05:
→ input: path, query, body, header, cookie, multipart, filename, metadata, GraphQL variable, websocket message
→ context: string, numeric, identifier, JSON, HTML, JS, CSS, URL, header, command arg, file path
→ interpreter: SQL, NoSQL, LDAP, XPath, XML, shell, template, browser DOM, ORM, search DSL, regex, expression language
→ sink: database query, OS command, template render, HTML output, redirect, log, email, PDF, report, webhook
→ state: reflected, stored, blind, second-order, async, admin-only, tenant-filtered
→ impact: data read/write, auth bypass, RCE proof, XSS in privileged context, tenant filter bypass
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Dynamic search/filter/sort | often reaches SQL/NoSQL/ORM/search DSL |
| Template preview/export/email | SSTI and second-order render sink |
| File conversion/import | command/argument/parser injection |
| Admin log/dashboard rendering user input | stored XSS or log injection |
| GraphQL raw filters | schema validation may not protect backend query |
| Parser error difference | useful for safe proof and fingerprinting |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Database/query injection | 1-9 | SQL, NoSQL, ORM, LDAP, XPath, search |
| Command and server-side execution | 10-17 | command, argument, SSTI, expression, file tooling |
| Browser/client output | 18-25 | XSS, DOM, HTML, markdown, CRLF |
| Parser/document/second-order | 26-34 | XML, CSV, PDF, log, webhook, async |
| Reporting and guardrails | 35-40 | safe payload, severity, retest |

---

## Universal Testing Logic

```text
Find A05:
map input surface and exact sink context →
start with smallest harmless syntax probe →
observe error, boolean diff, timing, reflection, callback, or side effect →
confirm control over interpreter without destructive function →
prove impact with tester-owned data or safe read-only evidence →
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

> Bypass A05 berarti mencari sink/context lain ketika input awal terlihat tersanitasi. Gunakan payload aman: marker, boolean diff, error proof, timing kecil, tester-owned callback, atau rendering marker. Hindari destructive SQL/OS command, data theft, dan DoS.

## A05 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| SQL/NoSQL probe ditolak | JSON vs form, nested object, duplicate param, array/type confusion, sort/filter/include, export/report | cari parser atau sink alternatif |
| WAF/block muncul | ubah context bukan sekadar obfuscation: endpoint API v1, mobile, GraphQL, batch, import, admin report | buktikan backend sink, bukan adu payload dengan WAF |
| XSS tidak popup | cek context HTML/attribute/JS/URL/CSS, CSP, sandbox iframe, sanitized DOM, user gesture, origin/frame, stored render | cari apakah payload tidak masuk executable context |
| XSS reflected tapi tidak execute | test harmless DOM marker, event context, SVG/Markdown/rich text, postMessage, DOM sink, admin/export/email/PDF render | validasi execution path yang realistis |
| CSP memblokir | cari allowed origin, JSONP/Angular/template gadget, upload same-origin, legacy page, report-only policy | hanya valid bila script action tetap terjadi; jangan bypass origin di luar scope |
| Command injection ditolak | argument injection, filename option, environment variable, URL handler, archive/import/convert worker | cek non-shell command boundary |
| SSTI tidak eval | template engine lain, email/PDF preview, admin template, notification, delayed render | cek second-order render |
| XXE ditolak | SOAP/SAML/docx/svg/rss/import parser lain, external entity disabled but XInclude/DTD behavior, error channel | validasi parser config aman |
| CRLF/header gagal | filename, redirect, custom integration header, webhook header, cache key, email header | cari downstream header sink |
| GraphQL aman | variables in search/filter, aliases/batching, custom scalar, nested resolver, old operation | cek resolver-level injection |

## XSS No-Popup Troubleshooting

```text
1. Tentukan sink:
HTML text, attribute, JS string, URL, CSS, DOM API, Markdown, SVG, PDF, email, log viewer.

2. Tentukan origin dan frame:
same-origin, sandboxed iframe, CDN/static subdomain, data/blob URL, webview, admin-only render.

3. Tentukan policy:
CSP enforce/report-only, Trusted Types, sanitizer, iframe sandbox, MIME sniffing, HttpOnly cookie.

4. Jika alert tidak muncul:
jangan otomatis invalid.
Cari marker aman: DOM berubah, controlled image/callback in-scope, console-safe marker, event fired,
admin/export/email render, or state-changing proof with tester account.

5. Jika hanya self-XSS:
cari realistic delivery: stored field, shared object, admin review, support ticket, import/export,
OAuth/webhook notification, or log viewer.
```

## A05 Chaining Playbook

```text
Info leak/source map →
hidden API/search/export sink →
injection proof →
tenant filter bypass or stored admin XSS →
account/data/business impact.

Stored low-priv input →
admin/support/export renderer →
XSS/SSTI/log injection →
privileged action or sensitive data exposure.

Parser confusion →
validator sees safe value →
handler/query/template sees injected value →
authorization or data boundary bypass.
```

**Rule chaining:** popup bukan satu-satunya bukti. Yang penting adalah controlled execution, query control, command boundary change, or data/action impact yang aman.

---

# Methodology Patterns

## 1. Classic SQL Injection

**Find Classic SQL Injection:** uji search/filter/id/report dengan quote/boolean/error proof aman.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** query logic changes or database error/timing proves injection.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 2. Blind Boolean SQL Injection

**Find Blind Boolean SQL Injection:** bandingkan true/false conditions dengan response size/count/status.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** conditional difference is stable and tied to injected logic.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 3. Time-Based SQL Injection

**Find Time-Based SQL Injection:** gunakan delay sangat kecil dan rate rendah hanya bila program mengizinkan.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** timing difference reliable without load or DoS.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 4. Second-Order SQL Injection

**Find Second-Order SQL Injection:** input profile/name/filter disimpan lalu dipakai di report/export/admin query.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** stored value later changes query behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 5. ORM Filter Injection

**Find ORM Filter Injection:** user controls `where`, `include`, `order`, `fields`, relation, or operator.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tenant filter or data scope changes.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 6. NoSQL Operator Injection

**Find NoSQL Operator Injection:** JSON/form input accepts object operator, array, regex, or type confusion.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** auth/filter/search bypass occurs.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 7. LDAP Injection

**Find LDAP Injection:** directory login/search/group lookup accepts filter syntax.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** directory condition changes or auth/search bypasses.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 8. XPath Injection

**Find XPath Injection:** XML/SOAP/SAML lookup uses user input in XPath.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** node selection changes or data outside intended node returned.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 9. Search DSL Injection

**Find Search DSL Injection:** Elasticsearch/Lucene/Solr query syntax accepted from user.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** query bypasses tenant/filter or leaks documents.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 10. Command Injection

**Find Command Injection:** server-side tool like ping, convert, git, curl, ffmpeg, PDF runs user input.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** input escapes intended command boundary with harmless proof.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 11. Argument Injection

**Find Argument Injection:** no shell, but user controls flags/options to CLI tool.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tool behavior changes through option injection.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 12. SSTI

**Find SSTI:** template preview/email/invoice/CMS renders server-side expressions.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** harmless expression evaluates server-side.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 13. Expression Language Injection

**Find Expression Language Injection:** workflow/rules/formula engine evaluates user-controlled expression.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** expression affects server decision or output.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 14. Server-Side JavaScript Injection

**Find Server-Side JavaScript Injection:** sandbox or automation executes user-provided JS-like expression.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** safe expression runs with unintended privileges.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 15. File Path Injection

**Find File Path Injection:** download/import/template parameter reaches file resolver.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** path changes resource boundary without destructive access.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 16. Header Injection into Downstream

**Find Header Injection into Downstream:** custom webhook/proxy/integration headers include CRLF or trusted header value.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** downstream service trusts injected header.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 17. SSRF via Injection Sink

**Find SSRF via Injection Sink:** template/XML/URL parser causes server request to tester endpoint.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** server makes out-of-band request in scope.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 18. Reflected XSS

**Find Reflected XSS:** input reflected into HTML/attribute/JS/URL context.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** script executes in victim-relevant context with impact.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 19. Stored XSS

**Find Stored XSS:** comment/profile/name/file metadata stored then rendered to another user/admin.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** stored script executes for privileged/other actor.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 20. DOM XSS

**Find DOM XSS:** hash/query/postMessage/localStorage reaches DOM sink.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** client-side script execution without server reflection.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 21. Markdown/HTML Sanitizer Bypass

**Find Markdown/HTML Sanitizer Bypass:** rich text parser validates one representation and browser renders another.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** active content survives sanitizer.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 22. SVG/HTML Upload XSS

**Find SVG/HTML Upload XSS:** uploaded SVG/HTML rendered inline on same origin.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** script runs with application origin or sensitive context.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 23. PDF/Email Template Injection

**Find PDF/Email Template Injection:** input rendered in generated PDF/email with script/link/template behavior.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** recipient/admin sees executed or trusted injected content.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 24. CRLF Response Splitting

**Find CRLF Response Splitting:** input controls response header/redirect/filename.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker injects header, cookie, or cache behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 25. Cache Poisoning via Header Injection

**Find Cache Poisoning via Header Injection:** header/input influences cache key or cached response.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tester-controlled cache entry affects another request safely.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 26. XXE

**Find XXE:** XML parser resolves external entity or DTD.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** harmless callback or allowed file proof demonstrates entity resolution.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 27. XML Entity Expansion Resource Config

**Find XML Entity Expansion Resource Config:** parser allows entity expansion without sane limits.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** small safe proof shows parser risk; no DoS.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 28. CSV Formula Injection

**Find CSV Formula Injection:** exported CSV includes attacker formula in spreadsheet context.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** formula executes when opened by expected victim workflow.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 29. Log Injection

**Find Log Injection:** username/header/message injects newline/severity/fake event in logs.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** audit trail can be forged or hidden.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 30. XSS in Log Viewer

**Find XSS in Log Viewer:** log viewer renders attacker-controlled input as HTML/JS.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** script executes in admin/security analyst context.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 31. GraphQL Resolver Injection

**Find GraphQL Resolver Injection:** GraphQL variable reaches SQL/NoSQL/search without safe binding.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** resolver query changes or tenant filter bypasses.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 32. GraphQL Alias/Batch Amplification

**Find GraphQL Alias/Batch Amplification:** batch/alias causes repeated expensive resolver or bypass limit.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** security impact shown with tiny safe count.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 33. WebSocket Message Injection

**Find WebSocket Message Injection:** socket message fields reach query/template/command.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** same injection sink exists outside REST.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 34. Template Parser Confusion

**Find Template Parser Confusion:** frontend sanitizer and backend renderer use different parsers.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** payload safe in one layer executes in another.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 35. Unicode/Encoding Bypass

**Find Unicode/Encoding Bypass:** normalization/encoding changes validated input before sink.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** blocked syntax reaches interpreter after decode/normalize.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 36. Duplicate Parameter Injection

**Find Duplicate Parameter Injection:** validator reads one parameter, handler uses another.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** injected value reaches sink while safe value passes validation.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 37. Multipart Metadata Injection

**Find Multipart Metadata Injection:** filename/content-type/form field metadata reaches parser/header/command.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** metadata changes sink behavior.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 38. Webhook Payload Injection

**Find Webhook Payload Injection:** third-party event fields render/query/log downstream.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** tester-controlled event triggers injection sink.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

## 39. Safe Payload Discipline

**Find Safe Payload Discipline:** choose proof that shows control without data damage or heavy load.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** report contains minimal reproducible, non-destructive evidence.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** use parameterized APIs, context-specific output encoding, allowlist structural fields, safe command invocation, parser hardening, and identical sanitization across async/admin/export sinks.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai untrusted input to interpreter
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
→ syntax error or self-only reflection without sensitive context

Medium:
→ stored/reflected issue with limited victim path
→ injection limited to tester-owned data

High:
→ tenant filter bypass
→ admin stored XSS
→ database read/write of sensitive data
→ command execution constrained proof

Critical:
→ RCE path
→ database-wide compromise
→ admin/session takeover
→ payment/identity workflow injection
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A05 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ input parameter and sink context
→ baseline request and payload request
→ interpreter evidence: error, boolean diff, timing, callback, rendered execution, or data diff
→ tester-owned or redacted non-sensitive impact proof
→ why payload is non-destructive
→ affected role/environment and business impact
```

**Jangan hanya laporkan:**

```text
→ destructive SQL/OS commands
→ volumetric timing or regex DoS
→ stealing real user tokens/data
→ WAF block screenshots without backend evidence
```

---

## Retest Checklist

```text
Retest after fix:
→ parameterized query/safe API used
→ server-side allowlist for structural fields
→ context-specific output encoding
→ command arguments separated and option injection blocked
→ template sandboxed or disabled
→ XXE and risky parser features disabled
→ async/export/admin render uses same sanitizer
→ tenant filters enforced after parsing
```

---

# Real-World Bug Bounty Insight Appendix

## A. Search Export Bypasses Tenant Filter

**Pattern:** UI search safe, CSV export query misses tenant predicate.

```text
Find:
→ create data in tenant A/B
→ search/export with low-priv tester
→ compare API vs export output
```

**Lesson:** Injection often appears in secondary export/report path, not main UI.

---

## B. Admin Stored XSS via Log Field

**Pattern:** User-Agent or filename stored in security logs and rendered in admin console.

```text
Find:
→ send harmless marker
→ open own/admin-visible log if allowed
→ confirm rendering context
```

**Lesson:** Impact comes from privileged viewer, not from initial request.

---

## C. Argument Injection in File Converter

**Pattern:** filename beginning with option alters CLI behavior even without shell.

```text
Find:
→ upload tester file with safe option-like filename
→ observe converter output/error
→ prove behavior changed
```

**Lesson:** Shell escaping does not prevent argument injection into dangerous tools.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A05 harus punya branch “no popup” dan branch parser mismatch supaya tidak berhenti ketika payload awal terlihat gagal.

## Recent Bypass Branches

- **XSS no-popup workflow:** jika alert tidak muncul, pindah ke sink realistis: support/admin inbox, markdown preview, PDF/email renderer, notification, mobile WebView, CSV export, rich text editor, dan stored-to-admin flow.
- **CSP bypass harus dichain:** cek report-only, weak nonce, JSONP/legacy framework gadget, allowed upload origin, trusted CDN gadget, dangling markup, dan subdomain trust. Validasi impact tanpa mencuri cookie/data user.
- **Cookie/parser XSS chain:** cek parameter yang dapat set cookie, duplicate cookie precedence, path/domain scope, cookie parser ambiguity, dan sink yang membaca cookie tanpa encoding.
- **Second-order injection:** simpan marker aman di profile/filter/template/import, lalu cari eksekusi di worker, report builder, search index, log viewer, webhook, email, atau export.
- **Content-type/parser confusion:** ulangi input via JSON, form, multipart, XML fallback, GraphQL variables, URL-encoded body, duplicate key, dan CRLF/header boundary.
- **AI/LLM prompt dan output injection:** treat prompt, retrieved document, support article, ticket body, email, PDF/OCR text, tool output, dan model response sebagai source/sink. Gunakan benign instruction marker yang tidak meminta data pihak ketiga, lalu validasi apakah model/tool memisahkan data vs instruksi, menolak tool action tanpa user intent, dan tidak merender output mentah ke HTML/email/admin UI.

## Evidence Upgrade

Gunakan harmless marker, screenshot sink, source-to-sink map, request pembanding sanitized/unsanitized, dan chain impact seperti account action, admin context, atau data integrity. Jangan exfiltrate cookie atau data pihak ketiga.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **Protobuf/parser XSS:** jika target memakai protobuf/binary format, test schema-aware marker, length/payload boundary, browser form mutation, and decoder-vs-parser mismatch secara non-destruktif.
- **Client-side gadget chain:** CSPT, DOM clobbering, iframe, CSS injection, postMessage, sanitizer bypass, HTMX/template oddity, and Chrome extension sink harus dipetakan source-to-sink.
- **Whitebox patterns:** cari vulnerable coding formulas: raw template output, dangerous deserialization, XML/XPath parser, .NET remoting, command builder, and URL fetch sink.
- **No-popup escalation:** jika marker tidak eksekusi di current page, cari admin/support/PDF/email/export/mobile WebView sink.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Scanner-to-manual validation:** output Nuclei/Dalfox/Dursgo adalah lead; validasi sink, parser position, WAF behavior, browser execution, dan impact chain secara manual.
- **WebView injection boundary:** JS enabled, file access, universal access, mixed content, JS bridge, dan origin allowlist adalah source-to-sink mobile.
- **Local SQLi integrity:** SQLi lokal di mobile bernilai jika mengubah entitlement, paid/pro state, server sync, atau trust decision.
- **404/notfound reflection:** reflection di error path harus dibuktikan sebagai browser-executable sink, bukan sekadar string reflection.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A05 Injection: https://owasp.org/Top10/2025/A05_2025-Injection/
- OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP XSS Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- PortSwigger SQL injection: https://portswigger.net/web-security/sql-injection
- PortSwigger XSS: https://portswigger.net/web-security/cross-site-scripting
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
