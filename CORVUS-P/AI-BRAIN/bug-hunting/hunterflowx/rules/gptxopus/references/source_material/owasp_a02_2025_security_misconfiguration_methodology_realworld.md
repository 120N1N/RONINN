# OWASP A02:2025 Security Misconfiguration - Methodology v3 Deep Advanced Real-World Bug Bounty Edition

**Bahasa:** Indonesia  
**Status:** merged v3 deep  
**Fokus:** metodologi testing, triage, dan reporting untuk **OWASP A02:2025 — Security Misconfiguration**  
**Catatan etika:** gunakan hanya pada aset, program bug bounty, lab, atau environment yang memang memberi izin eksplisit.

---

## Core Rule

Security Misconfiguration valid bila konfigurasi aplikasi, framework, server, cloud, CDN, container, database, identity provider, CI/CD, observability, atau deployment membuat data, fungsi, credential, debug surface, trust boundary, atau internal service dapat diakses lebih luas dari secure baseline yang semestinya.

---

## Attack Surface Mapping

```text
Mapping:
→ environment: prod, staging, dev, preview, beta, mobile, legacy, region lain
→ layer: DNS, CDN, WAF, reverse proxy, web server, app server, framework, API gateway
→ runtime: container, Kubernetes, service mesh, serverless, VM, database, search service
→ identity: OAuth, OIDC, SAML, session, API key, mTLS, cloud IAM, service account
→ config source: header, cookie, CORS, CSP, HSTS, TLS, bucket ACL, IAM policy, IaC, feature flag
→ exposed surface: admin panel, debug route, docs, sample app, metrics, actuator, GraphQL playground
→ data source: backup, log, env var, source map, .git, config file, export, object storage, build artifact
→ trust boundary: public internet, authenticated user, tenant, internal service, cloud metadata, CI/CD
```

**Misconfig priority matrix:**

| Signal | Why it matters |
|---|---|
| Debug/verbose error | Fingerprint stack, secrets, internal paths, SQL/query detail |
| Default/admin console | Often becomes auth bypass, control-plane access, or RCE chain |
| Public bucket/CDN origin | Direct sensitive file exposure or origin bypass |
| Weak headers/cookies | Browser-side security control weakened |
| Permissive CORS | Authenticated data readable cross-origin |
| IAM trust wildcard | Cloud privilege abuse and cross-account role assumption |
| DNS/subdomain drift | Takeover, phishing, OAuth redirect, cookie scope abuse |
| CI/CD artifact/log exposure | Secrets, source, deploy path, and supply-chain compromise |
| Environment drift | Staging/dev has prod data or weaker controls |

---

## Universal Testing Logic

```text
Find A02:
fingerprint stack, environments, and deployment layers →
map every public, semi-public, internal-looking, and environment-specific surface →
compare prod vs staging/dev/mobile/API/legacy/region/CDN/origin →
look for default, debug, verbose, sample, backup, permissive, stale, or drifted config →
validate with non-destructive read-only evidence whenever possible →
classify whether the misconfiguration leaks data, enables auth bypass, expands attack surface,
weakens browser/cloud controls, or becomes an entry point to A01/A03/A04/A05/A07/A08/A09/A10.

Jika hasil awal terlihat aman:
jangan berhenti di satu layer.
Cek edge vs origin, UI vs API, prod vs staging, current vs legacy, framework vs gateway,
cloud policy vs app policy, and sync drift between IaC and manually created resources.
```

---

## 1. Prinsip inti A02

OWASP A02:2025 mendefinisikan **Security Misconfiguration** sebagai kondisi ketika sistem, aplikasi, atau cloud service disetel secara salah dari perspektif keamanan sehingga menciptakan vulnerability. OWASP menyebut contoh seperti missing hardening, fitur yang tidak perlu masih aktif, default account/password, verbose error, security feature baru yang tidak diaktifkan setelah upgrade, backward compatibility yang terlalu diprioritaskan, security header yang hilang, dan permission cloud yang salah.

**Root rule:**

```text
Find A02:
pahami intended secure baseline → petakan semua konfigurasi yang memengaruhi exposure →
bandingkan prod, staging, dev, API, cloud, CDN, container, CI/CD, dan identity provider →
valid jika konfigurasi membuat data, fungsi, trust boundary, credential, atau internal service terekspos.

Jika hasil awal terlihat aman:
jangan langsung simpulkan aman.
Cek konfigurasi di layer lain: CDN, reverse proxy, WAF, API gateway, container, service mesh,
identity provider, cloud role, DNS, cache, log pipeline, dan environment lama.
```

Misconfiguration jarang berdiri sendiri. Banyak temuan A02 menjadi **entry point** untuk A01, A03, A04, A05, A07, A08, A09, atau A10.

---

## 2. Cara membaca file ini

Setiap pattern menggunakan format:

```text
Find [PATTERN]:
apa yang dicari → cara membuat baseline → cara memvalidasi secara aman → kondisi valid.

Jika tidak langsung valid:
cek cabang lain → cek lokasi konfigurasi lain → cek environment lain → cek side effect.

Typical impact:
Info / Low / Medium / High / Critical, tergantung context dan chaining.
```

**Severity default tidak absolut.** Missing header bisa Info/Low, tetapi bisa naik jika menjadi bagian dari chain XSS/clickjacking. Public admin console bisa Critical bila ada default credential atau unauthenticated control plane. IAM trust wildcard bisa Critical bila role punya permission tinggi.

---

## 3. Cluster navigasi

| Cluster | Isi |
|---|---|
| Web hardening | headers, cookies, HSTS, TLS |
| Exposure | debug, error, backup, secrets |
| Protocol | HTTP methods, smuggling, CORS |
| Cloud | storage, IAM, IMDS, DNS |
| Identity | OAuth, OIDC, SAML, session |
| API | GraphQL, rate limit, docs |
| Runtime | container, K8s, service mesh |
| Pipeline | CI/CD, IaC, drift |
| Data plane | logs, cache, tenant isolation |

---

## Decision Tree

```text
Jika 200/204:
→ cek apakah response memang public
→ cek side effect
→ cek apakah data sensitif dikirim tapi UI menyembunyikan
→ cek cache/CDN
→ cek header/cookie/security directive
→ cek apakah status sukses terjadi di endpoint yang seharusnya internal

Jika 301/302/307/308:
→ cek apakah redirect menyembunyikan response asli
→ cek redirect ke HTTP atau external domain
→ cek callback/return/next/RelayState
→ cek apakah token ikut dalam URL
→ cek cache redirect

Jika 401:
→ cek endpoint alternatif
→ cek asset static/export/download
→ cek API version lama
→ cek dev/staging host
→ cek token lama, remember-me, API key, signed URL

Jika 403:
→ cek apakah block di edge saja atau backend juga
→ cek method lain
→ cek content-type lain
→ cek header custom
→ cek host header
→ cek API gateway vs origin
→ cek service mesh bypass

Jika 404:
→ bandingkan dari environment lain
→ cek trailing slash, case, extension
→ cek route lama
→ cek source map / API schema
→ cek DNS/CDN/origin mismatch
→ cek apakah 404 masking digunakan

Jika 500:
→ cek verbose stack trace
→ cek environment variable leak
→ cek framework version
→ cek path internal
→ cek database error
→ cek secret redaction

Jika UI aman:
→ jangan berhenti
→ cek raw response
→ cek API langsung
→ cek JS bundle
→ cek source map
→ cek mobile API
→ cek GraphQL schema
→ cek documentation endpoint
```

---

## Severity Heuristic

```text
Info:
konfigurasi kurang ideal tetapi belum ada exposure atau chain nyata.

Low:
misconfiguration melemahkan defense-in-depth tetapi impact langsung kecil.

Medium:
misconfiguration mengekspos informasi, memperluas attack surface, atau mempermudah exploit.

High:
misconfiguration memungkinkan unauthorized access, token/session exposure, sensitive data exposure,
SSO abuse, subdomain takeover, atau cloud privilege abuse.

Critical:
misconfiguration memberi control plane access, admin access, RCE path, role assumption berisiko tinggi,
credential compromise, public secret, atau takeover aset production.
```

---

# Bypass & Chaining Workflow

