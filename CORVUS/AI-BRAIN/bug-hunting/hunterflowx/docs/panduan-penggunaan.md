# Panduan Penggunaan Hunterflowx

Dokumen ini adalah manual operator untuk memakai workflow final dari awal
engagement sampai report. Tujuannya bukan hanya menjalankan tool, tetapi
memastikan semua aktivitas AI tercatat, bisa diaudit, dan punya bukti yang
layak sebelum disebut vulnerability.

Workflow ini hanya untuk bug bounty atau pentest yang sudah punya izin.

## 1. Konsep Utama

Workflow ini memakai prinsip:

```text
chat bukan bukti
event adalah state
evidence adalah dasar verdict
dashboard adalah visibility
judge adalah gate kualitas bukti
```

Artinya:

- AI boleh memberi hipotesis, tetapi hipotesis belum menjadi finding.
- Scanner boleh memberi sinyal, tetapi scanner output belum cukup untuk report.
- Source code boleh menunjukkan risk, tetapi source-only claim belum cukup.
- Endpoint dianggap sudah diuji hanya jika ada event dan evidence yang cocok.
- Finding baru layak dilaporkan jika sudah melewati evidence score, judge, dan
  fresh repro sesuai kebutuhan.

Alur dasar:

```text
init engagement
-> isi scope dan safety policy
-> recon / import / mapping
-> source review satu file per satu file
-> endpoint angle-plan
-> angle-exec lewat browser/Burp/Caido/http
-> evidence-score
-> judge
-> fresh-repro
-> report lifecycle
-> dashboard monitoring
```

## 2. Struktur Folder

Root workflow:

```text
/Users/raihan/BugBounty/worfklow/hunterflowx
```

Struktur penting:

```text
bin/bbf                         CLI utama
dashboard/                      UI dashboard static
docs/                           dokumentasi fitur
workflow/                       playbook metodologi
scripts/                        executor, verifier, scorer, dashboard server
templates/                      template engagement, report, source review
engagements/<program>/<target>/ workspace tiap target
```

Setelah membuat engagement, folder program akan berisi:

```text
engagements/<program>/docs/      dokumentasi program lintas target
engagements/<program>/rules/     scope, rules, rate limit, allowed accounts
engagements/<program>/notes/     catatan program lintas target
engagements/<program>/findings/  kumpulan finding lintas target
engagements/<program>/report/    laporan program-level atau rekap submit
engagements/<program>/evidence/  evidence lintas target bila perlu
```

Folder target tetap berisi detail teknis per target:

```text
data/events.jsonl               ledger semua event
data/graph_state.json           state dashboard
data/safety_policy.json         allowlist, rate limit, forbidden path
data/run_queue.json             queue Command Center
data/report_lifecycle.json      status report
scope.md                        scope target
notes/rules.md                  rules target atau turunan rules program
notes/recent-state.md           catatan state terakhir
source-file-queue.md            queue source review
source-reviews/                 bukti file source sudah dibaca
multi-angle-coverage.md         coverage angle per endpoint
test-ledger.md                  test yang sudah dilakukan
priority-testing-plan.md        endpoint prioritas
evidence/                       request/response, screenshot, review, judge
findings/                       candidate dan confirmed finding
reports/                        draft, submitted, archived
```

## 3. Syarat Minimal

Wajib:

```text
python3
browser lokal
akses ke target yang memang in-scope
aturan program bug bounty
akun test milik sendiri jika perlu authenticated testing
```

Opsional tetapi disarankan:

```text
Burp Suite atau Caido untuk request/response proof
Caido CLI untuk native workflow
Neo4j untuk graph exploration yang lebih luas
Playwright untuk browser transport
```

## 4. Membuat Engagement Baru

Jalankan dari root workflow:

```bash
cd /Users/raihan/BugBounty/worfklow/hunterflowx
bin/bbf init <program> <target>
```

Contoh:

```bash
bin/bbf init template example-api
bin/bbf init h1 acme
```

Masuk ke workspace engagement:

```bash
cd engagements/<program>/<target>
```

Contoh:

```bash
cd engagements/template/example-api
```

Dari dalam engagement, semua command memakai:

```bash
../../../bin/bbf <command>
```

