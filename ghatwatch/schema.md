# GhatWatch data contract: `ranking.json`

This is the single contract between `score.py` (A1), `index.html` (A2) and `brief.py` (A3).
**Do not modify this file.** If something here is ambiguous, write the question in `ghatwatch/BUILD-LOG.md`, take the safest assumption, and keep going.

## Common rules (all agents)

1. **Strict CPCB class B limits, and only on pH / DO / BOD.**
   - DO fail = `value < 5`
   - BOD fail = `value > 3`
   - pH fail = `value < 6.5` or `value > 8.5`
   - A value exactly equal to a limit (DO = 5.0, BOD = 3.0) is **within limit**.
   - Limits are read at runtime from `data/cpcb_water_quality_criteria.csv`, class B rows. Do not hard-code them.
   - The other 10 parameters have no class B limit and never affect rank.
2. **Missing or `no_table` is never clean and never passes.** It is not counted in `n` and not counted as a fail. It must be shown visibly as missing (grey or hatched, with the words "not sampled" or "no table in report").
3. **No LLM calls at runtime. No API keys anywhere.** Everything is deterministic Python + static HTML.
4. **Banned words in any output text:** "safe", "unsafe", "healthy", "unhealthy", "clean", "polluted beyond repair", and any health claim (disease, illness, skin, "dangerous for people"). Say "outside the CPCB class B limit" or "within the limit" instead. DO = 0 may be described as "zero dissolved oxygen recorded" only, with no claims about fish deaths or other effects.
5. **Rani Kamlapati / Kamla Park are two separate points.**
   - Ganesh tables → ghat id `kamla_park_kund`, display name "Kamla Park kund (Ganesh tables)"
   - Durga tables → ghat id `rani_kamlapati_ghat`, display name "Rani Kamlapati ghat, Lower Lake (Durga tables)"
   - Both carry `site_group: "Rani Kamlapati ghat / Kamla Park kund"` and `site_match: "medium"`, so a combined total (24 fails / 54 readings) can still be computed.
6. **Every number shown must trace to `evidence[].id`.** KPIs, ranking rows, alerts and insights all carry `evidence_ids`, or are directly derivable from evidence rows with the same ghat/scope.
7. **English only.** No Hindi text, no Hindi fields, no language toggle.
8. Readings come only from `data/bhopal_ghats_2023_2025.csv`. No other data.

## Ghat ids (fixed, 8 points)

| id | display name | site_group | water_body | site_match |
|---|---|---|---|---|
| `bairagarh` | Bairagarh (Sant Hirdaram) kund | same as name | Upper Lake (enclosed kund) | high |
| `malikhedi` | Malikhedi kund | same | Kund | high |
| `khatlapura` | Khatlapura ghat | same | Lower Lake | high |
| `kamla_park_kund` | Kamla Park kund (Ganesh tables) | Rani Kamlapati ghat / Kamla Park kund | as printed: Kamla Park | medium |
| `rani_kamlapati_ghat` | Rani Kamlapati ghat, Lower Lake (Durga tables) | Rani Kamlapati ghat / Kamla Park kund | Lower Lake | medium |
| `prempura` | Prempura ghat | same | Upper Lake | high |
| `hathaikheda` | Hathaikheda dam / kund | same | Hathaikheda dam | high |
| `shahpura` | Shahpura lake ghat | same | Shahpura Lake | high |

The CSV `site` "Rani Kamlapati ghat / Kamla Park kund" is mapped by `festival`: Ganesh → `kamla_park_kund`, Durga → `rani_kamlapati_ghat`.

## Scopes

- `all`: every year and festival
- `durga`: Durga rows only
- `ganesh`: Ganesh rows only

`kamla_park_kund` appears only in `all` and `ganesh`. `rani_kamlapati_ghat` appears only in `all` and `durga`. So `all` has 8 rows, `durga` has 7 and `ganesh` has 7.

## Tiers and rank