> Gunakan workflow ini untuk membuktikan misconfiguration secara aman. Jangan brute force, jangan load test, dan jangan mengambil data pihak ketiga; cukup buktikan exposure dengan asset tester, metadata redacted, atau konfigurasi yang terlihat.

## A02 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| Domain utama aman | origin host/IP, alternate hostname, CDN history, cert SAN, old DNS, direct object URL | cek edge/CDN/WAF tidak menjadi satu-satunya kontrol |
| Prod aman | staging, dev, preview, beta, old region, mobile API, legacy host | cek environment drift dan prod data di non-prod |
| Admin panel 403 | path/case/suffix, default route, old console, management plane, source map route | cek panel masih reachable di surface lain |
| Header/cookie tampak lemah | cari endpoint auth/sensitive yang bergantung pada browser control | naikkan dari low ke impact chain yang nyata |
| CORS terlihat longgar | cek credentials, reflected origin, `null` origin, subdomain takeover chain, readable response | valid hanya bila origin asing bisa membaca data authenticated |
| Bucket/listing ditutup | predictable object key, old export, signed URL lifecycle, CDN cache, folder dari JS | cek object-level exposure tanpa listing |
| GraphQL tooling disabled | introspection via auth role berbeda, old path, schema source map, mobile endpoint, verbose error | cek schema/operation leak di surface lain |
| Cloud IAM tampak aman | trust policy condition, wildcard principal, ExternalId, role chaining, over-permissioned service role | cek privilege boundary cloud |
| Debug tidak muncul | trigger error aman, `Accept` HTML/JSON, GraphQL error, webhook error, staging/preview | cek verbose error per renderer/environment |
| Docs/API tertutup | source map, mobile bundle, OpenAPI old version, developer portal, generated clients | cek route/function leakage |

## A02 Chaining Playbook

```text
Source map / docs / verbose error →
internal route, package, version, tenant key →
A01 IDOR/BAC or A05 injection target →
impact data/action nyata.

Origin bypass →
edge auth/WAF/cache control hilang →
admin/API/debug route terbuka →
credential/data/control-plane exposure.

Public bucket/export/CDN →
private file or source leak →
secret/API key/package token →
A03/A04/A07/A08 escalation.

DNS takeover / email auth gap →
trusted domain abuse →
OAuth redirect, cookie scope, reset/invite phishing chain →
account or tenant impact.
```

**Rule chaining:** missing header atau version leak sendiri sering rendah; severity naik hanya bila chain realistis dan dibuktikan.

---

# Methodology Patterns

## 6.1 Missing secure baseline / incomplete hardening

**Find Missing Baseline:** mapping server, framework, API gateway, CDN, WAF, cloud, container, database, CI/CD, dan identity provider → bandingkan dengan baseline secure yang disepakati → cari environment yang belum mengikuti baseline → valid jika ada konfigurasi yang membuat surface tidak perlu terbuka atau security control tidak aktif.

**Jika terlihat aman:** cek environment drift, staging, old subdomain, internal endpoint yang diekspos publik, region cloud lain, dan resource yang dibuat manual di luar IaC.

```text
Prod aman
→ cek staging
→ cek preview environment
→ cek region lain
→ cek legacy host
→ cek IaC drift
→ cek resource manual
```

**Typical impact:** Medium–High.

---

## 6.2 Default accounts and credentials

**Find Default Credentials:** identifikasi admin console, appliance, database UI, CMS, monitoring, CI/CD, dashboard, staging app, dan sample app → cek apakah default account masih aktif → valid jika default credential atau akun vendor/test dapat login ke aset non-lab.

**Jika login default gagal:** cek akun sample lain, password yang tertulis di config, onboarding guide, container image default, Helm chart default, dan credential di documentation endpoint.

```text
admin/admin gagal
→ cek vendor default lain
→ cek sample user
→ cek config leak
→ cek Helm chart default
→ cek seeded database user
```

**Typical impact:** High–Critical.

---

## 6.3 Unnecessary features, services, files, and documentation

**Find Unnecessary Features:** cari sample app, documentation, test route, old API, Swagger/OpenAPI, GraphiQL, actuator, metrics, debug page, default server page, `.git`, `.svn`, `.DS_Store`, source map, package metadata, dan backup file → valid jika fitur/file yang tidak perlu membuka informasi atau fungsi berbahaya.

**Jika root path aman:** cek subfolder, alternate host, CDN asset, old release path, dan JS bundle reference.

```text
/ aman
→ cek /docs
→ cek /api-docs
→ cek /swagger
→ cek /graphql
→ cek /.git/HEAD
→ cek /actuator
→ cek source map
```

**Typical impact:** Low–Critical.

---

## 6.4 Debug mode in production

**Find Debug Mode:** cek framework flag seperti `DEBUG`, `NODE_ENV`, verbose exception, interactive debugger, hot reload, test framework, profiling panel, dan debug headers → valid jika debug mode production mengungkap stack, environment, secret, interactive console, atau internal route.

**Jika debug tidak muncul normal:** trigger error non-destruktif, cek API error, cek Accept header, cek JSON vs HTML error, dan cek staging/preview.

```text
Normal response bersih
→ trigger error aman
→ cek JSON error
→ cek HTML error
→ cek debug header
→ cek staging host
```

**Typical impact:** Medium–Critical.

---

## 6.5 Verbose error, stack trace, and log forwarding leak

**Find Verbose Error:** buat error aman pada route yang valid → amati stack trace, framework version, file path, SQL error, environment, internal IP, dependency version, atau secret redaction failure → valid jika informasi internal berguna untuk exploit berikutnya.

Tambahkan checkpoint untuk **Sentry/Bugsnag/public DSN** di JS bundle. Public DSN tidak selalu secret, tetapi bisa menjadi masalah bila event ingestion menerima data sensitif, issue detail terbuka publik, atau source map mengungkap code.

```text
Error page bersih
→ cek API error
→ cek GraphQL error
→ cek webhook error
→ cek log forwarding SDK
→ cek source map
→ cek stack trace di mobile API
```

**Typical impact:** Low–High.

---

## 6.6 Missing or weak security headers

**Find Header Misconfiguration:** cek semua response utama, API, static asset, error page, redirect, CDN cached page, dan subdomain → valid jika security directive hilang atau terlalu longgar sehingga melemahkan perlindungan browser.

Header utama:

- `Strict-Transport-Security`
- `Content-Security-Policy`
- `X-Content-Type-Options`
- `X-Frame-Options` atau `frame-ancestors`
- `Referrer-Policy`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy`
- `Cross-Origin-Resource-Policy`
- `Cross-Origin-Embedder-Policy`

**Jika homepage aman:** cek error page, login page, OAuth callback, file download, admin page, API JSON, dan CDN asset.

```text
Homepage punya header
→ cek 404/500
→ cek login
→ cek callback
→ cek API JSON
→ cek static asset
→ cek CDN response
```

**Typical impact:** Info–Medium, bisa High bila chaining.

---

## 6.7 Cookie flag misconfiguration

**Find Cookie Misconfiguration:** cek session, refresh, remember-me, CSRF, tenant, OAuth state, dan device cookie → valid jika cookie sensitif tidak memiliki flag yang sesuai atau cakupan domain/path terlalu luas.

Cek:

- `Secure`
- `HttpOnly`
- `SameSite`
- `Domain`
- `Path`
- expiry
- prefix `__Host-` atau `__Secure-` bila relevan

**Jika cookie utama aman:** cek subdomain, SSO callback, remember-me, legacy session, mobile web, staging, dan OAuth flow.

```text
Session cookie aman
→ cek remember-me
→ cek refresh token
→ cek OAuth state
→ cek subdomain cookie
→ cek legacy cookie
```

**Typical impact:** Low–High.

---

## 6.8 HSTS misconfiguration

**Find HSTS Issue:** cek apakah HTTPS enforced, HSTS aktif di production, max-age cukup, includeSubDomains sesuai, dan tidak ada mixed scheme callback → valid jika user masih bisa dipaksa HTTP atau subdomain penting tidak terlindungi.

**Jika HSTS ada:** cek preload readiness, subdomain coverage, HTTP redirect chain, CDN edge, dan alternate host.

```text
HSTS ada di root
→ cek www
→ cek api
→ cek auth
→ cek static
→ cek callback
→ cek redirect pertama dari HTTP
```

**Typical impact:** Low–High.

---

## 6.9 TLS/SSL cipher, protocol, certificate, and downgrade misconfiguration

**Find TLS Misconfiguration:** audit semua endpoint TLS, bukan hanya domain utama → cek protocol version, cipher suite, certificate chain, SAN, expiry, OCSP stapling, forward secrecy, HTTP/2/TLS interaction, dan downgrade behavior → valid jika TLS mendukung protocol/cipher lemah, certificate salah, atau authentication TLS dapat dilewati.

Penekanan v3:

- Nonaktifkan `SSLv2`, `SSLv3`, `TLS 1.0`, dan `TLS 1.1`.
- Gunakan `TLS 1.2` atau `TLS 1.3`.
- Untuk TLS 1.2, prioritaskan cipher AEAD seperti AES-GCM atau ChaCha20-Poly1305.
- Jangan aktifkan RC4, DES, 3DES, EXPORT, NULL, anonymous cipher, atau weak DH.
- Hindari static RSA key exchange karena tidak memberi forward secrecy.
- Pastikan tidak ada protocol downgrade path.
- Pastikan certificate valid, tidak expired, tidak self-signed di production, dan SAN cocok.
- Audit internal API, admin port, API gateway, monitoring endpoint, dan mobile backend.

**Jika public endpoint aman:** cek internal endpoint yang tetap accessible via VPN, alternate port, staging, API gateway, CDN origin, mail/webhook TLS, dan service mesh egress.

```text
443 aman
→ cek 8443
→ cek API gateway
→ cek CDN origin
→ cek staging
→ cek admin dashboard
→ cek webhook endpoint
→ cek internal API
```

**Valid jika:** endpoint production menerima TLS lama, cipher lemah, certificate tidak valid, atau konfigurasi memungkinkan MITM/downgrade pada skenario realistis.

**Typical impact:** Low–High, bisa Critical untuk mTLS/auth bypass atau sensitive channel.

---

## 6.10 mTLS misconfiguration

**Find mTLS Misconfiguration:** identifikasi endpoint yang mengklaim memakai mTLS → cek apakah client certificate benar-benar required, chain divalidasi, identity certificate dipetakan ke allowlist, dan fallback non-mTLS tidak aktif → valid jika endpoint menerima request tanpa client cert atau menerima cert dari identity yang tidak semestinya.

Cek:

- `optional` vs `required`
- client cert SAN/CN mapping
- expired client cert
- revoked client cert
- trust store terlalu luas
- plaintext bypass port
- sidecar bypass
- fallback ke bearer token tanpa constraint

```text
mTLS aktif di gateway
→ cek origin langsung
→ cek alternate port
→ cek path health/debug
→ cek service mesh permissive mode
→ cek client cert identity mapping
```

**Typical impact:** High–Critical.

---

## 6.11 CORS misconfiguration

**Find CORS Misconfiguration:** cari API sensitif yang memakai cookie/session/browser credential → uji apakah origin tidak tepercaya bisa membaca response → valid jika attacker-controlled origin dapat membaca data authenticated.

**Jika header terlihat longgar tapi data tidak terbaca:** cek `Access-Control-Allow-Credentials`, wildcard, reflected origin, preflight, method, allowed headers, cookie `SameSite`, dan apakah endpoint memang public.

```text
Origin direfleksikan
→ cek credentials
→ cek sensitive endpoint
→ cek cookie dikirim
→ cek preflight
→ cek wildcard + credential
→ cek subdomain takeover chain
```

**Typical impact:** Medium–High.

---

## 6.12 Legacy cross-domain policy

**Find Crossdomain Policy:** cek `crossdomain.xml`, `clientaccesspolicy.xml`, dan legacy Flash/Silverlight policy → valid jika policy mengizinkan domain luas pada endpoint sensitif atau internal.

**Jika tidak ada di root:** cek subdomain, CDN, upload host, API host, dan old static host.

```text
/crossdomain.xml tidak ada
→ cek api host
→ cek static host
→ cek legacy host
→ cek CDN host
```

**Typical impact:** Low–Medium.

---

## 6.13 Directory listing

**Find Directory Listing:** cek folder upload, backup, export, asset, build, media, temp, log, dan static route → valid jika daftar file membantu menemukan data, source, backup, atau secret.

**Jika listing mati:** cek subfolder, alternate host, bucket listing, generated index, dan CDN origin.

```text
/uploads/ aman
→ cek /uploads/reports/
→ cek /backup/
→ cek /static/maps/
→ cek bucket endpoint
```

**Typical impact:** Low–High.

---

## 6.14 Backup/source/config files exposed

**Find Exposed Files:** cari file `.env`, `.git`, `.svn`, `.hg`, `.DS_Store`, `composer.json`, `package.json`, `yarn.lock`, `pnpm-lock.yaml`, `requirements.txt`, `web.config`, `application.properties`, `application.yml`, `spring.config.*`, `.bak`, `.old`, `.zip`, `.tar.gz`, SQL dump, dan source map → valid jika file mengungkap secret, dependency, route, or internal architecture.

**Jika direct path 404:** cek casing, extension, old deploy folder, CDN cache, source map pointer, dan staging.

```text
.env 404
→ cek .env.prod
→ cek .env.backup
→ cek application.yml
→ cek source map
→ cek deploy.zip
→ cek database.sql
```

**Typical impact:** Medium–Critical.

---

## 6.15 Secrets exposure in config, repository, environment, and logs

**Find Secrets Exposure:** audit code, config, env vars, JS bundle, logs, CI/CD variables, Terraform state, Docker image layer, mobile app, and generated reports → valid jika API key, database password, private key, JWT secret, webhook secret, cloud key, or signing key dapat dibaca oleh pihak tidak berhak.

Penekanan v3:

- Blokir public access ke `.env`, `application.properties`, `spring.config.*`, dan secret file lain.
- Scan code repository dan commit history.
- Scan artifact build.
- Scan container image layer, bukan hanya filesystem runtime.
- Scan logs/traces untuk token dan credential.

```text
Repo bersih
→ cek commit history
→ cek CI artifact
→ cek Terraform state
→ cek Docker layer
→ cek source map
→ cek log pipeline
```

**Typical impact:** High–Critical.

---

## 6.16 Sensitive data in URL and access logs

**Find Sensitive Data in URL:** cek login, reset password, magic link, OTP, invite, download, OAuth callback, payment, webhook retry, dan tracking link → valid jika token, OTP, session ID, email, user ID sensitif, atau credential dikirim lewat query string dan masuk browser history, referrer, access log, CDN log, SIEM, atau third-party analytics.

**Jika tidak terlihat di UI:** cek network log, redirect chain, email link, mobile deep link, analytics event, and access log redaction.

```text
Token tidak terlihat di page
→ cek URL query
→ cek redirect chain
→ cek Referer
→ cek analytics payload
→ cek server access log
→ cek CDN log
```

**Typical impact:** Medium–High.

---

## 6.17 HTTP method and WebDAV misconfiguration

**Find Method Misconfiguration:** cek method yang diterima: `PUT`, `DELETE`, `PATCH`, `TRACE`, `TRACK`, `OPTIONS`, `PROPFIND`, `MKCOL`, `COPY`, `MOVE` → valid jika method tidak perlu aktif dan memungkinkan upload, overwrite, delete, disclosure, or cross-site tracing.

**Jika root aman:** cek subfolder, upload path, API path, old route, WebDAV path, and CDN/origin mismatch.

```text
OPTIONS root aman
→ cek /api
→ cek /uploads
→ cek /webdav
→ cek old host
→ cek origin langsung
```

**Typical impact:** Low–Critical.

---

## 6.18 HTTP request smuggling and header smuggling

**Find Smuggling Misconfiguration:** identifikasi chain frontend-backend: CDN, WAF, reverse proxy, load balancer, API gateway, app server → cari parsing differential antara frontend dan backend, terutama `Content-Length` dan `Transfer-Encoding` → valid jika request boundary, header, atau path diproses berbeda sehingga security control bisa dilewati.

Penekanan v3:

- Cek mismatch `Content-Length` / `Transfer-Encoding`.
- Cek HTTP/2 downgrade ke HTTP/1.1.
- Cek duplicate header dan ambiguous header.
- Cek `X-Forwarded-Host`, `X-Forwarded-Proto`, `X-Original-URL`, `X-Rewrite-URL`, dan `Forwarded`.
- Cek path restriction bypass di reverse proxy.
- Cek cache poisoning atau auth bypass akibat header yang tidak di-key.

**Jika scanner tidak menemukan:** jangan anggap aman; smuggling sering context-specific. Validasi topology, server versions, proxy normalization, dan backend origin behavior.

```text
Edge tampak aman
→ cek origin path
→ cek H2 downgrade
→ cek duplicate header
→ cek forwarded headers
→ cek proxy rewrite headers
→ cek cache key
```

**Typical impact:** High–Critical.

---

## 6.19 Proxy, CDN, and cache configuration

**Find Proxy/CDN Misconfiguration:** cek cache key, `Vary`, `Cache-Control`, cookie handling, auth header handling, origin shielding, error caching, redirect caching, custom header trust, and host header routing → valid jika personalized or privileged response disajikan ke user lain atau request ke origin dapat dimanipulasi.

**Jika live response aman:** cek cached response, stale response, error cache, route variant, parameter variant, and unkeyed header.

```text
Live API aman
→ cek cached copy
→ cek stale cache
→ cek unkeyed query
→ cek unkeyed header
→ cek error response cached
→ cek Host routing
```

**Typical impact:** Medium–Critical.

---

## 6.20 Web cache poisoning and cache deception

**Find Cache Abuse:** cek apakah parameter/header yang tidak masuk cache key memengaruhi response → cek apakah private page dapat disimpan sebagai static-looking resource → valid jika cache menyimpan konten berbahaya atau data private.

**Jika cache-control aman:** cek CDN override, service worker, browser cache, proxy cache, and old rules.

```text
no-store ada
→ cek CDN rule override
→ cek service worker
→ cek static extension path
→ cek error response
→ cek redirect response
```

**Typical impact:** Medium–Critical.

---

## 6.21 Public cloud storage and object permissions

**Find Cloud Storage Misconfiguration:** audit S3/GCS/Azure Blob/bucket/object store → cek public read/write/list, bucket policy, object ACL, signed URL expiry, CDN public origin, encryption, versioning, and lifecycle → valid jika data non-public dapat dibaca/ditulis/listed oleh pihak tidak berhak.

**Jika bucket private:** cek object-level ACL, old object, versioned object, signed URL lifetime, CDN cache, and cross-account policy.

```text
Bucket private
→ cek object ACL
→ cek old versions
→ cek signed URLs
→ cek CDN origin
→ cek replication target
→ cek bucket policy wildcard
```

**Typical impact:** High–Critical.

---

## 6.22 Cloud IAM role trust misconfiguration

**Find IAM Trust Misconfiguration:** audit trust policy, permission policy, service account binding, managed identity, workload identity, and cross-account assumption → valid jika principal yang tidak seharusnya bisa assume role, impersonate service account, atau mendapatkan permission berlebih.

Penekanan v3:

- Cek `Principal: *` atau wildcard principal.
- Cek account root trust yang terlalu luas.
- Cek multiple principal yang diasumsikan sebagai AND padahal dievaluasi sebagai OR.
- Cek missing `Condition` seperti MFA, source account, source ARN, audience, external ID, branch/ref, or subject.
- Cek cross-account trust.
- Cek GitHub Actions/OIDC trust wildcard branch.
- Cek privilege role setelah assumption, bukan hanya trust.
- Terapkan least privilege dan short-lived credential.

```text
Policy terlihat spesifik
→ cek wildcard dalam ARN
→ cek Condition kosong
→ cek external ID
→ cek source account
→ cek OIDC subject
→ cek permission setelah assume
→ cek cross-account path
```

**Valid jika:** role dapat diasumsikan oleh principal yang tidak dimaksudkan atau permission setelah assumption melebihi kebutuhan.

**Typical impact:** High–Critical.

---

## 6.23 Cloud compute/function role overpermission

**Find Compute Role Misconfiguration:** audit role attached ke EC2, Lambda, ECS task, Cloud Run, GCE, Azure Function, VM, and container workload → valid jika workload public/low-trust memegang permission sensitive seperti admin, secret read, storage write, KMS decrypt, iam pass role, or deploy.

**Jika role tampak minimal:** cek inline policies, managed policies, inherited permission, permission boundary, resource wildcard, and service-linked roles.

```text
Role tampak kecil
→ cek managed policy
→ cek inline policy
→ cek resource wildcard
→ cek iam:PassRole
→ cek secrets access
→ cek KMS decrypt
```

**Typical impact:** High–Critical.

---

## 6.24 Cloud metadata service exposure / IMDS

**Find IMDS Exposure:** cek apakah workload dapat mengakses metadata service dan apakah metadata credential bisa dicapai melalui SSRF, proxy, container escape, or misrouted egress → valid jika aplikasi public bisa memicu workload membaca credential metadata atau metadata endpoint tidak dibatasi.

Cek:

- IMDSv1 enabled
- IMDSv2 not required
- hop limit terlalu longgar
- metadata egress tidak diblokir dari container
- SSRF sink dapat mencapai metadata
- overly privileged instance role

**Jika SSRF test eksternal blocked:** cek redirect handling, internal fetcher, webhook validator, URL preview, PDF generator, and image fetcher dalam scope yang diizinkan.

```text
Direct metadata blocked
→ cek URL fetcher lain
→ cek redirect follow
→ cek container network
→ cek hop limit
→ cek IMDSv2 required
→ cek role permission
```

**Typical impact:** High–Critical.

---

## 6.25 DNS and subdomain takeover misconfiguration

**Find DNS/Subdomain Takeover:** enumerate DNS records untuk CNAME, NS, MX, A/AAAA, TXT, and cloud-managed host → cari record yang menunjuk ke service non-existent, deprovisioned, expired, or unclaimed → valid jika subdomain dapat diklaim oleh pihak yang tidak berhak atau record mengarah ke resource yang tidak aktif.

Penekanan v3:

- Cari dangling CNAME ke S3, Azure Storage, Azure App Service, Heroku, GitHub Pages, Vercel, Netlify, CloudFront, Fastly, Zendesk, Shopify, or old SaaS.
- Cari dangling NS delegation.
- Cari dangling MX yang bisa menerima email untuk subdomain.
- Verifikasi domain dihapus saat layanan berhenti.
- Evaluasi cookie `Domain=.example.com` karena takeover subdomain bisa mencuri cookie scoped luas.
- Evaluasi CSP jika subdomain dipercaya sebagai script/image/connect source.
- Jangan klaim resource tanpa izin program; cukup buktikan dengan evidence yang diizinkan scope.

```text
CNAME terlihat aktif
→ cek provider error signature
→ cek resource existence
→ cek service expired
→ cek DNS TTL
→ cek cookie Domain
→ cek CSP trust
→ cek MX/NS delegation
```

**Valid jika:** record DNS tetap menunjuk ke layanan yang bisa dikontrol pihak lain, atau subdomain trust dapat disalahgunakan.

**Typical impact:** Medium–Critical.

---

## 6.26 Email authentication misconfiguration: SPF, DKIM, DMARC, BIMI

**Find Email Auth Misconfiguration:** cek DNS TXT SPF, DKIM selector, DMARC record, alignment, third-party senders, and reporting → valid jika domain mudah di-spoof atau email legitimate gagal karena record salah.

Penekanan v3:

- SPF tidak boleh `+all`.
- Soft fail `~all` tidak menolak spoofing secara tegas.
- SPF lookup harus tidak melebihi 10 DNS lookup.
- Domain sebaiknya memiliki satu SPF record valid.
- Semua third-party sender harus masuk SPF/DKIM alignment.
- DKIM harus aktif dan key tidak lemah.
- DMARC minimal `p=quarantine`, ideal `p=reject` setelah monitoring.
- Subdomain policy `sp=` perlu dicek.
- DMARC report `rua`/`ruf` membantu monitoring.
- BIMI bukan pengganti DMARC; BIMI bergantung pada DMARC enforcement.

```text
SPF ada
→ cek +all/~all
→ cek lookup count
→ cek multiple SPF
→ cek DKIM selector
→ cek DMARC p=none
→ cek alignment
→ cek third-party sender
```

**Valid jika:** spoofing domain masih diterima pada kondisi realistis atau record email auth gagal enforce policy.

**Typical impact:** Medium–High.

---

## 6.27 OAuth / OIDC provider and relying-party misconfiguration

**Find OAuth/OIDC Misconfiguration:** mapping authorization server, client app, redirect URI, callback, state, nonce, PKCE, scope, audience, issuer, token lifetime, and grant type → valid jika config memungkinkan account takeover, code/token leakage, scope escalation, or token misuse.

Cek:

- redirect URI wildcard
- regex/prefix allowlist
- subdomain wildcard
- open redirect chain
- missing state
- weak state
- missing nonce
- PKCE optional untuk public client
- implicit flow masih aktif
- excessive scopes
- audience tidak dicek
- issuer tidak dicek
- token dikirim via query
- client secret public
- token endpoint menerima credential di query

**Jika redirect URI utama strict:** cek alternate callback, mobile deep link, localhost exception, custom scheme, staging callback, and old client ID.

```text
redirect_uri strict
→ cek wildcard subdomain
→ cek open redirect chain
→ cek localhost/custom scheme
→ cek old client
→ cek PKCE optional
→ cek audience/issuer
```

**Typical impact:** High–Critical.

---

## 6.28 SAML configuration issues

**Find SAML Misconfiguration:** cek metadata IdP/SP, certificate, assertion signature, response signature, audience restriction, recipient, ACS URL, RelayState, NameID, group mapping, and replay window → valid jika assertion dapat dipakai ulang, dimodifikasi, dikirim ke SP yang salah, atau diarahkan ke URL tidak tepercaya.

Cek:

- signature optional
- only response signed, assertion not validated
- signature wrapping risk
- ACS URL bebas
- audience restriction tidak dicek
- NotBefore/NotOnOrAfter terlalu longgar
- RelayState open redirect
- weak XMLDSig mode
- expired signing certificate accepted
- group/role mapping too broad

```text
Login SAML berhasil normal
→ cek metadata
→ cek signature required
→ cek assertion signed
→ cek audience
→ cek ACS binding
→ cek RelayState
→ cek replay window
```

**Typical impact:** High–Critical.

---

## 6.29 Session lifecycle misconfiguration

**Find Session Lifecycle Misconfiguration:** login → simpan session/token → lakukan logout, password change, role change, device revoke, org removal, MFA reset, or account disable → gunakan kembali session/token lama pada endpoint sensitif → valid jika session yang seharusnya mati masih bisa dipakai.

Penekanan v3:

- Invalidate session pada logout.
- Invalidate/rotate session setelah password change.
- Invalidate/refresh authorization setelah role change.
- Rotate session ID after login.
- Gunakan expiry wajar.
- Gunakan `Secure`, `HttpOnly`, dan `SameSite` sesuai context.
- Sediakan re-authentication untuk aksi sensitif seperti ubah email, ubah password, tambah rekening, atau ubah MFA.
- Logout SSO dan app session perlu dipahami terpisah.

```text
Logout mematikan session utama
→ cek refresh token
→ cek remember-me
→ cek API key
→ cek WebSocket
→ cek mobile session
→ cek role downgraded token
→ cek password-change old token
```

**Typical impact:** Medium–High.

---

## 6.30 Rate limiting and anti-automation misconfiguration

**Find Rate Limit Misconfiguration:** identifikasi endpoint sensitif seperti login, OTP, password reset, email verification, invite, upload, payment, webhook, search, GraphQL, and public API → lakukan test burst aman sesuai scope → valid jika endpoint dapat disalahgunakan tanpa throttling, lockout, quota, or detection.

Penekanan v3:

- Jangan hanya rate limit per IP.
- Terapkan per user, per account, per API key, per device, per tenant, dan per action.
- Di balik proxy/WAF, validasi `X-Forwarded-For` hanya dari trusted proxy.
- Jangan percaya user-supplied forwarding headers.
- CAPTCHA yang hanya ada di UI bukan control backend.
- GraphQL perlu rate limit berbasis cost/complexity, bukan hanya request count.
- Webhook perlu rate limit dan replay protection.

```text
Login punya rate limit IP
→ cek per account
→ cek per username
→ cek per API key
→ cek X-Forwarded-For trust
→ cek distributed source
→ cek OTP resend
→ cek password reset
```

**Typical impact:** Medium–High.

---

## 6.31 GraphQL-specific misconfiguration

**Find GraphQL Misconfiguration:** cari endpoint GraphQL, schema exposure, introspection, GraphiQL/Playground, verbose error, query depth, complexity, batching, aliases, persisted queries, GET support, CSRF, and field-level auth → valid jika GraphQL production membuka tooling, schema, expensive queries, or fields that should be restricted.

Penekanan v3:

- Introspection production harus dinonaktifkan atau gated dengan auth/role yang tepat.
- Error tidak boleh membocorkan schema, resolver, internal path, SQL, or stack trace.
- GraphiQL/Playground tidak boleh public di production.
- Terapkan depth limit.
- Terapkan complexity/cost limit.
- Terapkan timeout and resolver resource limit.
- Terapkan allowlist/persisted queries untuk high-risk API.
- Rate limit berdasarkan cost, bukan hanya jumlah request.
- Monitor schema drift secara continuous.
- Jalankan automated introspection checks setiap deploy.
- Validasi field-level authorization, bukan hanya root query.

```text
Introspection disabled
→ cek verbose error schema leak
→ cek GraphiQL path
→ cek GET query
→ cek alias amplification
→ cek batching
→ cek nested query depth
→ cek field-level authorization
→ cek schema change drift
```

**Valid jika:** schema/tooling production terekspos tanpa kebutuhan, query expensive tidak dibatasi, atau field sensitive dikirim karena resolver/authorization config longgar.

**Typical impact:** Medium–Critical.

---

## 6.32 API documentation and developer tooling exposed

**Find API Tooling Exposure:** cari Swagger, OpenAPI, Postman collection, API schema, SDK docs, GraphiQL, admin docs, sample requests, and test console → valid jika documentation memberi endpoint, token, internal hostname, or action sensitive yang tidak seharusnya public.

**Jika docs butuh auth:** cek old docs, cached docs, JSON spec direct file, staging docs, and mobile docs.

```text
/docs 401
→ cek /openapi.json
→ cek /swagger.json
→ cek cached spec
→ cek staging docs
→ cek JS bundle route
```

**Typical impact:** Low–High.

---

## 6.33 XML External Entity / XXE parser configuration

**Find XXE Misconfiguration:** cari XML parser, SOAP, SAML, SVG, DOCX/XLSX import, RSS, sitemap, and file upload that parses XML → valid jika external entity/DTD resolution enabled and can read local file, make SSRF, or cause network callback in authorized test.

**Jika XML upload rejected:** cek content-type, file import, SOAP endpoint, SAML parser, SVG preview, and office document parsing.

```text
XML endpoint aman
→ cek SOAP
→ cek SVG
→ cek SAML
→ cek file import
→ cek document conversion
```

**Typical impact:** High–Critical.

---

## 6.34 XML entity expansion / parser resource limits

**Find Entity Expansion:** cek XML parser resource limit, DTD handling, entity expansion, recursion limit, and file size limit → valid jika parser dapat dibuat menghabiskan CPU/memory dalam test aman.

**Jika DTD disabled:** cek nested data parser lain, YAML, JSON parser limit, multipart parser, and archive decompression.

```text
DTD disabled
→ cek YAML parser
→ cek JSON nesting
→ cek multipart size
→ cek archive extraction
```

**Typical impact:** Medium–High.

---

## 6.35 Unsafe deserialization safe-mode misconfiguration

**Find Deserialization Mode:** cari Java serialization, .NET BinaryFormatter, PHP `unserialize`, Python `pickle`, Ruby `Marshal`, YAML unsafe loader, Jackson default typing, MessagePack typeless mode, and framework view state → valid jika aplikasi deserializes untrusted data menggunakan mode unsafe atau tanpa allowlist.

**Jika endpoint tidak langsung jelas:** cek cookies, hidden fields, queue messages, cache blobs, session storage, signed-but-not-encrypted data, and file imports.

```text
No direct serialized input
→ cek cookie
→ cek hidden field
→ cek queue
→ cek cache
→ cek upload import
→ cek ViewState
```

**Typical impact:** High–Critical.

---

## 6.36 Template engine and SSTI mode misconfiguration

**Find Template Misconfiguration:** cek template engine exposed to user-controlled templates, debug template context, unsafe helper, sandbox disabled, and sensitive globals like config/request/session → valid jika template can access internal object, secret, or execute logic beyond intended.

**Jika user input escaped:** cek admin-customizable template, email template, CMS block, report template, PDF generator, and preview mode.

```text
Form input safe
→ cek email template
→ cek CMS block
→ cek report template
→ cek PDF preview
→ cek admin template editor
```

**Typical impact:** High–Critical.

---

## 6.37 Framework-specific insecure settings

**Find Framework Misconfiguration:** cek framework flags and security settings for Django, Flask, Spring, Express, Rails, Laravel, ASP.NET, Next.js, Nuxt, NestJS, and PHP config → valid jika framework security feature disabled or development mode active in production.

Examples to check:

- Django `DEBUG=True`, `ALLOWED_HOSTS=*`
- Flask debug console
- Spring Boot actuator exposure
- Express development error handler
- Rails local errors in production
- Laravel debug mode
- ASP.NET detailed errors
- Next.js source map exposure

```text
Framework root aman
→ cek error route
→ cek actuator
→ cek health/metrics
→ cek source map
→ cek debug console
```

**Typical impact:** Medium–Critical.

---

## 6.38 Database and search service exposure

**Find Data Service Exposure:** scan authorized asset inventory for database/admin/search endpoints like PostgreSQL, MySQL, Redis, MongoDB, Elasticsearch, Kibana, ClickHouse, RabbitMQ, Kafka UI, and adminer/phpMyAdmin → valid jika service exposed publicly, unauthenticated, or using weak/default credential.

**Jika port closed externally:** cek cloud security group, VPN exposure, bastion, private link, staging, and SSRF reachability in scope.

```text
Public port closed
→ cek staging SG
→ cek VPN route
→ cek admin UI
→ cek SSRF reachability
→ cek security group 0.0.0.0/0
```

**Typical impact:** High–Critical.

---

## 6.39 Admin console and management plane exposure

**Find Management Exposure:** cari control panel, CI/CD UI, Kubernetes dashboard, cloud console proxy, router, appliance, hypervisor, CMS admin, and monitoring console → valid jika management plane accessible publicly without proper auth, MFA, network restriction, or role separation.

**Jika login required:** cek default credentials, SSO misconfig, verbose login errors, no MFA, IP restriction bypass via proxy headers, and old path.

```text
Admin login ada
→ cek default credential
→ cek MFA required
→ cek IP allowlist
→ cek X-Forwarded-For trust
→ cek old admin route
```

**Typical impact:** High–Critical.

---

## 6.40 Container image and Docker configuration

**Find Container Misconfiguration:** audit Dockerfile, image layers, runtime flags, mounted volumes, exposed ports, user, capabilities, seccomp, AppArmor, secrets, and package manager cache → valid jika container runs as root unnecessarily, has privileged capability, exposes secret, or includes sensitive build artifact.

**Jika running container clean:** cek image history, intermediate layers, CI cache, base image defaults, and registry permissions.

```text
Runtime clean
→ cek image history
→ cek build args
→ cek intermediate layers
→ cek registry ACL
→ cek exposed ports
→ cek capabilities
```

**Typical impact:** Medium–Critical.

---

## 6.41 Kubernetes and orchestration misconfiguration

**Find K8s Misconfiguration:** audit manifests, Helm values, RBAC, service account, secrets, network policy, ingress, Pod Security, hostPath, hostNetwork, hostPID, privileged, capabilities, and admission controllers → valid jika pod/workload can escape isolation, access cluster secrets, or expose internal service.

Penekanan v3:

- `privileged: true`
- `hostNetwork: true`
- `hostPID: true`
- dangerous `hostPath`
- extra Linux capabilities
- default service account token mounted
- no NetworkPolicy
- Pod Security Standard not enforced
- public dashboard/metrics
- secret mounted broadly

```text
Ingress aman
→ cek service account
→ cek RBAC
→ cek hostPath
→ cek privileged
→ cek network policy
→ cek dashboard
→ cek metrics
```

**Typical impact:** High–Critical.

---

## 6.42 Service mesh and internal zero-trust misconfiguration

**Find Service Mesh Misconfiguration:** audit Istio/Linkerd/Consul/Envoy policy, mTLS mode, authorization policy, sidecar injection, egress policy, and plaintext fallback → valid jika service that should require mTLS/auth accepts plaintext or bypasses sidecar.

**Jika mesh says STRICT:** cek namespace override, workload exception, health port, admin port, direct pod IP, and egress bypass.

```text
Mesh strict global
→ cek namespace policy
→ cek workload exception
→ cek direct pod IP
→ cek health/admin port
→ cek sidecar injection
```

**Typical impact:** High–Critical.

---

## 6.43 Network ACL, firewall, and security group misconfiguration

**Find Network Misconfiguration:** audit exposed ports, security groups, firewall, NACL, Kubernetes ingress, database ACL, VPN routes, and zero-trust policies → valid jika internal service is internet-exposed or broad source can reach sensitive port.

**Jika external scanner clean:** cek IPv6, alternate interface, cloud region, staging, temporary rule, and firewall rule shadowing.

```text
IPv4 clean
→ cek IPv6
→ cek region lain
→ cek staging
→ cek temporary SG
→ cek internal route
→ cek public IP on DB
```

**Typical impact:** Medium–Critical.

---

## 6.44 Webhook and callback signature misconfiguration

**Find Webhook Misconfiguration:** identify inbound webhook/callback endpoints → cek authentication, HMAC signature, timestamp, replay protection, secret rotation, IP allowlist, mTLS, rate limit, schema validation, and error handling → valid jika arbitrary sender can trigger business action or replay old event.

Penekanan v3:

- Signature header must be verified.
- Verification must not be optional.
- Use timestamp and replay window.
- Store processed event ID to prevent duplicate processing.
- Shared secret must not be default/hardcoded.
- Use constant-time comparison for signatures.
- Rate limit webhook endpoint.
- Do not leak verbose error.

```text
Signature exists
→ cek verification required
→ cek timestamp window
→ cek replay duplicate
→ cek secret rotation
→ cek IP allowlist
→ cek error response
```

**Typical impact:** Medium–Critical.

---

## 6.45 Observability, logging, tracing, and analytics misconfiguration

**Find Observability Leak:** audit logs, traces, metrics, APM, SIEM, Sentry, Bugsnag, OpenTelemetry, analytics, and error events → valid jika token, PII, secrets, query strings, authorization headers, environment variables, or internal data are logged or exported to wrong sink.

**Jika application logs redacted:** cek trace spans, error screenshots, replay tools, analytics events, request bodies, and third-party destinations.

```text
Logs redacted
→ cek traces
→ cek metrics labels
→ cek error event
→ cek session replay
→ cek analytics payload
→ cek SIEM export
```

**Typical impact:** Medium–High.

---

## 6.46 CI/CD pipeline and runner misconfiguration

**Find CI/CD Misconfiguration:** audit GitHub Actions, GitLab CI, Jenkins, CircleCI, Buildkite, ArgoCD, Flux, runner, token, environment protection, branch protection, artifact, and secret handling → valid if untrusted code can access secret, deploy to protected env, modify pipeline, or assume cloud role.

**Jika main protected:** cek pull_request vs pull_request_target, fork workflow, wildcard OIDC subject, environment approval bypass, self-hosted runner exposure, and artifact leak.

```text
Main protected
→ cek fork workflow
→ cek pull_request_target
→ cek OIDC trust
→ cek environment approval
→ cek self-hosted runner
→ cek artifact secrets
```

**Typical impact:** High–Critical.

---

## 6.47 Infrastructure-as-Code drift and policy-as-code gap

**Find IaC Drift:** compare Terraform/CloudFormation/Pulumi/Kubernetes manifests with deployed resources → valid if actual resources are weaker than code baseline or security policy does not gate deployment.

**Jika IaC passes scanner:** cek manual console changes, ignored resources, imported resources, provider defaults, drift detection, and emergency exceptions.

```text
IaC scan pass
→ cek cloud actual state
→ cek manual changes
→ cek ignored resources
→ cek provider default
→ cek exception list
```

**Typical impact:** Medium–High.

---

## 6.48 Cross-tenant shared resource and shared key misconfiguration

**Find Cross-Tenant Config Failure:** audit cache key, storage prefix, encryption keys, JWT signing keys, DB schema, queue, topic, Redis key, and analytics/log partitioning → valid if tenant A can affect or read tenant B due to shared config without tenant isolation.

Cek:

- cache key without tenant prefix
- S3 prefix without tenant ACL
- same encryption key for high-risk tenants
- same JWT signing key across unrelated trust domains
- queue/topic shared without tenant filter
- log/analytics table not tenant-isolated

```text
API enforces tenant
→ cek cache key
→ cek storage prefix
→ cek queue topic
→ cek encryption key scope
→ cek log partition
→ cek analytics export
```

**Typical impact:** High–Critical.

---

## 6.49 Feature flags, dark-launch paths, and experimental features

**Find Feature Flag Misconfiguration:** read JS bundle, config endpoint, remote feature flag, A/B test, entitlement, and rollout rule → valid if hidden feature is accessible without correct backend enforcement or experimental path exposes sensitive function.

**Jika UI hides feature:** cek backend endpoint, mobile API, flag endpoint, old route, and entitlement in client.

```text
Flag off in UI
→ cek API request from enabled user
→ replay with disabled user
→ cek flag config endpoint
→ cek mobile API
→ cek old route
```

**Typical impact:** Medium–High.

---

## 6.50 Mobile/client build configuration exposure

**Find Client Build Misconfiguration:** audit mobile app, desktop app, browser extension, JS bundle, source maps, API base URLs, feature flags, test keys, and debug build flags → valid if production client includes debug endpoint, secret, internal host, or staging token.

**Jika production app clean:** cek old versions, beta builds, source maps, crash logs, and app store artifacts.

```text
Current build clean
→ cek old build
→ cek beta build
→ cek source map
→ cek crash report
→ cek embedded API host
```

**Typical impact:** Low–High.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek bucket prefix, CDN cache key, tenant header, org_id di object path, shared KMS key,
  shared GraphQL schema, shared search index, and shared logging pipeline.

API v1/mobile:
→ cari config lama yang tidak punya header/cookie/CORS hardening baru, session lifecycle baru,
  mTLS enforcement, rate limit, or GraphQL depth control.

GraphQL:
→ cek introspection, GraphiQL, playground, verbose resolver error, field suggestion,
  query depth/complexity, batching, and auth middleware bypass.

CDN/cache:
→ cek Vary, Cache-Control, stale response, cache deception, origin bypass,
  304 behavior, personalized response public, and cache poisoning precondition.

CI/CD:
→ cek exposed build logs, artifacts, preview env, deployment status, runner metadata,
  public workflow logs, and secret masking gap.

OAuth/OIDC/SAML:
→ cek redirect/callback config, test IdP, weak allowlist, verbose SAML/OIDC errors,
  signature/encryption mode, session binding, and metadata endpoint exposure.

Webhook/worker async:
→ cek webhook test panel, job retry, queue dashboard, callback logs, signature config,
  timeout handling, and worker-only endpoint exposure.

Parser/proxy mismatch:
→ cek proxy blocks path A but backend serves encoded/cased/suffixed variant,
  request smuggling, method override, WebDAV method, and host/origin mismatch.

Cloud/control plane:
→ cek IAM trust wildcard, over-permissioned role, public function URL, IMDS exposure,
  security group drift, and resource created outside IaC.

Client build:
→ cek source map, debug flag, staging token, internal host, feature flag endpoint,
  old mobile build, browser extension config, and crash analytics leak.
```

