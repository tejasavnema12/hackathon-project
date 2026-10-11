# GhatWatch verification report (A4)

Run on 2026-10-11. Read-only checks; scripts in `scratch/verify/v.py`. Inputs: `data/bhopal_ghats_2023_2025.csv`, `data/cpcb_water_quality_criteria.csv`, `ghatwatch/ranking.json`, `ghatwatch/index.html`, `ghatwatch/brief.json`, PDF text in `scratch/pdftext/`.

## Summary

| # | Test | Result | Key numbers |
|---|---|---|---|
| 1 | Strict-limit counts from CSV and KPIs | PASS | DO<5 42/116, BOD>3 100/112, pH out 6/115, DO==0 4 (all Bairagarh). KPIs match. |
| 2 | Total fails / readings | PASS | CSV 148/343; ranking.all sum 148/343 |
| 3 | Ghat-wise fails/n (all scope) | PASS | Bairagarh 24/39, Malikhedi 20/39, Khatlapura 24/53, Rani Kamlapati 12/27 + Kamla Park 12/27 = 24/54, Shahpura 23/54, Hathaikheda 19/54, Prempura 14/50 |
| 4 | Bairagarh/Malikhedi Durga 2025 no_table | PASS | coverage no_table x3 phases each; 18 no_table evidence rows; Tier 1 in all/durga/ganesh; 0 missing/no_table rows with a value or counted in n |
| 5 | 10 random evidence rows vs CSV and PDF | PASS | 10/10 match CSV value, printed value and page; 10/10 token on PDF page |
| 6 | Banned words | PASS | Only 3 hits, all the allowed "Missing is not clean / not a clean result"; "cleaning" (action) allowed |
| 7 | Secrets and network calls | PASS (WARNING at repo root) | 0 secret hits in ghatwatch/; no fetch/requests/urllib/http in .py/.html; repo-root CLAUDE.md contains an Anthropic API key |
| 8 | Embedding, Devanagari, evidence ids, counts, limits | PASS | 1 DATA pair; embedded = ranking.json + brief; 0 Devanagari; 1479 refs, 0 dangling; evidence 378, coverage 126; limits match CPCB class B |
| 9 | Static check of score.py limits | PASS | Limits read from CPCB csv class B rows; `v < DO_MIN`, `v > BOD_MAX`, `v < PH_LO or v > PH_HI` |

## Details

### 1. Strict-limit counts
Own pandas code, numeric values only, over the 360 rows with parameter in {pH, Dissolved oxygen, BOD}:
- DO < 5: 42 of 116. BOD > 3: 100 of 112. pH < 6.5 or > 8.5: 6 of 115.
- DO == 0: 4 rows, all at site "Bairagarh (Sant Hirdaram) kund".
- ranking.json kpis: days_to_durga 9 (n null), do_below_5 42/116 (42 evidence ids), bod_above_3 100/112 (100 ids), ph_out_of_range 6/115 (6 ids), do_zero 4/116 (4 ids), ghats_no_durga_2025 2/7 (18 ids). All match. Also checked every numeric evidence row's status against the strict rule: 0 mismatches.

### 2. Totals
Own count: 148 fails of 343 numeric readings. Sum over ranking.all: fails 148, n 343. Evidence status counts: fail 148, within_limit 195, missing 17, no_table 18 (total 378).

### 3. Ghat-wise (scope all)
| Ghat | CSV fails/n | ranking.json | tier | fail_rate |
|---|---|---|---|---|
| Bairagarh | 24/39 | 24/39 | 1 | 0.615 |
| Malikhedi | 20/39 | 20/39 | 1 | 0.513 |
| Khatlapura | 24/53 | 24/53 | 2 | 0.453 |
| Rani Kamlapati ghat (Durga) | — | 12/27 | 2 | 0.444 |
| Kamla Park kund (Ganesh) | — | 12/27 | 2 | 0.444 |
| (combined group) | 24/54 | 24/54 | | |
| Shahpura | 23/54 | 23/54 | 2 | 0.426 |
| Hathaikheda | 19/54 | 19/54 | 3 | 0.352 |
| Prempura | 14/50 | 14/50 | 3 | 0.280 |

Also re-derived fails/n for every ranking row in all three scopes from the evidence rows (fail + within_limit only): 0 mismatches. Near-tie flags look consistent with the 0.02 rule (for example durga: Shahpura 0.519 / Khatlapura 0.500 both near_tie, Tier 1).

### 4. Missing Durga 2025 tables
- coverage: bairagarh and malikhedi, 2025 Durga, pre/during/after: all `no_table`.
- evidence: 18 `no_table` rows (9 bairagarh, 9 malikhedi), all 2025 Durga, value null, source_page null.
- Tier 1 in all (ranks 1, 2), durga (1, 2) and ganesh (1, 2; Malikhedi Ganesh rate 0.429 is Tier 1 only because of durga_2025_missing, as the schema requires). confidence.level = low.
- No evidence row with status missing/no_table has a non-null value; none is counted in any ranking n.
- UI: `STATUS_TXT` maps `missing` to "not sampled" and `no_table` to "no table in report", grey/hatched classes; charts only plot `fail`/`within_limit`. No path shows them as within limit.

