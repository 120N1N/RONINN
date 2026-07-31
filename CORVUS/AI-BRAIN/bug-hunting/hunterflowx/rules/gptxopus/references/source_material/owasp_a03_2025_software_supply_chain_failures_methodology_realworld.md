# OWASP A03:2025 Software Supply Chain Failures — Methodology v3 Deep Real-World Bug Bounty Edition

> Gunakan metodologi ini hanya pada aset, program, atau lingkungan yang memang berada dalam scope pengujian sah. Fokus dokumen ini adalah alur pikir testing, validasi impact, dan pelaporan kuat; bukan menyerang sistem tanpa izin. Semua contoh POC dibingkai agar aman, non-destruktif, dan memakai akun/data tester.

## Ringkasan Revisi v3 Deep

Versi ini mengikuti format A01: cluster navigation, universal testing logic, decision tree, pattern metodologi, real-world appendix, severity heuristic, evidence checklist, retest checklist, dan source notes. Fokusnya dibuat lebih nyata untuk bug bounty modern: API, mobile, GraphQL, cloud, CI/CD, CDN/cache, OAuth/webhook, worker async, parser mismatch, multi-tenant, dan reportability.

Tambahan paling penting:

- **SBOM-to-impact workflow** mapping dependency dari manifest, lockfile, source map, container layer, dan artifact ke runtime reachability.
- **Dependency confusion without unsafe publishing** validasi dengan registry config, namespace ownership, dan build log, bukan upload package berbahaya.
- **CI/CD trust boundary** pull_request_target, untrusted artifacts, build logs, runner secret, and deployment privilege.
- **Artifact integrity** signature, digest pinning, SLSA/provenance, mutable tag, and unsigned update channel.
- **Real-world triage** membedakan dependency noise dari reachable exploit path yang bisa dibayar bug bounty.

---

## Core Rule A03

A03 valid bila aplikasi, pipeline, dependency, artifact, package, registry, update channel, CI/CD workflow, third-party script, plugin, atau build provenance mempercayai komponen yang rentan, tidak terverifikasi, tidak terdokumentasi, tidak updateable, atau berasal dari trust boundary yang bisa disalahgunakan.

---

## Attack Surface Mapping

```text
Mapping A03:
→ ecosystem: npm, PyPI, Maven, Go, Composer, RubyGems, Docker, GitHub Actions, CDN script
→ dependency: direct, transitive, devDependency, optional, plugin, extension, SDK, third-party JS
→ build path: source repo, CI runner, package registry, artifact store, container registry, deploy pipeline
→ trust proof: lockfile, checksum, digest, signature, provenance, SBOM, private registry policy
→ actor: public contributor, fork PR, maintainer, tenant plugin author, compromised package, build worker
→ impact path: secret leak, RCE dependency, account takeover, poisoned artifact, malicious update, cloud deploy takeover
```

**Risk matrix awal:**

| Signal | Kenapa penting |
|---|---|
| Internal package name exposed | dependency confusion or namespace squatting risk |
| Public CI logs/artifacts | secrets, source, and deploy path often leak here |
| Mutable artifact tag | production may pull unreviewed code |
| Unsigned update | client or server accepts attacker-controlled software |
| Reachable critical CVE | reportability depends on runtime path, not only version |
| Third-party JS on auth page | script inherits user session context |

---

## Cluster Navigation

| Cluster | Pattern | Focus |
|---|---|---|
| Inventory and reachability | 1-7 | SBOM, lockfile, vulnerable dependency, stale component |
| Package trust | 8-14 | dependency confusion, typosquatting, maintainer risk |
| CI/CD and artifact | 15-24 | workflow, runner, artifact, provenance, registry |
| Client/update/plugin | 25-31 | CDN script, plugin, auto-update, SDK |
| Reporting and triage | 32-36 | severity, evidence, retest, false positive control |

---

## Universal Testing Logic