## 5. Isi Scope, Rules, Dan Safety Policy

Sebelum live testing, isi file ini:

```text
scope.md
notes/rules.md
notes/recent-state.md
data/safety_policy.json
```

Minimal isi:

```text
in-scope host
out-of-scope host
allowed account
forbidden action
rate limit
allowed method
auth/session rule
testing window jika ada
data yang tidak boleh diubah
```

Cek safety policy:

```bash
../../../bin/bbf safety status
```

Default policy sengaja strict:

```json
{
  "mode": "enforce",
  "max_rps": 10,
  "allow_hosts": []
}
```

Isi `allow_hosts` sebelum active testing. Jika kosong, executor akan memblokir
request aktif.

Contoh policy:

```json
{
  "version": "1.0.0",
  "mode": "enforce",
  "max_rps": 10,
  "allow_hosts": ["api.target.example", "app.target.example"],
  "allow_schemes": ["https"],
  "allow_methods": ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH"],
  "forbidden_path_patterns": ["*/logout*", "*/delete-account*", "*/billing/charge*"],
  "active_testing_requires_approval": true,
  "notes": ["Owned accounts only. No destructive testing."]
}
```

## 6. Menjalankan Dashboard

Jalankan dari root workflow atau dari engagement:

```bash
../../../bin/bbf dashboard --port 5173
```

Jika sedang di root:

```bash
bin/bbf dashboard --port 5173
```

Buka:

```text
http://127.0.0.1:5173
```

Dashboard memakai satu port untuk banyak engagement. Pilih target dari selector
`Engagement`.

Halaman dashboard:

```text
/             Overview, evidence, findings, report, coverage
/neo4j        workspace graph luas
/command      run queue, Caido, safety, report lifecycle
```

## 7. Cara Membaca Dashboard

### Overview

Gunakan halaman utama untuk melihat:

```text
total endpoint
tested endpoint
planned angles
tested angles
evidence quality
judge result
source completeness
domain depth
risk priorities
findings dan reports
activity diagram
```

Dashboard menunjukkan state, bukan keputusan final. Kalau dashboard menunjukkan
ada evidence, tetap jalankan:

```bash
../../../bin/bbf evidence-score ...
../../../bin/bbf judge ...
```

### Neo4j Graph

Halaman `/neo4j` menampilkan chain:

```text
JS File -> API Route -> Param -> Auth Role -> Test Angle -> Chaining -> Evidence -> Finding
```

Gunakan untuk:

```text
melihat attack path yang belum lengkap
klik node untuk inspect detail
filter stage tertentu
mencari endpoint/angle/evidence
mengambil Cypher export
menentukan pivot berikutnya
```

### Command Center

Halaman `/command` dipakai untuk operasi:

```text
seed pipeline
run next safe task
approve active testing
run task tertentu
lihat Caido status
import history Caido/Burp
lihat safety policy
buat report draft
```

Active testing task harus di-approve sebelum dijalankan.

## 8. Event Ledger

Semua state penting harus menjadi event di:

```text
data/events.jsonl
```

Tambah event manual:

```bash
../../../bin/bbf event <event_type> --key value --key2 value2
```

Contoh endpoint ditemukan:

```bash
../../../bin/bbf event endpoint_discovered \
  --engagement template-example-api \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me \
  --source "Burp Proxy history #12"
```

Contoh source file dibaca:

```bash
../../../bin/bbf event source_file_read \
  --source-id src-login-controller \
  --source-file app/controllers/login.py \
  --review source-reviews/src-login-controller.md
```

Event penting:

```text
asset_added
endpoint_discovered
param_discovered
endpoint_seen_runtime
source_file_queued
source_file_read
source_flow_linked
attack_surface_mapped
endpoint_angle_planned
endpoint_angle_tested
creative_hypothesis_added
chain_candidate_added
evidence_added
evidence_reviewed
evidence_judged
verdict_set
finding_promoted
dead_end_recorded
pivot_decision
gap_found
blocked
```

Rebuild graph setelah event manual:

```bash
../../../bin/bbf build
```

## 9. Import Recon Framework

Jika sudah punya output dari `hunterweb/recon-framework`, import ke engagement:

```bash
../../../bin/bbf import-reconfw /path/to/reconfw/workspace
```

