# Hunterflowx

Workflow final siap pakai untuk bug bounty dengan AI, live graph, recursive
hunting loop, evidence ledger, dan strict verdict gate.

Hunterflowx adalah workflow operasional mandiri yang menggabungkan disiplin
recon dari `hunterweb` dan metodologi source-grounded dari `GPTxOPUS` ke dalam
satu control plane yang siap dipakai.

Folder ini memakai dua sumber metodologi lokal:

```text
hunterweb/recon-framework        -> policy-gated recursive recon engine
GPTxOPUS                         -> A01-A10 coverage + source-grounding + manual test card discipline
```

## Prinsip Utama

```text
AI chat is not truth.
Events are truth.
Evidence is truth.
Graph shows coverage.
Ledger shows what was tested.
Dead ends must pivot, block, retest, or close with evidence.
```

## Quick Start

Dokumentasi pemakaian lengkap ada di:

```text
docs/panduan-penggunaan.md
rules/HUNTERFLOW_RULES.md
```

```bash
cd /Users/raihan/BugBounty/worfklow/hunterflowx

# 1. Buat engagement baru
python3 scripts/init_engagement.py demo target-app

# 2. Masuk ke engagement
cd engagements/demo/target-app

# 3. Isi scope/rules dulu
$EDITOR notes/rules.md
$EDITOR scope.md

# 4. Tambahkan event contoh
../../../bin/bbf event endpoint_discovered \
  --engagement demo-target-app \
  --asset-id asset-app \
  --endpoint-id ep-post-login \
  --method POST \
  --path /login \
  --source "manual:initial-map"

# 5. Buat test-card aktif dari metodologi Hunterflowx
../../../bin/bbf pentest-card idor \
  --asset-id asset-app \
  --endpoint-id ep-post-login \
  --method POST \
  --path /login \
  --title "IDOR/BAC boundary check for login-adjacent API"

# 6. Generate baseline A01-A10/API testing jika perlu
../../../bin/bbf owasp-plan api \
  --asset-id asset-app \
  --endpoint-id ep-post-login \
  --method POST \
  --path /login

# 6b. Untuk endpoint penting, queue deep multi-angle + creative hypotheses
../../../bin/bbf angle-plan full \
  --asset-id asset-app \
  --endpoint-id ep-post-login \
  --method POST \
  --path /login

# 6c. Jalankan queued angle lewat Burp/Caido/browser/http dan simpan evidence
../../../bin/bbf angle-exec \
  --transport burp \
  --proxy http://127.0.0.1:8080 \
  --base-url https://target.example \
  --endpoint-id ep-post-login \
  --angle authn_session \
  --allow-active

# 6d. Score kualitas evidence sebelum menyimpulkan
../../../bin/bbf evidence-score \
  --endpoint-id ep-post-login \
  --angle authn_session

# 6d-2. Judge apakah evidence sudah reportable atau masih kurang
../../../bin/bbf judge \
  --endpoint-id ep-post-login \
  --angle authn_session

# 6e. Jika ada source code, verify file penting benar-benar sudah dibaca
../../../bin/bbf source-verify \
  --source-root /path/to/extracted/source \
  --queue-missing

# 6f. Saat endpoint banyak, pilih yang paling worth diuji dulu
../../../bin/bbf risk-prioritize --limit 25

# 6g. Jika target domain-specific, aktifkan depth profile
../../../bin/bbf domain-plan wp       # WordPress plugin
../../../bin/bbf domain-plan onprem   # on-prem/source product
../../../bin/bbf domain-plan mobile   # Android/iOS/mobile API
../../../bin/bbf domain-verify --domain all

# 7. Build graph
../../../bin/bbf build

# 8. Jalankan dashboard lokal
../../../bin/bbf dashboard
```

Lalu buka:

```text
http://localhost:5173
```

Dashboard memakai satu port dan otomatis menampilkan semua engagement yang sudah
di-init di `engagements/<program>/<target>/`.

## Struktur