```text
Find A03:
collect manifests, lockfiles, SBOM, source maps, container metadata, and public build evidence →
map dependency to runtime/build-time/dev-only reachability →
identify trust boundary where external package/artifact/code can influence build or runtime →
validate with non-destructive evidence: version proof, config proof, reachable feature, or safe test account →
connect component failure to confidentiality, integrity, availability, or deploy-chain impact →
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

> Untuk A03, bypass berarti mencari jalur trust lain ketika satu bukti supply-chain terlihat tidak reachable. Jangan publish package, jangan mengubah artifact target, dan jangan menjalankan malicious code kecuali program memberi izin eksplisit.

## A03 Bypass Matrix

| Kondisi awal | Coba variasi aman | Tujuan validasi |
|---|---|---|
| Dependency vulnerable dianggap dev-only | container layer, serverless bundle, source map, build script, test endpoint, admin tooling | cek apakah sebenarnya masuk runtime/build privileged |
| CVE tidak reachable di UI | API v1/mobile, import/export/parser, worker async, admin report, webhook payload | temukan sink yang memakai library vulnerable |
| Dependency confusion tidak boleh diuji publish | registry config, package name ownership, lockfile, build log, `.npmrc`, namespace reservation | bukti risk tanpa membuat package berbahaya |
| CI workflow tampak aman | artifact boundary, cache restore, matrix job, self-hosted runner, PR metadata, release job | cek untrusted input masuk job privileged |
| Artifact signed | cek apa yang ditandatangani: binary, manifest, URL, version, channel, digest | pastikan signature menutup object yang dipakai deploy/update |
| Container tag pinned | cek base image, multi-stage copy, runtime download, init script, helm chart | cari mutable component lain |
| Third-party JS unavoidable | SRI, CSP, auth page context, token access, subresource pinning, self-hosted fallback | cek script supply-chain blast radius |
| SBOM terlihat lengkap | transitive deps, container packages, browser CDN scripts, vendored code, generated code | cari blind spot inventory |
| Private registry ada | public fallback, scope typo, unscoped package, token leak, read/write permission | cek trust boundary registry |
| Update channel aman | downgrade, replay manifest, old channel, beta channel, plugin updater, CDN cache | cek integrity lifecycle |

## A03 Chaining Playbook

```text
Dependency inventory leak →
reachable parser/package CVE →
safe input proof →
data/RCE/business impact.

Internal package name leak →
registry fallback proof →
dependency confusion risk →
CI/build context privilege →
deploy or secret impact.

Public CI artifact/log →
token/source/provenance leak →
registry/cloud/package access →
A04 key compromise or A08 artifact integrity failure.