---

# Cross-reference matrix

| Pattern | Often chains with |
|---|---|
| TLS weak config | A04, session theft |
| DNS takeover | A01, A05, A07 |
| IAM trust wildcard | A01, A03, A08 |
| SPF/DKIM/DMARC | phishing, A07 |
| GraphQL tooling | A01, A05, DoS |
| Rate limit gap | A07, abuse flow |
| Session lifecycle | A07, A01 |
| Request smuggling | A01, cache, auth bypass |
| Secrets exposure | A03, A04, cloud takeover |
| CI/CD misconfig | A03, A08 |
| Cache misconfig | A01, data exposure |
| XXE | SSRF, file read |

---

## POC Evidence Checklist

Untuk setiap temuan A02, report sebaiknya menjawab:

1. **Apa konfigurasi yang salah?** Jelaskan layer: web server, framework, cloud, DNS, IdP, CI/CD, container, proxy, cache, atau client.
2. **Apa baseline yang seharusnya?** Sertakan expected secure state.
3. **Apa bukti aman?** Screenshot, response header, config snippet redacted, DNS record, policy snippet, atau log sanitized.
4. **Apa impact langsung?** Data exposure, auth bypass, credential compromise, phishing, privilege escalation, or control plane access.
5. **Apa chain realistis?** Misalnya DNS takeover → cookie theft, verbose error → exploit version, IAM role → cloud data access.
6. **Apa scope affected?** Domain, environment, tenant, region, API, role, or service.
7. **Apa remediation?** Specific setting, config change, policy, guardrail, or automated check.
8. **Apa regression test?** Header test, IaC policy, CI check, DNS audit, GraphQL schema check, TLS scan, or role policy test.