```text
hunterflowx/
  AGENTS.md
  README.md
  QUICKSTART.md
  bin/bbf
  dashboard/
    index.html
  docs/
    panduan-penggunaan.md
    angle-executor.md
    evidence-quality-scorer.md
    evidence-judge.md
    domain-depth-profiles.md
    source-completeness-verifier.md
    risk-based-prioritizer.md
    architecture.md
    recursive-loop.md
    reconfw-bridge.md
    verdict-gate.md
    integration-map.md
  engagements/
    .gitkeep
    template/
      docs/
      rules/
      notes/
      findings/
      report/
      evidence/
      example-api/
        data/
        evidence/
        findings/
        reports/
  examples/
    demo-events.jsonl
  references/
    source-map.md
  schemas/
    event.schema.json
    graph_state.schema.json
  scripts/
    init_engagement.py
    add_event.py
    import_reconfw.py
    pentest_card.py
    build_graph.py
    check_coverage.py
    serve_dashboard.py
  templates/
    engagement/
    events/
    findings/
    reports/
  workflow/
    final-operating-model.md
    multi-angle-source-flow-playbook.md
    web-api-playbook.md
    wp-plugin-playbook.md
    source-audit-playbook.md
    mobile-app-playbook.md
```

## Cara Kerja

Setiap aksi AI atau operator harus menjadi event:

```text
scope_loaded
asset_added
endpoint_discovered
param_discovered
endpoint_seen_runtime
loop_started
test_started
payload_attempted
evidence_added
dead_end_recorded
pivot_decision
verdict_set
finding_promoted
```

Import hasil `hunterweb/recon-framework`:

```bash
cd engagements/<program>/<target>
../../../bin/bbf import-reconfw /path/to/reconfw/workspace
```

Detailnya ada di `docs/reconfw-bridge.md`.

Generate source-grounded manual test-card:

```bash
cd engagements/<program>/<target>
../../../bin/bbf pentest-card idor --endpoint-id ep-user-export --asset-id asset-api --method GET --path /api/users/123/export
```

Ini menulis:

```text
leads/test-cards/<test-id>.md
data/events.jsonl       # test_planned
priority-testing-plan.md
data/graph_state.json
```

Generate A01-A10/API Top 10 baseline:

```bash
cd engagements/<program>/<target>
../../../bin/bbf owasp-plan web --endpoint-id ep-user-export --asset-id asset-api --method GET --path /api/users/123/export
../../../bin/bbf owasp-plan api --endpoint-id ep-user-export --asset-id asset-api --method GET --path /api/users/123/export
../../../bin/bbf owasp-plan both --endpoint-id ep-user-export --asset-id asset-api --method GET --path /api/users/123/export
```

`owasp-plan` otomatis menjalankan `angle-plan full` kecuali diberi
`--skip-angle-plan`. Jadi dashboard harus menunjukkan `planned_tests`,
`planned_angles`, dan `creative_ideas`.

Queue multi-angle tanpa membuat A01-A10/API card:

```bash
cd engagements/<program>/<target>
../../../bin/bbf angle-plan core --endpoint-id ep-user-export --asset-id asset-api --method GET --path /api/users/123/export
../../../bin/bbf angle-plan deep --endpoint-id ep-user-export --asset-id asset-api --method GET --path /api/users/123/export
../../../bin/bbf angle-plan full --endpoint-id ep-user-export --asset-id asset-api --method GET --path /api/users/123/export
```

Gunakan `full` untuk endpoint penting. Ini mencegah workflow menjadi
IDOR/A01-heavy karena angle yang tercatat mencakup authn, role, object/tenant,
input/parser, state, business logic, data exposure, side effects, race, cache,
file/URL, error oracle, source/runtime diff, API inventory, async jobs,
client-trust integrity, webhook/callback, dan chain potential.

Execute queued angles:

```bash
../../../bin/bbf angle-exec --transport burp --proxy http://127.0.0.1:8080 --base-url https://target.example --endpoint-id ep-user-export --angle authn_session --allow-active
../../../bin/bbf angle-exec --transport caido --proxy http://127.0.0.1:8080 --base-url https://target.example --endpoint-id ep-user-export --angle input_validation --allow-active
../../../bin/bbf angle-exec --transport browser --base-url https://target.example --endpoint-id ep-user-export --angle cache_cors_redirect --allow-active
```