Third-party JS on auth page →
no SRI/CSP pin →
script compromise scenario →
session/API/PII access impact.
```

**Rule chaining:** A03 report harus membedakan scanner noise dari trust boundary yang benar-benar bisa memengaruhi build/runtime.

---

# Methodology Patterns

## 1. Dependency Inventory Exposure

**Find Dependency Inventory Exposure:** cari `package.json`, lockfile, SBOM, source map, Docker layer, build log, or artifact yang membocorkan dependency dan internal namespace.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** inventory mengungkap vulnerable reachable package, private package name, registry config, or deploy path.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 2. Reachable Known Vulnerable Dependency

**Find Reachable Known Vulnerable Dependency:** identifikasi vulnerable version lalu cari route/feature yang benar-benar memakai library tersebut.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** vulnerable code path reachable dari input user atau high-value workflow.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 3. Transitive Dependency Blind Spot

**Find Transitive Dependency Blind Spot:** dari lockfile/SBOM, cari transitive package vulnerable yang dipanggil oleh direct dependency.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** direct dependency memanggil vulnerable API and user input reaches it.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 4. Dev Dependency Used in Production

**Find Dev Dependency Used in Production:** cek devDependency/test tool yang ikut dibundle ke runtime, container, serverless, or static app.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** dev tool exposes debug server, compiler, source map, or vulnerable parser in production.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 5. Abandoned / Archived Component

**Find Abandoned / Archived Component:** cari repo archived, deprecated package, no release, or unmaintained security issue.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** component protects sensitive path or has known unfixed vulnerability.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 6. Backported Fix Ambiguity

**Find Backported Fix Ambiguity:** ketika scanner bilang vulnerable, cek apakah vendor backport fix tanpa version bump.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** valid bila tidak ada bukti backport and affected behavior reachable.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 7. Runtime vs Build-Time Reachability

**Find Runtime vs Build-Time Reachability:** bedakan package yang hanya build-time dari package runtime.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** build-time bug tetap valid bila untrusted input reaches CI/build or artifact creation.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 8. Dependency Confusion

**Find Dependency Confusion:** cari internal package name yang tidak scoped/reserved dan registry config fallback ke public.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** build can resolve attacker-controlled public package name; proof cukup dari config/log tanpa publishing.

**Typical impact:** High-Critical bila mencapai build/deploy/release/secret path.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 9. Namespace / Scope Takeover

**Find Namespace / Scope Takeover:** cek npm scope, PyPI org, GitHub package namespace, container org yang tidak diklaim.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker can claim namespace used by target docs/build config.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 10. Typosquatting / Slopsquatting

**Find Typosquatting / Slopsquatting:** cari package mirip populer, LLM-hallucinated package, suspicious maintainer, install script, low download.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** target uses wrong or untrusted package in build/runtime.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 11. Maintainer Account Risk

**Find Maintainer Account Risk:** cek package critical dengan maintainer abandoned/single maintainer and takeover signal.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** stronger bila package controls auth, crypto, build, parser, or update path.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 12. Malicious Install Script Exposure

**Find Malicious Install Script Exposure:** identifikasi `preinstall`, `postinstall`, `prepare`, native build, dynamic binary download.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** install script executes in CI/developer/build context with meaningful token/file access.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 13. Private Registry Token Leak

**Find Private Registry Token Leak:** cari `.npmrc`, pip config, Maven settings, Docker auth, package registry token di logs/artifacts.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** token can read/write private package or influence dependency supply chain.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 14. Unpinned Dependency Version

**Find Unpinned Dependency Version:** cek wildcard/range/latest dependency in high-risk build.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** build output can change without review and affects production/runtime.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 15. GitHub Actions pull_request_target Misuse

**Find GitHub Actions pull_request_target Misuse:** workflow privileged menjalankan code atau artifact dari fork/untrusted PR.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** untrusted contributor can influence job with secrets/write token.

**Typical impact:** High-Critical bila mencapai build/deploy/release/secret path.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 16. Untrusted Artifact Promotion

**Find Untrusted Artifact Promotion:** cek workflow yang download artifact dari PR lalu deploy/sign/release pada job privileged.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** artifact crossing trust boundary reaches deploy/release.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 17. Build Log Secret Exposure

**Find Build Log Secret Exposure:** cek public CI logs for env vars, tokens, registry URL, cloud keys, signing data.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** secret or sensitive deploy path visible.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 18. Self-Hosted Runner Exposure

**Find Self-Hosted Runner Exposure:** cek runner labels, workspace reuse, artifact cache, secret persistence.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** untrusted job can read residue or influence later privileged job.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 19. Workflow Command Injection

**Find Workflow Command Injection:** input issue title, branch, tag, artifact name, commit message, package version masuk shell.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** untrusted text influences shell/build command in CI.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 20. Over-Privileged CI Token

**Find Over-Privileged CI Token:** cek `GITHUB_TOKEN`/cloud role/deploy key used outside least privilege.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** workflow compromise would write repo, packages, release, cloud, or prod.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 21. Unsigned Build Artifact

**Find Unsigned Build Artifact:** release binary/container/package served without signature/checksum/provenance.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** consumer or deploy pipeline cannot verify artifact origin/integrity.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 22. Mutable Container Tag

**Find Mutable Container Tag:** deployment pulls `latest` or unpinned tag from registry.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker with registry influence or compromised tag can alter production image.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 23. Container Base Image Drift

**Find Container Base Image Drift:** Dockerfile uses old/unpinned base image with high CVE or mutable tag.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** base image vulnerability reachable or breaks supply-chain reproducibility.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 24. Artifact Store Public Exposure

**Find Artifact Store Public Exposure:** S3/GCS/Azure/artifact bucket exposes builds, symbols, source, SBOM, or package.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** private code, secrets, or deploy artifacts downloadable.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 25. Third-Party CDN Script Without Integrity

**Find Third-Party CDN Script Without Integrity:** authenticated page loads external JS without SRI/CSP or pinning.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** script can read DOM/session context or call authenticated API.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 26. Compromised SDK / Analytics Script Risk

**Find Compromised SDK / Analytics Script Risk:** third-party SDK has broad token/user data access on sensitive pages.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** SDK compromise would expose PII/session/action capability.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 27. Plugin / Extension Marketplace Trust Failure

**Find Plugin / Extension Marketplace Trust Failure:** tenant/admin can install plugin/theme/connector from unverified source.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** plugin executes with higher privilege or cross-tenant access.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 28. Auto-Update Manifest Tamper

**Find Auto-Update Manifest Tamper:** desktop/mobile/agent/plugin checks update manifest without signature or anti-downgrade.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** update path can install malicious/old vulnerable artifact in scope.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 29. SBOM Missing Critical Runtime Layer

**Find SBOM Missing Critical Runtime Layer:** SBOM omits transitive/container/browser/CDN dependency.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** hidden component has high-risk vulnerability and is used in production.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 30. Package Lockfile Missing

**Find Package Lockfile Missing:** repo/deploy builds without lockfile or ignores lockfile.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** build resolves dependency versions unpredictably.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 31. Internal Mirror Bypass

**Find Internal Mirror Bypass:** registry config intended to use mirror but falls back to public internet.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker-controlled package can be preferred or mixed with trusted packages.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 32. Release Signing Key Exposure

**Find Release Signing Key Exposure:** signing key, npm token, Docker token, mobile signing material leaks.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** attacker can publish trusted artifact.

**Typical impact:** High-Critical bila mencapai build/deploy/release/secret path.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 33. SLSA / Provenance Gap

**Find SLSA / Provenance Gap:** release claims official but no attestation tying artifact to source/build.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** high-risk artifact cannot be traced or verified.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 34. Vendored Dependency Drift

**Find Vendored Dependency Drift:** copied library in repo not tracked by package manager or scanner.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** known vulnerable code remains hidden from SCA.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 35. Generated Code / Codegen Trust Failure

**Find Generated Code / Codegen Trust Failure:** OpenAPI/GraphQL/protobuf codegen pulls remote schema or plugin unsafely.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** untrusted schema/plugin influences generated runtime code.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

## 36. Reportability Filter

**Find Reportability Filter:** for each finding, prove not only CVE/package name but exploit path, affected asset, and safe impact.

**Jika tidak langsung valid:**

```text
→ cek surface alternatif: API v1/mobile/GraphQL/bulk/export/import/async worker
→ ubah satu variabel pada satu waktu: role, object, tenant, state, method, content-type, header
→ bandingkan response, side effect, audit log, job status, dan cache behavior
→ gunakan akun/data tester dan berhenti sebelum destructive impact
```

**Valid bila:** finding meets bug bounty impact threshold rather than scanner noise.

**Typical impact:** Medium-High tergantung sensitivitas data, privilege, blast radius, dan chain realistis.

**Mitigation angle:** pin trusted dependencies, reserve namespaces, isolate CI trust levels, sign artifacts, enforce provenance/SBOM, and monitor package risk.

---

# Advanced Bug Bounty Branches

```text
Multi-tenant:
→ cek tenant_id/org_id/workspace_id yang dipakai supply-chain trust
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
→ inventory exposure tanpa sensitive package or exploit path
→ outdated dev-only dependency tanpa reachability