Dry-run dulu jika ingin melihat hasil tanpa menulis event:

```bash
../../../bin/bbf import-reconfw /path/to/reconfw/workspace --dry-run
```

Hasil import akan mengisi event seperti:

```text
asset_added
endpoint_discovered
param_discovered
endpoint_seen_runtime
```

Setelah import:

```bash
../../../bin/bbf build
../../../bin/bbf risk-prioritize --limit 25
```

## 10. Mapping Source Code

Jika ada source code, JS bundle, PHP, Python, config, template, atau file lain,
gunakan aturan satu file per satu file.

Alur wajib:

```text
queue file
-> baca satu file penuh
-> buat source review artifact
-> extract route, handler, role, query, sink, source
-> link source -> flow -> endpoint
-> map attack surface
-> buat angle-plan
-> baru lanjut file berikutnya
```

Queue file:

```bash
../../../bin/bbf event source_file_queued \
  --source-id src-login-controller \
  --source-file app/controllers/login.py
```

Buat review:

```text
source-reviews/src-login-controller.md
```

Isi minimal review:

```text
file path
hash atau timestamp jika ada
tujuan file
routes/handlers
auth role
input source
query/data store
external service
sink/security boundary
endpoint terkait
attack surface baru
angle yang harus diuji
```

Catat file sudah dibaca:

```bash
../../../bin/bbf event source_file_read \
  --source-id src-login-controller \
  --source-file app/controllers/login.py \
  --review source-reviews/src-login-controller.md
```

Hubungkan ke flow:

```bash
../../../bin/bbf event source_flow_linked \
  --source-id src-login-controller \
  --flow-id flow-login \
  --endpoint-id ep-post-login \
  --handler loginController
```

Map attack surface:

```bash
../../../bin/bbf event attack_surface_mapped \
  --endpoint-id ep-post-login \
  --surface-id surface-login-session \
  --surface "session and role transition boundary"
```

Verifikasi completeness:

```bash
../../../bin/bbf source-verify \
  --source-root /path/to/extracted/source \
  --queue-missing
```

Untuk semua file source-like:

```bash
../../../bin/bbf source-verify \
  --source-root /path/to/extracted/source \
  --all \
  --queue-missing
```

Strict mode untuk CI/manual gate:

```bash
../../../bin/bbf source-verify \
  --source-root /path/to/extracted/source \
  --strict
```

## 11. Multi-Angle Testing Endpoint

Jangan hanya test IDOR/A01. Endpoint penting harus diuji multi-angle.

Queue angle:

```bash
../../../bin/bbf angle-plan full \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me
```

Profile:

```text
core       angle minimal
deep       angle lebih luas
creative   hipotesis dan pivot kreatif
full       core + deep + creative
```

Angle yang umum:

```text
authn_session
authz_role
object_tenant_boundary
input_validation
state_transition
business_logic
data_exposure
side_effect_write
rate_limit_or_race
cache_cors_redirect
file_or_url_handling
error_oracle
source_runtime_diff
chain_potential
```

Endpoint baru boleh dianggap meaningful covered jika angle relevan berakhir di:

```text
endpoint_angle_tested
tested_secure
finding_candidate
confirmed
gap_found
blocked
out_of_scope
by_design
inconclusive
```

## 12. Generate OWASP A01-A10 Dan API Top 10

Generate Web A01-A10:

```bash
../../../bin/bbf owasp-plan web \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me
```

Generate OWASP API Top 10:

```bash
../../../bin/bbf owasp-plan api \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me
```

Generate keduanya:

```bash
../../../bin/bbf owasp-plan both \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me
```

Secara default `owasp-plan` juga menjalankan `angle-plan full`.

Jika hanya ingin membuat test card dari bug class tertentu:

```bash
../../../bin/bbf pentest-card idor \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me \
  --title "IDOR/BAC boundary check for /api/me"
```

Bug class yang tersedia:

```text
idor, xss, oauth, business-logic, graphql, ssrf, sqli, race, file-upload, rce,
info-disclosure, llm-ai
a01..a10
api01..api10
```

## 13. Menjalankan Test Dengan Executor

Executor mendukung transport:

```text
http
browser
burp
caido
```

Contoh Burp:

```bash
../../../bin/bbf angle-exec \
  --transport burp \
  --proxy http://127.0.0.1:8080 \
  --base-url https://target.example \
  --endpoint-id ep-get-api-me \
  --angle authn_session \
  --allow-active
```

Contoh Caido:

```bash
../../../bin/bbf angle-exec \
  --transport caido \
  --proxy http://127.0.0.1:18081 \
  --base-url https://target.example \
  --endpoint-id ep-get-api-me \
  --angle object_tenant_boundary \
  --allow-active
```

Contoh browser:

```bash
../../../bin/bbf angle-exec \
  --transport browser \
  --base-url https://target.example \
  --endpoint-id ep-get-api-me \
  --angle cache_cors_redirect \
  --allow-active
```

Header session:

```bash
../../../bin/bbf angle-exec \
  --transport burp \
  --base-url https://target.example \
  --endpoint-id ep-get-api-me \
  --angle authz_role \
  --headers-file .private/account-a.json \
  --alt-headers-file .private/account-b.json \
  --allow-active
```

Contoh `.private/account-a.json`:

```json
{
  "Cookie": "session=REDACTED",
  "X-CSRF-Token": "REDACTED"
}
```

State-changing method butuh izin eksplisit:

```bash
../../../bin/bbf angle-exec \
  --transport burp \
  --base-url https://target.example \
  --method POST \
  --path /api/profile \
  --endpoint-id ep-post-profile \
  --angle side_effect_write \
  --body-file .private/profile-body.json \
  --allow-active \
  --allow-state-change
```

Hasil executor masuk ke:

```text
evidence/responses/
evidence/burp/
evidence/caido/
test-ledger.md
data/events.jsonl
```

Executor tidak boleh langsung menyimpulkan `confirmed`. Ia hanya bisa membuat
state seperti `tested_secure`, `finding_candidate`, `inconclusive`, atau
`blocked`.

## 14. Evidence Quality Scorer

Score evidence:

```bash
../../../bin/bbf evidence-score \
  --endpoint-id ep-get-api-me \
  --angle authn_session
```

Score semua test yang cocok:

```bash
../../../bin/bbf evidence-score --all
```

Dengan test id:

```bash
../../../bin/bbf evidence-score --test-id test-angle-ep-get-api-me-authn-session
```

Scorer mengecek:

```text
baseline
negative control
mutated request
read-back
saved evidence file
Burp/Caido/browser context
```

Output:

```text
evidence/reviews/
data/events.jsonl
data/graph_state.json
dashboard evidence quality metrics
```

Interpretasi:

```text
sufficient   cukup kuat untuk lanjut judge
partial      ada bukti, tetapi masih kurang kontrol
incomplete   belum layak jadi dasar report
```

## 15. Semantic Evidence Judge

Judge evidence:

```bash
../../../bin/bbf judge \
  --endpoint-id ep-get-api-me \
  --angle authn_session
```

Judge semua:

```bash
../../../bin/bbf judge --all
```

Judge dari test id:

```bash
../../../bin/bbf judge --test-id <test-id>
```

Judge mengecek:

```text
baseline request/evidence
mutated request/evidence
negative control/evidence
read-back evidence
semantic status/body diff
ownership atau role context
fresh repro pass
saved evidence file
redaction
verdict coherence
```

Kemungkinan hasil:

```text
judge_reportable       bukti siap masuk report
judge_candidate        kuat, tetapi masih ada proof gap
judge_needs_evidence   belum cukup
judge_blocked          ada blocker yang harus diselesaikan
```

Rule:

```text
dashboard menunjukkan state
judge menilai kualitas bukti
```

## 16. Fresh Repro

Sebelum report final, lakukan fresh repro dengan session baru atau akun lain
jika relevan:

```bash
../../../bin/bbf fresh-repro \
  --test-id <test-id> \
  --headers-file .private/fresh-session.json \
  --allow-active
```

Jika replay dilakukan manual lewat browser/Burp/Caido:

```bash
../../../bin/bbf fresh-repro \
  --test-id <test-id> \
  --mark-pass \
  --evidence-path evidence/screenshots/fresh-repro.png \
  --reason "manual browser and Burp replay passed with a fresh session"
```

Jika gagal:

