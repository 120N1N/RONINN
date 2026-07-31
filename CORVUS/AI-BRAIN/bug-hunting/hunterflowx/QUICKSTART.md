# Quickstart

Panduan lengkap operator ada di:

```text
docs/panduan-penggunaan.md
rules/HUNTERFLOW_RULES.md
```

## 1. Buat Engagement

```bash
cd /Users/raihan/BugBounty/worfklow/hunterflowx
python3 scripts/init_engagement.py <program> <target>
```

Contoh:

```bash
python3 scripts/init_engagement.py h1 acme
python3 scripts/init_engagement.py template example-api
```

Output:

```text
engagements/h1/acme/
engagements/h1/docs/
engagements/h1/rules/
engagements/h1/notes/
engagements/h1/findings/
engagements/h1/report/
engagements/h1/evidence/
```

## 2. Isi Scope

Wajib isi sebelum live testing. Program-level:

```text
engagements/<program>/rules/scope.md
engagements/<program>/rules/program-rules.md
engagements/<program>/notes/README.md
```

Target-level:

```text
scope.md
notes/rules.md
notes/recent-state.md
```

Minimal tulis:

- asset in scope
- asset out of scope
- rate limit
- allowed test accounts
- forbidden actions
- required headers/user-agent
- auth/session rules

## 3. Jalankan Mapping Dengan Event

Contoh event endpoint:

```bash
cd engagements/h1/acme
../../../bin/bbf event endpoint_discovered \
  --engagement h1-acme \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me \
  --source "Burp Proxy history #12"
```

## 4. Build Graph

```bash
../../../bin/bbf build
```

## 5. Import Recon Framework Jika Ada

Kalau kamu sudah menjalankan `hunterweb/recon-framework`, import hasilnya:

```bash
../../../bin/bbf import-reconfw /path/to/reconfw/workspace
```

Ini akan menulis event dan rebuild graph otomatis.

## 6. Generate Source-Grounded Test Card

Gunakan ini saat mau mengubah metodologi hunterweb + GPTxOPUS menjadi pekerjaan
yang benar-benar tercatat di Hunterflowx:

```bash
../../../bin/bbf pentest-card idor \
  --asset-id asset-main \
  --endpoint-id ep-get-api-me \
  --method GET \
  --path /api/me \
  --title "IDOR/BAC boundary check for /api/me"
```

Outputnya:

```text
leads/test-cards/<test-id>.md
data/events.jsonl       # test_planned
priority-testing-plan.md
data/graph_state.json
```

Bug class yang tersedia:

```text
idor, xss, oauth, business-logic, graphql, ssrf, sqli, race, file-upload, rce,
info-disclosure, llm-ai
a01, a02, a03, a04, a05, a06, a07, a08, a09, a10
api01, api02, api03, api04, api05, api06, api07, api08, api09, api10
```

Generate semua baseline sekaligus:

```bash
../../../bin/bbf owasp-plan web --endpoint-id ep-get-api-me --asset-id asset-main --method GET --path /api/me
../../../bin/bbf owasp-plan api --endpoint-id ep-get-api-me --asset-id asset-main --method GET --path /api/me
../../../bin/bbf owasp-plan both --endpoint-id ep-get-api-me --asset-id asset-main --method GET --path /api/me
```

`owasp-plan` otomatis membuat `endpoint_angle_planned` dan
`creative_hypothesis_added` lewat `angle-plan full`.

Kalau mau queue angle tanpa A01-A10/API card:

```bash
../../../bin/bbf angle-plan full --endpoint-id ep-get-api-me --asset-id asset-main --method GET --path /api/me
```

Jalankan satu queued angle lewat Burp:

```bash
../../../bin/bbf angle-exec \
  --transport burp \
  --proxy http://127.0.0.1:8080 \
  --base-url https://target.example \
  --endpoint-id ep-get-api-me \
  --angle authn_session \
  --allow-active
```

Score evidence:

```bash
../../../bin/bbf evidence-score --endpoint-id ep-get-api-me --angle authn_session
```

Judge apakah evidence sudah reportable:

```bash
../../../bin/bbf judge --endpoint-id ep-get-api-me --angle authn_session
```

Untuk Caido, ganti `--transport caido`. Untuk browser, gunakan
`--transport browser`; mode ini memakai Playwright jika tersedia.

## 7. Aktifkan Domain Depth Jika Perlu

Untuk WordPress plugin:

```bash
../../../bin/bbf wp-plan
../../../bin/bbf domain-verify --domain wp
```

Untuk on-prem/source product:

```bash
../../../bin/bbf onprem-plan
../../../bin/bbf source-verify --source-root /path/to/source/current --queue-missing
../../../bin/bbf domain-verify --domain onprem
```

Untuk mobile app:

```bash
../../../bin/bbf mobile-plan
../../../bin/bbf domain-verify --domain mobile
```

Selesaikan check dengan event:

```bash
../../../bin/bbf event domain_check_completed \
  --domain wp \
  --check-id wp-capability-nonce \
  --status domain_complete \
  --evidence-path evidence/burp/wp-capability-nonce.txt
```

## 8. Buka Dashboard

