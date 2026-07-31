# Recon Framework Bridge

Bridge ini menghubungkan output `hunterweb/recon-framework` ke workflow final.

Tujuan:

```text
reconfw workspace -> data/events.jsonl -> data/graph_state.json -> dashboard
```

Bridge tidak menjalankan scan sendiri. Jalankan `reconfw` sesuai policy target,
lalu import hasilnya ke engagement final.

## Basic Usage

Dari engagement final:

```bash
cd /Users/raihan/BugBounty/worfklow/hunterflowx/engagements/<program>/<target>
../../../bin/bbf import-reconfw /path/to/reconfw/workspace
```

Command ini akan:

- membaca output recon-framework yang tersedia
- menulis event baru ke `data/events.jsonl`
- skip event yang sudah pernah diimport
- rebuild `data/graph_state.json`
- membuat dashboard langsung update

Dry-run:

```bash
../../../bin/bbf import-reconfw /path/to/reconfw/workspace --dry-run
```

Import tanpa rebuild graph:

```bash
../../../bin/bbf import-reconfw /path/to/reconfw/workspace --no-build
```

## Input Yang Dibaca

Bridge membaca file jika ada:

```text
assets/hosts.jsonl
assets/services.jsonl
assets/cloud.jsonl
assets/mobile.jsonl
assets/urls.jsonl
assets/endpoints.jsonl
assets/js.jsonl
output/live-probes/baselines.jsonl
output/mapping/graphql.jsonl
output/mapping/websockets.jsonl
output/mapping/signed-url-workflows.jsonl
output/graph/coverage-gaps.jsonl
leads/scored-leads.jsonl
queues/*.jsonl
output/diff/*.jsonl
coverage/audit-findings.jsonl
coverage/accepted-operational-gaps.jsonl
output/collector-health.jsonl
```

File yang tidak ada dilewati.

## Event Mapping

| Recon-framework output | Final event |
|---|---|
| `assets/hosts.jsonl` | `asset_added` |
| `assets/urls.jsonl` | `endpoint_discovered` |
| `assets/endpoints.jsonl` | `endpoint_discovered`, `graphql_operation_imported` |
| `assets/js.jsonl` | `js_endpoint_extracted` |
| `output/live-probes/baselines.jsonl` | `endpoint_verified_reachable`, `evidence_added` |
| `output/graph/coverage-gaps.jsonl` | `mapping_gap_found` |
| `leads/scored-leads.jsonl` | `attack_path_expanded` |
| `queues/*.jsonl` | `loop_started` |
| `output/diff/*.jsonl` | `source_runtime_diff_added` |
| coverage/health files | `gap_found`, `coverage_reviewed` |

## Important Rule

Import dari recon-framework bukan finding final.

```text
reconfw output = mapped surface / lead / gap
confirmed finding = runtime evidence + verdict gate
```

Jadi hasil import hanya menaikkan coverage dan prioritas testing. Finding tetap
harus lewat `evidence_added` dan `verdict_set`.