Medium:
→ reachable medium CVE or internal package namespace exposure
→ public build metadata yang mempermudah attack chain

High:
→ reachable critical parser/RCE dependency
→ CI secret exposure
→ private artifact/source leak
→ untrusted artifact influences release

Critical:
→ dependency confusion path to production
→ signing/deploy token compromise
→ privileged CI workflow takeover
→ malicious update channel
```

---

## Bug Bounty POC Evidence Checklist

Agar temuan A03 tidak ditolak sebagai teori, laporan harus menunjukkan impact nyata.

```text
Minimum evidence:
→ component/package/artifact name and version
→ source evidence: manifest, lockfile, SBOM, build log, source map, repo, artifact
→ runtime/build-time reachability
→ trust boundary that can be influenced
→ non-destructive impact proof
→ fixed version or mitigation
→ statement that no malicious package/tampering was performed
```

**Jangan hanya laporkan:**

```text
→ scanner output without reachability
→ publishing package to prove dependency confusion without explicit permission
→ claiming critical for dev-only unreachable dependency
→ leaking secrets in report without redaction
```

---

## Retest Checklist

```text
Retest after fix:
→ dependency upgraded/removed or compensating control documented
→ private package namespaces reserved and scoped
→ registry resolution order locked to trusted source
→ CI untrusted inputs separated from secrets/write tokens
→ artifacts signed and pinned by digest/checksum
→ SBOM includes direct, transitive, container, and browser dependencies
→ build logs/artifacts scrubbed
→ update channel validates signature and prevents downgrade
```

---

# Real-World Bug Bounty Insight Appendix

## A. Dependency Confusion Without Unsafe Publication

**Pattern:** internal package name appears in public lockfile and registry fallback allows public resolution.

```text
Find:
→ collect package name from manifest/log
→ prove public namespace unclaimed
→ show registry config fallback
→ do not publish malicious package
```

**Lesson:** Bug bounty proof can be config-based; avoid creating real supply-chain risk.

---

## B. PR Artifact to Deploy Chain

**Pattern:** untrusted fork artifact is consumed by privileged deploy workflow.

```text
Find:
→ map workflow triggers
→ identify artifact upload/download boundary
→ show privileged job consumes untrusted output
→ prove with harmless artifact metadata if allowed
```

**Lesson:** The vulnerability is trust crossing, not the shell payload.

---

## C. Unsigned Update Manifest

**Pattern:** client or agent trusts update JSON from mutable endpoint.

```text
Find:
→ capture manifest
→ check signature/digest/downgrade rules
→ alter only tester-controlled endpoint if scope allows
→ show install decision would trust changed metadata
```

**Lesson:** Update integrity requires signature over artifact, version, channel, and rollback policy.

---

# Recent 2023-2026 Writeup Intelligence

Tambahan dari writeup/riset 2023-2026: A03 makin bergeser ke CI/CD, artifact trust, package identity, dan provenance.

## Recent Bypass Branches

- **Dependency confusion without malware:** cari package internal dari lockfile, source map, Docker layer, docs, CI log, dan error message. Proof cukup dengan ownership/namespace evidence atau package reservation jika program mengizinkan eksplisit.
- **GitHub Actions/GitLab CI trust boundary:** cek mutable action tag, unpinned third-party action, `pull_request_target`, broad `GITHUB_TOKEN` permission, artifact poisoning, cache poisoning, dan secret exposed to fork PR.
- **Maintainer/package takeover:** cari abandoned package, expired maintainer domain/email, stale org namespace, missing 2FA signal, package transfer risk, typo/slopsquatting candidate, dan registry ownership drift.
- **Artifact provenance:** cek apakah release binary/container punya signature, digest, SBOM, SLSA attestation, reproducible build signal, dan rollback protection.
- **CDN script supply chain:** cek mutable third-party script, missing SRI, broad CSP allowlist, tag manager trust, abandoned vendor domain, and client-side package loaded from untrusted origin.

## Evidence Upgrade

Jangan menjalankan malware atau publish payload. Evidence yang aman: dependency path, CI config snippet, artifact metadata, package ownership proof, SBOM/SCA finding, dan skenario impact yang menjelaskan privileged build/distribution trust.

# Critical Thinking Podcast Addendum

Tambahan dari scan 124 post Critical Thinking:

- **Acquisition hunting:** recon perusahaan yang baru diakuisisi: domain, repo, CI, cloud project, staging, package namespace, and asset owner transition.
- **Orphaned commits/source maps:** gunakan untuk menemukan endpoint, package internal, route lama, secret candidate, and authorization assumption. Validasi aman dan redacted.
- **Report/research opsec:** jangan membocorkan full chain lebih dari yang dibutuhkan untuk triage awal; dokumentasikan root cause dan impact, simpan detail exploit yang sensitif sampai diminta.
- **CI/CD artifact trust:** source-to-sink juga berlaku untuk build pipeline: untrusted commit/artifact/cache -> privileged build/release/signing sink.

# TegalSec Blog Addendum

Tambahan dari scan TegalSec 2023-2026:

- **Persistent secrets:** token/API key/SSH key/OAuth token/certificate yang bocor harus diuji dari sisi lifetime, scope, rotation, dan audit tanpa unauthorized use.
- **AI information supply chain:** forum/support/community answer yang dirangkum AI dapat menjadi trust-source poisoning; cek canonical support channel dan monitoring.
- **Third-party trust anchor:** SaaS, CDN, analytics, customer support, CI/CD, dan mobile SDK harus masuk inventory supply chain.

# Source Notes

Sumber yang menginspirasi revisi ini:

- OWASP Top 10 2025 - A03 Software Supply Chain Failures: https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/
- OWASP Dependency Graph SBOM Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Dependency_Graph_SBOM_Cheat_Sheet.html
- GitHub Advisory Database: https://github.com/advisories
- Open Source Vulnerabilities database: https://osv.dev/
- SLSA framework: https://slsa.dev/
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- HackerOne Hacktivity and blog: https://www.hackerone.com/blog
- Intigriti Researcher Blog: https://www.intigriti.com/researchers/blog
- Critical Thinking Bug Bounty Podcast Blog: https://blog.criticalthinkingpodcast.io/
- PayloadsAllTheThings, adapted only for safe authorized testing: https://github.com/swisskyrepo/PayloadsAllTheThings