Minimum evidence:

```text
→ exact asset, environment, and layer
→ expected secure baseline
→ observed misconfiguration
→ request/response, header, DNS record, policy snippet, screenshot, or sanitized log
→ proof of impact or realistic chain
→ why validation stayed inside authorized scope
```

---

## Retest Checklist

```text
→ debug off and generic errors in production
→ default/sample/admin surfaces removed or protected
→ security headers, cookie flags, HSTS, TLS, and CORS match baseline
→ buckets/object storage private, non-listable, and bound to intended identity/tenant
→ cloud IAM trust policy and permission scope least-privilege
→ DNS records have no dangling takeover target
→ OAuth/OIDC/SAML callbacks, signatures, audience, issuer, and session binding validated
→ GraphQL tooling disabled or protected, and depth/complexity limits enforced
→ CDN/origin/cache cannot bypass auth or leak personalized responses
→ CI/CD logs/artifacts/runners no longer expose secrets or privileged paths
→ IaC/policy-as-code detects drift and blocks unsafe resources
→ logs/source maps/backups/config files are not web-accessible
```

---

# Remediation themes

```text
Default deny:
aktifkan hanya fitur yang dibutuhkan.

Automate baseline:
gunakan IaC, policy-as-code, and continuous drift detection.

Separate environments:
prod, staging, dev harus punya credential dan exposure berbeda.

Secure by layer:
fix di backend/origin, bukan hanya UI, WAF, atau CDN.

Short-lived credentials:
gunakan federation, managed identity, and secret rotation.

Least privilege:
cloud role, token scope, API key, tenant resource, and service account.

Defense in depth:
headers, cookies, TLS, CSRF, rate limit, logging, and monitoring.

Continuous validation:
misconfiguration muncul karena drift; testing harus berulang.
```