- `fail_rate = fails / n`, where `n` counts numeric pH + DO + BOD readings in scope.
- `durga_2025_missing` = the ghat has no Durga 2025 table. This is true for `bairagarh` and `malikhedi`.
- **Tier 1:** `fail_rate >= 0.50` OR `durga_2025_missing`. The second condition applies in every scope, because the upcoming festival is Durga.
- **Tier 2:** `0.40 <= fail_rate < 0.50`
- **Tier 3:** `fail_rate < 0.40`
- **Rank:** sort by tier ascending, then `fail_rate` descending, then `worst_DO` ascending. Rank is 1..N.
- **Near tie:** if two adjacent rows in the same tier differ by less than 0.02 (2 percentage points) in `fail_rate`, set `near_tie: true` on both. The UI then shows them as "tied in Tier X" instead of ordering them by rank number.

## Top-level structure

```jsonc
{
  "meta": { ... },
  "kpis": [ ... ],
  "ranking": { "all": [ ... ], "durga": [ ... ], "ganesh": [ ... ] },
  "alerts": [ ... ],
  "insights": [ ... ],
  "evidence": [ ... ],
  "coverage": [ ... ],
  "limitations": [ "string", ... ],
  "brief": { ... }          // OPTIONAL. Added by build step from brief.py output; absent in raw ranking.json
}
```

### `meta`
| field | type | notes |
|---|---|---|
| `generated_on` | string `YYYY-MM-DD` | date the script ran |
| `durga_visarjan_date` | string | `"2026-10-20"` |
| `days_to_durga` | int | `(2026-10-20 − generated_on).days`. Can be ≤ 0 after the date |
| `class_b_limits` | object | read from CPCB csv: `{"DO": {"type":"min","value":5,"unit":"mg/l"}, "BOD": {"type":"max","value":3,"unit":"mg/l"}, "pH": {"type":"range","min":6.5,"max":8.5,"unit":""}}` |
| `source_csv` | string | `"data/bhopal_ghats_2023_2025.csv"` |
| `years` | int[] | `[2023, 2024, 2025]` |
| `ghats` | object[] | `[{id, name, site_group, water_body, site_match}]`, the 8 rows above |
| `schema_version` | string | `"1.0"` |

### `kpis[]` (exactly 6, in this order)
| field | type |
|---|---|
| `id` | string |
| `label` | string (English) |
| `value` | number |
| `n` | int or null (denominator) |
| `scope` | `"all"` |
| `evidence_ids` | string[] (may be long; fine) |

Required ids:
1. `days_to_durga`: value = meta.days_to_durga, n = null
2. `do_below_5`: value = 42, n = 116
3. `bod_above_3`: value = 100, n = 112
4. `ph_out_of_range`: value = 6, n = 115
5. `do_zero`: value = 4, n = 116
6. `ghats_no_durga_2025`: value = 2, n = 7 (Bhopal sites in the CSV)

(Values are what the real CSV should produce. `score.py` must compute them, not hard-code them.)

### `ranking.<scope>[]`
| field | type | notes |
|---|---|---|
| `ghat` | string | ghat id |
| `name` | string | display name |
| `site_group` | string | |
| `rank` | int | 1..N |
| `tier` | 1 \| 2 \| 3 | |
| `near_tie` | bool | |
| `fail_rate` | number | 0-1, rounded to 3 decimals |
| `fails` | int | |
| `n` | int | numeric pH + DO + BOD readings |
| `per_param_fails` | object | `{"DO": {"fails":int,"n":int}, "BOD": {...}, "pH": {...}}` |
| `worst_DO` | object or null | `{"value": number, "evidence_id": string}`, the lowest DO in scope |
| `durga_2025_missing` | bool | |
| `reason_en` | string | one or two plain sentences with numbers, e.g. "11 of 13 DO readings were below 5 mg/l, including 4 readings of zero. No Durga 2025 table in the report." |
| `action` | string | one of the fixed action strings below |
| `confidence` | object | see below |
| `evidence_ids` | string[] | all evidence rows behind this row (numeric and missing) |

`action` (exact strings):
- Tier 1 with `durga_2025_missing`: `"Test before, during and after Durga visarjan (no 2025 Durga data). Keep aeration and cleaning on standby."`
- Tier 1 otherwise: `"Priority: arrange aeration and extra cleaning, and test water before, during and after visarjan."`
- Tier 2: `"Watch: test during and after visarjan, and plan cleaning after immersion."`
- Tier 3: `"Routine: standard monitoring. Readings are still outside limits at times."`

