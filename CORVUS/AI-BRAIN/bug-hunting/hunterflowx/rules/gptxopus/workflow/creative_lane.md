# Creative Testing Lane

Creative lane menjaga GPT tetap mencari bug di luar checklist ketika ada sinyal nyata.

Creative lane tetap harus source-grounded. Gunakan `source_refs` untuk asal ide, lalu minta evidence manual sebelum verdict.

## Trigger

| Trigger | Contoh lead |
|---|---|
| UI blocked, API accepts | UI-only authorization |
| 403/404/302 shape aneh | masked object or route policy gap |
| Empty response with side effect | async or worker issue |
| JS hidden route | admin/support/API v1 route |
| No-popup XSS | alternate sink in admin/email/PDF/mobile |
| Cache validator | login/object existence leak |
| Parser mismatch | proxy/backend/CDN disagreement |
| Business anomaly | impossible state accepted |

## Creative Lead Template

| Field | Value |
|---|---|
| Lead ID |  |
| Source signal |  |
| Why outside baseline |  |
| Related OWASP |  |
| Source refs |  |
| Asset/route |  |
| Hypothesis |  |
| Safe manual test-card |  |
| Expected secure behavior |  |
| Stop conditions |  |
| Evidence needed |  |
| Evidence refs |  |
| Creative reasoning note |  |
| Status | `creative_lead` |

## Rule

High-signal lead boleh menginterupsi urutan A01-A10, tetapi harus tetap dicatat ke coverage map.