---

# Real-World Bug Bounty Insight Appendix

## A. Staging Environment With Production Data

**Pattern:** production sudah harden, tetapi staging/preview masih memakai data production, debug aktif, atau auth lebih lemah.

```text
Find:
petakan subdomain staging/dev/preview →
bandingkan header, auth, error, data, dan robots/indexing →
gunakan akun tester →
valid bila data/fungsi production terlihat di environment yang lebih lemah.
```

**Lesson:** A02 sering muncul dari environment drift, bukan dari domain utama.

---

## B. CDN Origin Bypass

**Pattern:** WAF/CDN melindungi domain utama, tetapi origin host/IP/alternate hostname tetap public dan melayani request langsung.

```text
Find:
fingerprint CDN →
cari origin dari DNS history, cert, error, source map, atau asset host →
bandingkan behavior domain utama vs origin →
valid bila origin membuka data/fungsi yang edge block.
```

**Lesson:** security control harus enforced di backend/origin, bukan hanya di edge.

---

## C. IAM Trust Wildcard

**Pattern:** cloud role trust policy terlalu longgar sehingga principal/account/service yang tidak semestinya bisa assume role.

```text
Find:
review policy snippet yang exposed atau in-scope →
cek wildcard Principal, missing ExternalId, broad condition, and over-permissioned role →
valid bila trust boundary cloud dapat dilewati.
```