Executor output masuk ke `evidence/responses/`, `evidence/burp/` atau
`evidence/caido/`, `test-ledger.md`, dan `data/events.jsonl`. Setelah itu
dashboard akan menaikkan `tested_angles`.

Score kualitas evidence:

```bash
../../../bin/bbf evidence-score --endpoint-id ep-user-export --angle authn_session
../../../bin/bbf evidence-score --endpoint-id ep-user-export --all
```

Scorer mengecek baseline, negative control, mutated request, read-back,
keberadaan file evidence, dan konteks Burp/Caido/browser. Hasilnya masuk ke
`evidence/reviews/`, event `evidence_reviewed`, dan dashboard metrics
`evidence_quality_*`.

Judge reportability evidence:

```bash
../../../bin/bbf judge --endpoint-id ep-user-export --all
../../../bin/bbf judge --test-id test-angle-ep-user-export-authz-abc123
```

Judge menggabungkan evidence score, baseline, mutation, negative control,
read-back, file evidence, Burp/Caido/browser context, verdict coherence, dan
redaction. Hasilnya masuk ke `evidence/judgements/`, `data/judgements.json`,
event `evidence_judged`, event `judge_reviewed`, dan dashboard metrics
`judge_*`.

Verify source completeness:

```bash
../../../bin/bbf source-verify --source-root /path/to/source --queue-missing
../../../bin/bbf source-verify --source-root /path/to/source --all --queue-missing
```

Verifier mengecek inventory file penting, `source_file_queued`,
`source_file_read`, artifact `source-reviews/<file-id>.md`, section wajib,
`source_flow_linked` atau `not_runtime_relevant`, `attack_surface_mapped`, dan
`endpoint_angle_planned`. Hasilnya masuk ke
`source-reviews/_completeness/`, event `source_completeness_reviewed`, dan
dashboard metrics `source_files_*`.

Prioritize endpoint besar:

```bash
../../../bin/bbf risk-prioritize --limit 25
../../../bin/bbf risk-prioritize --profile impact --limit 10
../../../bin/bbf risk-prioritize --profile source --limit 20
```

Prioritizer membaca endpoint, source-flow, attack surface, planned/tested
angles, chain candidates, evidence review, dan verdict state. Hasilnya masuk ke
`priority-testing-plan.md`, `data/risk_priorities.json`, event
`endpoint_prioritized`, event `risk_prioritization_reviewed`, dan dashboard
metrics `risk_*`.

Aktifkan domain-specific depth:

```bash
../../../bin/bbf wp-plan
../../../bin/bbf onprem-plan
../../../bin/bbf mobile-plan
../../../bin/bbf domain-plan all
../../../bin/bbf domain-verify --domain all
```

Ini membuat gate domain khusus sebagai event yang terlihat di dashboard:

```text
domain_profile_loaded
domain_check_planned
domain_check_completed
domain_depth_reviewed
```

Dashboard menampilkan `domain_depth_avg`, skor WP/on-prem/mobile, dan check
yang masih missing. Domain check tetap harus dilanjutkan ke runtime evidence,
`evidence-score`, dan `judge` sebelum report.

Governance dan attack-path controls:

```bash
../../../bin/bbf ai-governance check
../../../bin/bbf ai-governance sanitize-export
../../../bin/bbf attack-path-review --limit 25
../../../bin/bbf attack-path-review --queue --queue-limit 5
```

Ini menambahkan kontrol untuk autonomy labels, data governance,
hallucination-resistant proof gates, dan attack-path ranking.

Event masuk ke:

```text
engagements/<program>/<target>/data/events.jsonl
```

Lalu `build_graph.py` membuat:

```text
engagements/<program>/<target>/data/graph_state.json
```

Dashboard membaca graph state dan menampilkan:

- endpoint yang sudah/belum dites
- planned/tested endpoint angles
- Neo4j-ready attack graph:
  `JS File -> API Route -> Param -> Auth Role -> Test Angle -> Chaining -> Evidence -> Finding`
- source files complete/partial/incomplete
- P0/P1 risk priority endpoint queue
- domain-specific WP/on-prem/mobile depth
- evidence judge reportable/candidate/needs-evidence
- evidence missing
- active recursive loops
- dead end tanpa pivot
- finding candidate
- confirmed finding
- blocker/gap