### 5. Random evidence rows (random.seed(7), random.sample(evidence, 10), resampled until fail, within_limit and missing were all present)
| Evidence id | status | value | printed | CSV value / printed | report, page | CSV match | token on PDF page |
|---|---|---|---|---|---|---|---|
| E-2025-G-hathaikheda-during-BOD | fail | 10 | 10 | 10.0 / 10 | 2025 report p29 | yes | yes |
| E-2025-G-malikhedi-after-pH | missing | null | ** | NaN / ** | 2025 report p29 | yes | yes ("**"; site "maalikhedi" also on page) |
| E-2024-G-bairagarh-after-DO | fail | 4.2 | 4.2 | 4.2 / 4.2 | 2024 report p69 | yes | yes |
| E-2023-G-prempura-during-BOD | within_limit | 1.5 | 1.5 | 1.5 / 1.5 | 2023 CPCB p26 | yes | yes |
| E-2023-D-shahpura-after-DO | within_limit | 5 | 5 | 5.0 / 5 | 2023 CPCB p60 | yes | yes (DO = 5 is correctly within limit) |
| E-2023-G-prempura-after-DO | within_limit | 6.5 | 6.5 | 6.5 / 6.5 | 2023 CPCB p26 | yes | yes |
| E-2025-G-kamla_park_kund-pre-BOD | fail | 3.8 | 3.8 | 3.8 / 3.8 | 2025 report p29 | yes | yes |
| E-2023-D-hathaikheda-after-DO | within_limit | 8.6 | 8.6 | 8.6 / 8.6 | 2023 CPCB p59 | yes | yes |
| E-2024-D-khatlapura-during-DO | fail | 4.5 | 4.5 | 4.5 / 4.5 | 2024 report p24 | yes | yes |
| E-2024-G-prempura-during-BOD | fail | 6.8 | 6.8 | 6.8 / 6.8 | 2024 report p70 | yes | yes |

source_url follows `../resources/<file>#page=<n>` in all 10.

### 6. Banned words (case-insensitive, word boundary: safe, unsafe, healthy, unhealthy, clean, disease, illness, fish death)
- index.html line 171 (UI): "Grey/hatched = not sampled / no table. Missing is not clean." (allowed)
- index.html line 217 (embedded brief): "... Bairagarh (Sant Hirdaram) kund and Malikhedi kund. Missing is not a clean result." (allowed)
- brief.json: same sentence as above (allowed)
- ranking.json: 0 hits.
- "cleaning" (action word, allowed): index.html 17, ranking.json 15, brief.json 2.
- Extra: "skin" and "dangerous" also 0 hits in the three outputs.
- Source files (not outputs): brief.py and score.py contain the words only inside their own banned-word lists; score.py line 88 docstring "Clean number for JSON". Not user-facing.

### 7. Secrets and network
- ghatwatch/ (excluding vendor/chart.umd.js): 0 hits for sk-ant, sk-, api_key, apikey, x-api-key, token, secret, password, Bearer.
- vendor/chart.umd.js: 0 hits for the same terms; contains 2 `https://` strings in its license header (chartjs.org, github.com/kurkle/color). Comments only, not network calls. Noted, not failed.
- No `fetch(`, `XMLHttpRequest`, `requests`, `urllib`, `http://`/`https://` in any ghatwatch .py or index.html. index.html loads only `vendor/chart.umd.js` (local) and links to `../resources/*.pdf` (local relative).
- **WARNING (outside ghatwatch):** `D:\hackathon-claude\water\CLAUDE.md` contains an Anthropic API key (`sk-ant-...`) and a curl example using it. The repo has no `.git` yet and no `.gitignore`. This file must not be committed or pushed; the key should be revoked/rotated and CLAUDE.md excluded (A5 .gitignore) or cleaned before publishing.

### 8. Extra checks
- index.html: exactly 1 `/*DATA_START*/` and 1 `/*DATA_END*/`.
- Embedded JSON parses; keys meta, kpis, ranking, alerts, insights, evidence, coverage, limitations, brief. Without `brief` it equals ranking.json exactly; `brief` equals brief.json exactly.
- Devanagari (U+0900–U+097F): 0 hits in every file under ghatwatch/ (including vendor).
- Evidence id references from kpis, ranking (evidence_ids + worst_DO), alerts, insights: 1479 refs, 0 not in evidence. 378 unique evidence ids.
- len(evidence) = 378, len(coverage) = 126.
- meta.class_b_limits: pH range 6.5–8.5, DO min 5 mg/l, BOD max 3 mg/l; matches CPCB csv class B rows.
- meta: generated_on 2026-10-11, days_to_durga 9, durga_visarjan_date 2026-10-20.

### 9. score.py static review
- `read_limits()` reads `data/cpcb_water_quality_criteria.csv`, filters class == "B", parses pH "6.5-8.5", DO and BOD values and types; asserts DO is min and BOD is max.
- `is_fail`: `v < DO_MIN`, `v > BOD_MAX`, `v < PH_LO or v > PH_HI` (strict). No hard-coded 5 / 3 / 6.5 / 8.5 in the scoring logic (only in a limitations text string). Tier thresholds 0.5 / 0.4 and near-tie 0.02 match the schema.
- Not executed (would write project files).

## Fixes needed

No ghatwatch failures.

- WARNING (not owned by any ghatwatch agent; user/orchestrator): repo-root `CLAUDE.md` contains a live-looking Anthropic API key. Revoke the key, and remove CLAUDE.md from anything pushed (add it to the root `.gitignore`, owned by A5, before the first `git add`).

OVERALL: PASS