**Lesson:** cloud IAM misconfiguration bisa berubah dari A02 menjadi A01/A03/A08 chain.

---

## D. GraphQL Tooling in Production

**Pattern:** GraphiQL/playground/introspection/verbose resolver error aktif di production.

```text
Find:
cek /graphql, /graphiql, /playground, schema docs, and error response →
bandingkan auth vs unauth →
valid bila schema, mutation sensitif, internal type, or resolver error bocor.
```

**Lesson:** tooling bukan bug sendiri jika public by design, tetapi valid bila memperluas attack surface atau membuka sensitive implementation detail.

---

## E. Email Authentication Gap

**Pattern:** SPF/DKIM/DMARC lemah pada domain yang dipakai untuk login, reset password, invite, billing, atau support.

```text
Find:
cek SPF/DKIM/DMARC/BIMI record →
lihat domain dipakai untuk flow high-trust →
valid bila spoofing realistis memperkuat phishing/account recovery chain.
```

**Lesson:** severity naik bila domain email punya trust kuat dalam auth atau payment flow.

---

## F. CI/CD Artifact Leak

**Pattern:** build logs, artifacts, source maps, crash reports, atau preview deployments public.

```text
Find:
cari public workflow/log/artifact/source map →
cek secret redaction, env var, internal host, package token, and deploy path →
valid bila data sensitif atau supply-chain path exposed.
```

