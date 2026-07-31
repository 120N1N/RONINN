# Source Completeness Verifier

`bbf source-verify` memastikan AI tidak mengaku sudah memahami source hanya
karena pernah grep beberapa file.

Verifier ini membandingkan source root dengan event log dan artifact review:

```text
source root scan
  -> important file inventory
  -> source_file_queued
  -> source_file_read
  -> source-reviews/<file-id>.md
  -> source_flow_linked or not_runtime_relevant
  -> attack_surface_mapped
  -> endpoint_angle_planned
  -> source_completeness_reviewed
```

## Jalankan

```bash
cd engagements/<program>/<target>

../../../bin/bbf source-verify \
  --source-root /path/to/extracted/source \
  --queue-missing
```

Mode default hanya memasukkan file penting: route, controller, middleware,
service, model, auth, config, webhook, upload, export, payment, GraphQL, SQL,
dan file lain yang punya hint route/API/auth/data-flow.

Untuk memaksa semua file source-like ikut diverifikasi:

```bash
../../../bin/bbf source-verify \
  --source-root /path/to/extracted/source \
  --all \
  --queue-missing
```

## Yang Dicek

Per file, verifier memberi skor 0-100:

| Check | Points |
|---|---:|
| `source_file_queued` event | 10 |
| `source_file_read` event | 20 |
| non-empty `source-reviews/<file-id>.md` | 20 |
| semua section wajib ada dan terisi | 20 |
| `source_flow_linked` event | 15 |
| `attack_surface_mapped` event | 10 |
| `endpoint_angle_planned` event | 5 |

Jika file memang bukan runtime-relevant, tetap wajib punya review artifact dan
harus ditandai `not_runtime_relevant`. Dalam kasus itu verifier mengganti syarat
flow/attack/angle dengan disposition yang jelas.

## Section Wajib

Artifact source review harus mengikuti `templates/source/file-review.md` dan
berisi:

```text
RESTATE-OK
FILE-PURPOSE
ENTRYPOINTS
TRUST-BOUNDARIES
ROUTES-ENDPOINTS
DATA-FLOW
SINKS-SOURCES
AUTHZ-AUTHN
ATTACK-SURFACE
MULTI-ANGLE-PLAN
CHAIN-CANDIDATES
EVENTS-WRITTEN
OPEN-GAPS
```

`unknown` boleh ditulis, tapi harus ada `gap_found`, `mapping_gap_found`, atau
status `blocked`. Unknown tanpa gap dianggap tidak lengkap.

## Output

Verifier menulis:

```text
source-completeness.md
source-reviews/_completeness/source-completeness-<timestamp>.md
data/events.jsonl       # source_completeness_reviewed
data/graph_state.json   # rebuilt unless --no-build
```

Dashboard menampilkan:

```text
source_files_total
source_files_complete
source_files_partial
source_files_incomplete
source_reviews_missing
source_critical_missing
source_completeness_avg
```

## Interpretasi

```text
source_complete    = file sudah dibaca, artifact lengkap, dan flow/angle jelas
source_partial     = sebagian bukti ada, tapi belum cukup untuk bilang mapped
source_incomplete  = file penting belum dibaca/review/link dengan benar
```

Verifier tidak membuktikan vulnerability. Verifier hanya membuktikan bahwa
source coverage sudah cukup disiplin untuk lanjut ke runtime testing.