```bash
../../../bin/bbf dashboard
```

Open:

```text
http://localhost:5173
```

Dashboard ini satu port untuk banyak engagement. Engagement yang sudah punya
`data/graph_state.json` akan muncul di selector.

## 8. Source Dan Multi-Angle Rule

Kalau target punya source code, JS bundle, PHP, Python, config, template, atau
file lain, jangan langsung lompat antar file. Kerjakan satu file sampai selesai:

```bash
../../../bin/bbf event source_file_queued --source-id src-login --source-file app/login.php
../../../bin/bbf event source_file_read --source-id src-login --source-file app/login.php --review source-reviews/src-login.md
../../../bin/bbf event source_flow_linked --source-id src-login --flow-id flow-login --endpoint-id ep-login --handler loginController
../../../bin/bbf event attack_surface_mapped --endpoint-id ep-login --surface-id surface-login-authz --surface "login role/session boundary"
../../../bin/bbf angle-plan full --endpoint-id ep-login --asset-id asset-main --method POST --path /login
../../../bin/bbf angle-exec --transport burp --base-url https://target.example --endpoint-id ep-login --angle authn_session --allow-active
../../../bin/bbf evidence-score --endpoint-id ep-login --angle authn_session
../../../bin/bbf build
```

Isi:

```text
source-file-queue.md
source-reviews/<file-id>.md
multi-angle-coverage.md
```

Setelah source tersedia, jalankan completeness verifier supaya terlihat file
penting mana yang belum benar-benar dibaca:

```bash
../../../bin/bbf source-verify \
  --source-root /path/to/extracted/source \
  --queue-missing
```

Gunakan `--all` kalau engagement menuntut semua file source-like ikut
diverifikasi, bukan hanya file yang high-signal:

```bash
../../../bin/bbf source-verify --source-root /path/to/extracted/source --all --queue-missing
```

Output utama:

```text
source-completeness.md
source-reviews/_completeness/source-completeness-<timestamp>.md
data/events.jsonl       # source_completeness_reviewed
```

## 9. Prioritaskan Endpoint Saat Scope Besar

Setelah recon/import/source review membuat banyak endpoint, jalankan:

```bash
../../../bin/bbf risk-prioritize --limit 25
```

Output:

```text
priority-testing-plan.md
data/risk_priorities.json
data/events.jsonl       # endpoint_prioritized, risk_prioritization_reviewed
```

Gunakan profil sesuai kebutuhan:

```bash
../../../bin/bbf risk-prioritize --profile impact
../../../bin/bbf risk-prioritize --profile coverage
../../../bin/bbf risk-prioritize --profile source
../../../bin/bbf risk-prioritize --profile runtime
```

Mulai dari P0/P1 dengan readiness `ready` atau `needs_context`.

## 10. End Of Session

## 10. Governance Gate

Sebelum active testing atau report promotion, cek governance:

```bash
../../../bin/bbf ai-governance check
../../../bin/bbf ai-governance check --fix-queue
```

Review attack path yang paling worth dipivot:

```bash
../../../bin/bbf attack-path-review --limit 25
../../../bin/bbf attack-path-review --queue --queue-limit 5
```

Jika perlu handoff/VPS/share tanpa secret:

```bash
../../../bin/bbf ai-governance sanitize-export
```

Output:

```text
data/ai_governance_review.json
output/ai-governance-review.md
data/attack_path_priorities.json
output/attack-path-review.md
output/sanitized-export-*.zip
```

## 11. End Of Session

Sebelum berhenti:

```bash
../../../bin/bbf coverage
```

Lalu update:

```text
notes/recent-state.md
notes/loop/log.md
coverage-matrix.md
```

Final handoff harus menjawab:

```text
Events written:
Endpoints added:
Tests performed:
Evidence saved:
Verdicts changed:
Active loops:
Pivots created:
Open gaps:
Next safest action:
```

## 12. Command Center

Jalankan dashboard lalu buka halaman command:

```bash
../../../bin/bbf dashboard --port 5173
```

```text
http://127.0.0.1:5173/command
```

Seed pipeline:

```bash
../../../bin/bbf queue seed
```

Active testing task harus di-approve dulu:

```bash
../../../bin/bbf queue approve <task-id>
../../../bin/bbf queue run <task-id>
```

## 13. Caido CLI / Native Import

Proxy mode:

```bash
../../../bin/bbf angle-exec --transport caido --proxy http://127.0.0.1:18081 --allow-active
```

Caido CLI launch command per engagement:

```bash
../../../bin/bbf caido command
```

Import history export:

```bash
../../../bin/bbf caido import --source caido --file /path/to/history.har --endpoint-id ep-id --test-id test-id
```

## 14. Safety, Fresh Repro, Report

Isi allowlist sebelum live testing:

```bash
../../../bin/bbf safety status
```

Fresh repro sebelum report:

```bash
../../../bin/bbf fresh-repro --test-id test-id --headers-file .private/fresh-session.json --allow-active
../../../bin/bbf judge --test-id test-id
```

Report lifecycle:

```bash
../../../bin/bbf report-lifecycle draft --test-id test-id --title "Finding title"
../../../bin/bbf report-lifecycle list
```