`confidence`:
| field | type | notes |
|---|---|---|
| `n_readings` | int | same as `n` |
| `missing_festivals` | string[] | e.g. `["Durga 2025"]`, or phase-level like `"Ganesh 2025 pre/after (not sampled)"` |
| `site_match` | `"high"` \| `"medium"` | |
| `notes` | string[] | e.g. `"Enclosed kund: conductivity up to 1882, unlike lake water"`, `"Ganesh and Durga tables may describe two different places"` |
| `level` | `"high"` \| `"medium"` \| `"low"` | `low` if any festival table is missing, or n < 15 in scope; `medium` if site_match is medium or phases are missing; else `high` |

### `alerts[]`
| field | type | notes |
|---|---|---|
| `id` | string | e.g. `"A01"` |
| `severity` | `"critical"` \| `"warning"` \| `"data"` | |
| `rule_id` | string | from the list below |
| `ghat` | string | ghat id |
| `text_params` | object | the numbers used in the text |
| `text_en` | string | rendered sentence (score.py renders it from its own template) |
| `evidence_ids` | string[] | |
| `scope` | string | `"all"` unless the rule is festival-specific |

Rules:
| rule_id | severity | condition |
|---|---|---|
| `DO_ZERO` | critical | any DO reading == 0 at the ghat (one alert per ghat, listing all) |
| `DURGA_MISSING` | data | no Durga 2025 table for the ghat |
| `DO_FAIL_MAJORITY` | critical | DO fails / DO n > 0.5 (scope all) |
| `BOD_ALL_FAIL` | warning | BOD fails == BOD n, and n > 0 (scope all) |
| `PH_OUT` | warning | any pH outside 6.5-8.5 (one per ghat, listing all) |
| `SUSPECT_DO_BOD` | data | same sample has DO > 9 and BOD > 15 (wording: "unusual combination, check the report"; do not call it wrong) |
| `SITE_TWO_PLACES` | data | one alert for the Rani Kamlapati / Kamla Park group (ghat = `rani_kamlapati_ghat`) |

### `insights[]`
| field | type | notes |
|---|---|---|
| `id` | string | `"I01"` ... |
| `template_id` | string | e.g. `BASELINE_ALREADY_HIGH`, `BOD_EVERYWHERE`, `WORST_DO_SITES`, `DURGA_VS_GANESH`, `DATA_GAP_WORST_SITES`, `ONLY_DURING_2025` |
| `params` | object | numbers used |
| `text_en` | string | rendered |
| `evidence_ids` | string[] | |

Insights must be descriptive only, with no causal claims. For example: "BOD was already above 3 mg/l before immersion in 32 of 37 pre-immersion readings." Do not write "immersion caused".

### `evidence[]`
One row per CSV row where parameter ∈ {pH, Dissolved oxygen, BOD} (360 rows), **plus** synthetic `no_table` rows for each (ghat, year, festival, phase, parameter) that has no CSV row at all: bairagarh and malikhedi Durga 2025 × 3 phases × 3 params = 18 rows. Total 378.

| field | type | notes |
|---|---|---|
| `id` | string | `E-{year}-{G\|D}-{ghat}-{pre\|during\|after}-{DO\|BOD\|pH}`, e.g. `E-2023-D-bairagarh-pre-DO` |
| `ghat` | string | ghat id |
| `year` | int | |
| `festival` | `"Ganesh"` \| `"Durga"` | |
| `phase` | `"pre"` \| `"during"` \| `"after"` | |
| `parameter` | `"DO"` \| `"BOD"` \| `"pH"` | |
| `value` | number or null | |
| `value_as_printed` | string | from CSV (`""` for no_table) |
| `limit` | string | human-readable: `"≥ 5"`, `"≤ 3"`, `"6.5–8.5"` |
| `status` | `"fail"` \| `"within_limit"` \| `"missing"` \| `"no_table"` | `missing` = CSV row exists but no number (not sampled / `*` / `**` / `_`) |
| `source_report` | string or null | PDF filename: 2023 `Idol_immer._Report_23_CPCB.pdf`, 2024 `Ganesh_and_Durga_visarjan_report-2024.pdf`, 2025 `Ganesh_and_Durga_visarjan_report-2025.pdf` |
| `source_page` | int or null | null for no_table |
| `source_url` | string or null | relative to the repo-root `index.html`: `"resources/<file>#page=<n>"`. For no_table: `"resources/Ganesh_and_Durga_visarjan_report-2025.pdf"` (no page) |