**Lesson:** A02 pada pipeline sering menjadi entry point ke A03 atau A08.

---

# Quick template

```text
Find A02:
petakan konfigurasi yang menentukan exposure, authentication, authorization, transport,
resource boundary, logging, cache, DNS, cloud, pipeline, dan runtime →
buat secure baseline → bandingkan semua environment →
valid jika konfigurasi membuat data/fungsi/credential/internal service/trust boundary terekspos.

Jika hasil awal aman:
cek edge vs origin, prod vs staging, API vs UI, old route, CDN cache, DNS stale record,
IAM trust, OAuth/SAML config, session lifecycle, GraphQL schema, container image layer,
CI/CD artifact, and IaC drift.
```

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A02 harus dipakai sebagai configuration graph, bukan checklist header statis.

## Recent Bypass Branches

- **Service-specific misconfig:** setelah recon teknologi, gunakan checklist per produk: Jenkins/GitLab/Atlassian/Grafana, cloud storage, CDN, SSO app, GraphQL playground, K8s, object bucket, dan monitoring console.
- **Subdomain takeover POC:** buktikan kontrol dengan hidden path dan marker aman. Jangan deface index. Chain hanya bila program mengizinkan: cookie domain scope, OAuth redirect trust, CORS trust, email link trust, atau SSO callback.
- **Cache/CDN config:** cek private response cache, static extension confusion, origin bypass, path normalization, `Vary`/cookie key, host header routing, dan stale response dari user tester.
- **GraphQL production config:** cek introspection, suggestions, playground, missing depth/complexity limit, permissive CORS, and CSRF-compatible content types. Jangan melakukan batch/alias test yang berisiko DoS.
- **Environment drift:** staging/dev sering punya debug mode, weaker auth, production-like data, old OAuth app, exposed source maps, dan artifact lama.
- **AI/MCP/RAG service config:** cek endpoint model gateway, MCP server, vector DB, prompt/debug trace, agent dashboard, plugin marketplace, dan tool callback sebagai service config baru. Valid jika ada unauth exposure, permissive CORS, weak connector scope, leaked prompt/tool trace, atau environment dev yang memegang data produksi. POC cukup metadata, tester account, dan redaksi ketat.

## Evidence Upgrade

Untuk misconfig, report harus menjelaskan **config yang salah + service yang terpengaruh + impact path**. Screenshot header saja biasanya lemah; tunjukkan data/control boundary yang berubah tanpa mengganggu sistem.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **SaaS-specific misconfig:** tambahkan checklist untuk Salesforce, ServiceNow, Oracle Identity, Entra, cloud project, CDN-managed path, Chrome extension, and newly acquired assets.
- **Browser header bypass:** XFO/CSP/CORS/clickjacking tidak cukup dicek dengan header; uji framing context, sandboxed iframe, opener/referrer behavior, cross-origin isolation, dan credentialed API side effect.
- **CDN/origin drift:** treat CDN edge, CDN-CGI/managed paths, cache key, origin fallback, and stale asset as separate deployment configs.
- **Acquisition drift:** aset baru akuisisi sering punya baseline berbeda: staging, old IdP app, unowned repo, old CI job, and forgotten service account.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Subdomain takeover ecosystem:** dangling DNS harus dipetakan ke provider state, cookie scope, OAuth callback, CORS trust, SaaS tenant, dan brand trust.
- **Mobile hardening config:** cek WebView setting, exported component, deep link verification, backup/debuggable flag, storage mode, dan hardcoded endpoint.
- **Stale SaaS/cloud records:** old callback, forgotten service, stale CNAME, orphaned domain, dan old project sering menjadi entry point setelah product drift.

## Source Notes

- OWASP Top 10:2025 A02 — Security Misconfiguration.
- OWASP WSTG Configuration and Deployment Management Testing.
- OWASP Transport Layer Security Cheat Sheet.
- OWASP WSTG Testing for Weak Transport Layer Security.
- OWASP Subdomain Takeover Prevention Cheat Sheet.
- OWASP WSTG Test for Subdomain Takeover.
- OWASP GraphQL Cheat Sheet and WSTG GraphQL Testing.
- OWASP Session Management Cheat Sheet.
- OWASP WSTG HTTP Request Smuggling.
- OWASP Information Exposure Through Query Strings in URL.
- AWS IAM policy documentation and cloud IAM trust policy research.
- Public security research on SPF, DKIM, DMARC, request smuggling, and GraphQL production hardening.

### Source links

- [OWASP Top 10:2025 — A02 Security Misconfiguration](https://owasp.org/Top10/2025/A02_2025-Security_Misconfiguration/)
- [OWASP Top 10:2025 — Introduction](https://owasp.org/Top10/2025/0x00_2025-Introduction/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OWASP Transport Layer Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html)
- [OWASP WSTG — Testing for Weak Transport Layer Security](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/01-Testing_for_Weak_Transport_Layer_Security)
- [OWASP Subdomain Takeover Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Subdomain_Takeover_Prevention_Cheat_Sheet.html)
- [OWASP WSTG — Test for Subdomain Takeover](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/10-Test_for_Subdomain_Takeover)
- [OWASP GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [OWASP WSTG — Testing GraphQL](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/12-API_Testing/99-Testing_GraphQL)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP WSTG — HTTP Request Smuggling](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/16-Testing_for_HTTP_Request_Smuggling)
- [OWASP — Information Exposure Through Query Strings in URL](https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings_in_url)
- [AWS IAM Principal element documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html)
- [Hacking the Cloud — Misconfigured Role Trust Policy Wildcard Principal](https://hackingthe.cloud/aws/exploitation/Misconfigured_Resource-Based_Policies/misconfigured_iam_role_trust_policy_wildcard_principal/)
- [Token Security — IAM Role Trust Policies Misconfigurations](https://www.token.security/blog/iam-role-trust-policies-misconfigurations-hiding-in-plain-sight)
- [SecurityScorecard — SPF Soft Fail](https://support.securityscorecard.com/hc/en-us/articles/115003319223-SPF-Record-Contains-a-Soft-Fail)
- [SecurityScorecard — Malformed SPF Record](https://support.securityscorecard.com/hc/en-us/articles/115003337866-Malformed-SPF-Record)
- [PortSwigger — HTTP Request Smuggling](https://portswigger.net/web-security/request-smuggling)
- [PortSwigger — Information Disclosure](https://portswigger.net/web-security/information-disclosure)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [Wiz — GraphQL API Security Risks](https://www.wiz.io/academy/api-security/graphql-api-security-risks)