```bash
../../../bin/bbf fresh-repro \
  --test-id <test-id> \
  --mark-fail \
  --reason "fresh session could not reproduce the behavior"
```

Setelah fresh repro:

```bash
../../../bin/bbf judge --test-id <test-id>
```

## 17. Report Lifecycle

Buat draft:

```bash
../../../bin/bbf report-lifecycle draft \
  --test-id <test-id> \
  --title "Broken access control on user export"
```

List report:

```bash
../../../bin/bbf report-lifecycle list
```

Update status:

```bash
../../../bin/bbf report-lifecycle status <report-id> submitted --note "Submitted to platform"
../../../bin/bbf report-lifecycle status <report-id> triaged --note "Triaged by program"
../../../bin/bbf report-lifecycle status <report-id> accepted --bounty-value "500" --retest-date "2026-06-01"
```

Report lifecycle akan memblokir submit jika proof gate belum lengkap. Cek
kolom `missing_before_submit` di dashboard atau `data/report_lifecycle.json`.

## 18. Caido CLI Dan Native Import

Cek status Caido:

```bash
../../../bin/bbf caido status
```

Lihat command launch:

```bash
../../../bin/bbf caido command
```

Import HAR/JSON history dari Caido:

```bash
../../../bin/bbf caido import \
  --source caido \
  --file /path/to/caido-history.har \
  --endpoint-id ep-get-api-me \
  --test-id <test-id>
```

Import Burp export:

```bash
../../../bin/bbf caido import \
  --source burp \
  --file /path/to/burp-export.har \
  --endpoint-id ep-get-api-me \
  --test-id <test-id>
```

Import history berguna untuk membuat evidence dari request yang sudah terlihat
di proxy tanpa mengulang request yang tidak perlu.

## 19. Risk-Based Prioritizer

Saat engagement besar, jangan test semua endpoint secara rata. Jalankan:

```bash
../../../bin/bbf risk-prioritize --limit 25
```

Profile:

```bash
../../../bin/bbf risk-prioritize --profile balanced --limit 25
../../../bin/bbf risk-prioritize --profile impact --limit 10
../../../bin/bbf risk-prioritize --profile coverage --limit 20
../../../bin/bbf risk-prioritize --profile source --limit 20
../../../bin/bbf risk-prioritize --profile runtime --limit 20
```

Output:

```text
priority-testing-plan.md
data/risk_priorities.json
event endpoint_prioritized
event risk_prioritization_reviewed
```

Mulai dari:

```text
P0/P1
readiness ready
readiness needs_context
```

Endpoint `blocked` harus diselesaikan blocker-nya dulu.

## 20. Domain-Specific Depth

Generic Web/API testing belum cukup untuk target tertentu.

WordPress plugin:

```bash
../../../bin/bbf wp-plan
../../../bin/bbf domain-verify --domain wp
```

On-prem/source product:

```bash
../../../bin/bbf onprem-plan
../../../bin/bbf source-verify --source-root /path/to/source --queue-missing
../../../bin/bbf domain-verify --domain onprem
```

Mobile:

```bash
../../../bin/bbf mobile-plan
../../../bin/bbf domain-verify --domain mobile
```

Semua:

```bash
../../../bin/bbf domain-plan all
../../../bin/bbf domain-verify --domain all
```

Catat check yang selesai:

```bash
../../../bin/bbf event domain_check_completed \
  --domain wp \
  --check-id wp-capability-nonce \
  --status domain_complete \
  --evidence-path evidence/burp/wp-capability-nonce.txt
```

## 21. Neo4j Optional

Dashboard tetap jalan tanpa Neo4j. Untuk export Cypher:

Jalankan dari root workflow:

```bash
python3 scripts/neo4j_sync.py \
  --root engagements/<program>/<target> \
  --out engagements/<program>/<target>/output/attack-graph.cypher \
  --json-out engagements/<program>/<target>/output/attack-graph.json
```

Push ke Neo4j:

```bash
export NEO4J_URI=http://127.0.0.1:7474
export NEO4J_USER=neo4j
export NEO4J_PASSWORD='change-me'
python3 scripts/neo4j_sync.py \
  --root engagements/<program>/<target> \
  --push
```

Gunakan halaman dashboard:

```text
http://127.0.0.1:5173/neo4j
```

## 22. Run Queue / Command Center

## 22. Governance And Proof Controls

Kontrol governance dan proof gate diimplementasikan sebagai command:

```bash
../../../bin/bbf ai-governance check
../../../bin/bbf ai-governance check --fix-queue
../../../bin/bbf attack-path-review --limit 25
../../../bin/bbf attack-path-review --queue --queue-limit 5
../../../bin/bbf ai-governance sanitize-export
```

Gunanya:

```text
menandai autonomy level setiap task
memisahkan role agent secara eksplisit
mengecek active approval gate
mengecek evidence/judge gate sebelum report
meranking attack path yang belum lengkap
membuat queue untuk missing source/auth/chain/evidence/judge
membuat sanitized export tanpa secret
```

Autonomy level:

```text
passive_auto              analisis lokal, tidak kirim request
active_safe_auto          active rendah risiko, tetap dikontrol policy
active_requires_approval  live testing/replay/fresh repro
hard_deny                 out-of-scope/destructive/forbidden
```

Output:

```text
data/ai_governance.json
data/ai_governance_review.json
output/ai-governance-review.md
data/attack_path_priorities.json
output/attack-path-review.md
output/sanitized-export-*.zip
```

## 23. Run Queue / Command Center

Seed pipeline:

```bash
../../../bin/bbf queue seed
```

List task:

```bash
../../../bin/bbf queue list
```

Run next safe task:

```bash
../../../bin/bbf queue run-next
```

Approve active task:

```bash
../../../bin/bbf queue approve <task-id>
```

Run specific task:

```bash
../../../bin/bbf queue run <task-id>
```

Block task dengan reason:

```bash
../../../bin/bbf queue block <task-id> "missing allowed account"
```

Tambah task manual:

```bash
../../../bin/bbf queue add \
  --stage source-read \
  --label "Review login controller" \
  ../../../bin/bbf source-verify --source-root source/current --queue-missing
```

Tambah active task manual:

```bash
../../../bin/bbf queue add \
  --stage angle-exec \
  --label "Execute auth role test for /api/me" \
  --active \
  --blocked-reason "operator approval required" \
  ../../../bin/bbf angle-exec --transport burp --endpoint-id ep-get-api-me --angle authz_role --allow-active
```

## 24. Multi-Engagement

Tidak perlu beda port untuk banyak engagement. Buat folder engagement berbeda:

```bash
bin/bbf init template target-a
bin/bbf init template target-b
bin/bbf init h1 target-a
```

Jalankan satu server:

```bash
bin/bbf dashboard --port 5173
```

Buka:

```text
http://127.0.0.1:5173
```

Pilih engagement dari selector.

Jika ingin dashboard terpisah per browser/session, boleh gunakan port berbeda:

```bash
bin/bbf dashboard --port 5174
bin/bbf dashboard --port 5175
```

Tetapi default yang disarankan adalah satu port dan multi-engagement selector.

## 25. Daily Operating Checklist

Sebelum mulai:

```text
scope.md sudah jelas
notes/rules.md sudah diisi
data/safety_policy.json allow_hosts sudah benar
akun test valid
Burp/Caido siap jika perlu
dashboard terbuka
```

Saat recon:

```text
catat endpoint_discovered
catat param_discovered
catat endpoint_seen_runtime
import recon framework jika ada
build graph
risk-prioritize
```

Saat source review:

```text
queue file
baca satu file penuh
buat source review artifact
link source -> flow -> endpoint
map attack surface
angle-plan full
source-verify
```

Saat testing:

```text
cek safety policy
approve active task
jalankan angle-exec
simpan request/response/screenshot
evidence-score
judge
fresh-repro jika kandidat report
```

Sebelum berhenti:

```bash
../../../bin/bbf coverage
../../../bin/bbf build
```

Update:

```text
notes/recent-state.md
notes/loop/log.md
coverage-matrix.md
priority-testing-plan.md
```

Handoff akhir harus menjawab:

```text
events written
endpoints added
tests performed
evidence saved
verdicts changed
active loops
pivots created
open gaps
next safest action
```

## 26. Kapan Bisa Bilang Valid, Secure, Atau Reportable