### `coverage[]`
One row per (ghat id, year, festival, phase) over the full grid: 8 ghat ids, but `kamla_park_kund` is Ganesh only and `rani_kamlapati_ghat` is Durga only. So 6 ghats × 3 years × 2 festivals × 3 phases + 2 × 3 × 1 × 3 = 108 + 18 = **126 rows**.

| field | type | notes |
|---|---|---|
| `ghat`, `year`, `festival`, `phase` | | |
| `status` | `"numeric"` \| `"bdl"` \| `"missing"` \| `"no_table"` | Based on the **13 parameters**: `no_table` if no CSV rows; `missing` if rows exist but 0 numeric and 0 BDL; `bdl` if 0 numeric but ≥1 BDL; else `numeric` |
| `n_numeric`, `n_bdl`, `n_missing` | int | counts over the 13 parameters |
| `ranking_params_numeric` | int | 0-3, how many of pH/DO/BOD are numeric |

### `limitations[]`
Plain English strings. It must include at least these points:
- Only pH, DO and BOD have class B limits. Total coliform (also class B) was not tested, so no site can be said to meet class B.
- Pre-immersion readings already exceed limits often, so the data does not show that immersion caused them.
- Units are not printed in the reports; standard units are assumed.
- One grab sample per phase; no replicates, times or temperatures.
- Bairagarh and Malikhedi have no Durga 2025 table, and only "during" readings for Ganesh 2025.
- Rani Kamlapati / Kamla Park may be two places; shown separately.
- 2025 metal values of 0.03 / 0.031 repeat across sites and may be detection limits. Metals are not used for ranking.
- Latest data is 2025; nothing here predicts conditions on 20 October 2026.
- The brief is in English only; a Hindi brief has not been produced.

### `brief` (optional, added by build)
| field | type |
|---|---|
| `text_en` | string (plain text, newline-separated, ready to copy) |
| `generated_on` | string |
| `scope` | `"durga"` |

## File ownership

| Agent | Writes only |
|---|---|
| Orchestrator | `schema.md`, `fixture.json`, `build.py`, `BUILD-LOG.md` |
| A1 Scoring | `score.py`, `ranking.json` |
| A2 Frontend | `index.html` (repo root), `ghatwatch/vendor/` |
| A3 Brief | `brief.py`, `brief_templates.json` (and its output `brief.json`) |
| A4 Verifier | `VERIFY-REPORT.md` |
| A5 Docs | `README.md`, `LICENSE`, `.gitignore` (repo root) |

Anyone may append questions or status lines to `BUILD-LOG.md`.

## Embedding (build step)

`index.html` lives at the **repo root** (so a static host can serve the repo root and the `resources/` PDFs together). It loads its libraries from `ghatwatch/vendor/`. It must contain exactly one block:
```html
<script id="ghatwatch-data" type="application/json">
/*DATA_START*/{ ...fixture or ranking JSON... }/*DATA_END*/
</script>
```
`build.py` replaces the text between `/*DATA_START*/` and `/*DATA_END*/` with `ranking.json`, plus `brief` from `brief.json` and `coords` from `ghat_coords.json` if they exist. `coords` is optional map data, `{lakes:[{name,lat,lng,source}], ghats:[{id, lat|null, lng|null, approximate:true, location_status:"approximate"|"unverified", basis}]}`. It never affects ranking. The page parses it with `JSON.parse(text.replace('/*DATA_START*/','').replace('/*DATA_END*/',''))`. No fetch, no server, and it works from `file://`.

Pipeline: `python ghatwatch/score.py` → `python ghatwatch/brief.py` → `python ghatwatch/build.py`.