Untuk banyak engagement, cukup buat target baru:

```bash
bin/bbf init template example-api
bin/bbf init h1 acme
```

Setelah setiap engagement menjalankan `../../../bin/bbf build`, dashboard di
`http://127.0.0.1:5173` akan menampilkannya di selector engagement.

## Rule Paling Penting

```text
confirmed      = wajib ada request/response atau browser-visible evidence
tested_secure  = wajib ada baseline, test negatif, dan kontrol cukup
inconclusive   = evidence/session/role/control belum cukup
blocked        = ada missing action konkret
candidate      = lead kuat, belum reportable
```

Tidak ada report dari klaim source-only atau scanner-only.

## Neo4j Optional Bridge

Dashboard tetap berjalan tanpa Neo4j. Jika Neo4j aktif, export/push graph:

```bash
python3 scripts/neo4j_sync.py --root engagements/<program>/<target>

export NEO4J_URI=http://127.0.0.1:7474
export NEO4J_USER=neo4j
export NEO4J_PASSWORD='change-me'
python3 scripts/neo4j_sync.py --root engagements/<program>/<target> --push
```

Detail:

```text
docs/neo4j-bridge.md
```

## Source Dan Multi-Angle Testing

Jika ada source code atau file hasil ekstraksi, pakai aturan:

```text
one file at a time -> source review artifact -> source_flow_linked
-> attack_surface_mapped -> endpoint_angle_planned
-> endpoint_angle_tested -> evidence -> verdict -> chain
```

Workflow ini wajib diikuti, tapi tidak boleh membuat AI kaku. Kreativitas tetap
wajib dipakai untuk hipotesis, pivot, dan chaining selama dicatat sebagai:

```text
creative_hypothesis_added
creative_pivot_added
chain_candidate_added
attack_path_expanded
```

Dokumen utama:

```text
docs/source-completeness-verifier.md
docs/evidence-judge.md
docs/risk-based-prioritizer.md
docs/domain-depth-profiles.md
docs/command-center-and-proof-gates.md
workflow/multi-angle-source-flow-playbook.md
multi-angle-coverage.md
source-file-queue.md
creative-exploration.md
source-reviews/<file-id>.md
```

## Command Center, Caido, Safety, Dan Report Lifecycle

Dashboard sekarang punya halaman operasional:

```text
http://127.0.0.1:5173/command
```

Fungsinya bukan hanya visibility. Halaman ini mengelola run queue:

```text
recon -> source read -> map endpoint -> angle-plan -> angle-exec
-> evidence-score -> judge -> fresh-repro -> report
```

Command terkait:

```bash
../../../bin/bbf queue seed
../../../bin/bbf queue list
../../../bin/bbf queue run-next
../../../bin/bbf queue approve <task-id>
../../../bin/bbf caido status
../../../bin/bbf caido command
../../../bin/bbf caido import --source caido --file /path/to/export.har --endpoint-id ep-id --test-id test-id
../../../bin/bbf safety status
../../../bin/bbf fresh-repro --test-id test-id --headers-file .private/fresh-session.json --allow-active
../../../bin/bbf report-lifecycle list
../../../bin/bbf report-lifecycle draft --test-id test-id --title "Bug title"
```

Active testing lewat queue selalu dibedakan dari task pasif. Endpoint execution
juga melewati `data/safety_policy.json` untuk allowlist host, method, forbidden
path, dan rate budget. Default `max_rps` tetap `10`; isi `allow_hosts` sebelum
live testing.

Caido mode sekarang dua lapis:

```text
1. proxy mode  : bbf angle-exec --transport caido --proxy http://127.0.0.1:PORT
2. native import: bbf caido import dari HAR/JSON history export
```

Jika Caido CLI tersedia, `bbf caido command` menghasilkan command launch per
engagement dengan data path terpisah.

Judge sekarang lebih ketat: reportable butuh baseline, mutation, negative
control, read-back, semantic response diff, ownership/role context, saved
evidence, dan fresh repro pass. Report lifecycle akan memblokir submit jika
proof gate belum lengkap.