Gunakan rule ini:

```text
valid lead
  ada runtime signal dan minimal evidence awal

finding candidate
  ada baseline, mutation, negative control, dan impact hypothesis

reportable
  judge_reportable, fresh repro pass, scope cocok, bukti cukup

tested secure
  ada baseline, negative control, test angle relevan, dan tidak ada bypass

inconclusive
  bukti kurang, role/session kurang, response tidak cukup beda, atau kontrol lemah

blocked
  tidak bisa lanjut karena scope, account, rate limit, missing source, atau approval
```

Jangan klaim:

```text
confirmed dari source-only
tested secure dari satu request gagal
reportable tanpa fresh repro jika fresh repro dibutuhkan
complete jika source completeness masih partial/incomplete
multi-angle jika yang dites hanya A01/IDOR
```

## 27. Troubleshooting

Dashboard tidak muncul:

```bash
lsof -nP -iTCP:5173 -sTCP:LISTEN
../../../bin/bbf dashboard --port 5173
```

Port sudah dipakai:

```bash
../../../bin/bbf dashboard --port 5174
```

Engagement tidak muncul di selector:

```bash
../../../bin/bbf build
ls data/graph_state.json
```

Executor diblokir:

```bash
../../../bin/bbf safety status
```

Cek:

```text
allow_hosts
forbidden_path_patterns
allowed method
--allow-active
--allow-state-change untuk non-GET
```

Evidence score rendah:

```text
tambahkan baseline
tambahkan mutated request
tambahkan negative control
tambahkan read-back
simpan request/response
simpan browser screenshot jika UI-visible
```

Judge tidak reportable:

```text
cek fresh repro
cek ownership/role proof
cek semantic response diff
cek missing proof before submit
cek redaction
```

Source completeness rendah:

```bash
../../../bin/bbf source-verify --source-root /path/to/source --queue-missing
```

Lalu baca file yang queued satu per satu dan buat `source-reviews/<id>.md`.

## 28. Contoh Alur Lengkap Web/API

```bash
cd /Users/raihan/BugBounty/worfklow/hunterflowx
bin/bbf init template example-api
cd engagements/template/example-api

# isi scope/rules/policy dulu
$EDITOR scope.md
$EDITOR notes/rules.md
$EDITOR data/safety_policy.json

# catat endpoint
../../../bin/bbf event endpoint_discovered \
  --engagement template-example-api \
  --asset-id asset-api \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me \
  --source "Burp Proxy history #12"

# buat baseline coverage
../../../bin/bbf owasp-plan both \
  --asset-id asset-api \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me

# pilih prioritas
../../../bin/bbf risk-prioritize --limit 25

# execute satu angle
../../../bin/bbf angle-exec \
  --transport burp \
  --proxy http://127.0.0.1:8080 \
  --base-url https://target.example \
  --endpoint-id ep-get-api-me \
  --angle authz_role \
  --headers-file .private/account-a.json \
  --alt-headers-file .private/account-b.json \
  --allow-active

# score dan judge
../../../bin/bbf evidence-score --endpoint-id ep-get-api-me --angle authz_role
../../../bin/bbf judge --endpoint-id ep-get-api-me --angle authz_role

# fresh repro jika kandidat report
../../../bin/bbf fresh-repro --test-id <test-id> --headers-file .private/fresh-session.json --allow-active
../../../bin/bbf judge --test-id <test-id>

# buat report draft jika sudah reportable
../../../bin/bbf report-lifecycle draft --test-id <test-id> --title "Broken access control on /api/me"

# buka dashboard
../../../bin/bbf dashboard --port 5173
```

## 29. Dokumen Terkait

```text
README.md
QUICKSTART.md
AGENTS.md
docs/architecture.md
docs/command-center-and-proof-gates.md
docs/neo4j-bridge.md
docs/evidence-quality-scorer.md
docs/evidence-judge.md
docs/source-completeness-verifier.md
docs/risk-based-prioritizer.md
docs/domain-depth-profiles.md
workflow/final-operating-model.md
workflow/multi-angle-source-flow-playbook.md
workflow/web-api-playbook.md
workflow/wp-plugin-playbook.md
workflow/source-audit-playbook.md
workflow/mobile-app-playbook.md
```
