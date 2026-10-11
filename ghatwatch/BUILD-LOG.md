# BUILD-LOG

## Phase 0: Contract (15:15)
- Done: `schema.md` (contract + common rules + file ownership + embed markers) and `fixture.json` (3 ghats, tiers 1/2/3, Bairagarh Durga 2025 = no_table).
- Decision: Rani Kamlapati is split into `kamla_park_kund` (Ganesh) and `rani_kamlapati_ghat` (Durga), with a shared `site_group` so the combined 24/54 can still be checked.

## Questions / assumptions (agents append below)

## Phase 1: Parallel build (15:20)
- Launched A1 (score.py → ranking.json), A2 (index.html + vendor/Chart.js) and A3 (brief.py + brief_templates.json) in parallel against the schema and fixture.
- Orchestrator added `build.py` (embeds ranking.json + brief.json between the DATA markers). Pipeline: score → brief → build.
- A3 (brief): Q: how many ghats in the brief, and what if near_tie partner is outside the top list? Assumption: top 3 of ranking.durga by rank; tie shown as "(tied with X)" if an adjacent near_tie row in the same tier exists, else "(tied)".
- A3 (brief): Q: "Durga 2025" year in brief text. Assumption: taken from max(meta.years), not hard-coded. Partial gaps = Durga rows with non-empty confidence.missing_festivals ("not sampled"). Ghat lines show a short action label; full deduplicated action strings are listed under "Recommended actions". days_to_durga <= 0 renders "today" / "date has passed".

### A1 Scoring (score.py)
- Q: Should `confidence.missing_festivals` list "Durga 2025" in the `ganesh` scope too? Assumption: yes, for bairagarh/malikhedi in every scope (same as the Tier 1 rule), so their level is `low` everywhere.
- Q: Does a missing single parameter (e.g. Prempura Durga 2023 BOD, Khatlapura Durga 2023 during BOD) count as "phases missing"? Assumption: yes, it lowers confidence to `medium` and is listed in `notes`. `missing_festivals` only lists whole phases/tables.
- Q: The fixture's DURGA_MISSING text says "not a clean result" (banned word). Assumption: score.py uses "Missing data is not counted as within the limit" instead.
- Added extra insight `DO_BY_PHASE` (descriptive: DO < 5 by phase 12/38, 18/40, 12/38) and two extra limitation lines (missing never counted; values at the limit count as within).

### A2 Frontend (index.html)
- Q: Are alerts/heatmap/DO dot plot scope-aware? Assumption: yes. Alerts show when alert.scope is "all" or matches the current scope; the heatmap and DO plot filter by festival; KPIs are always scope "all", as the schema says.
- Q: How should the heatmap show a (ghat, year, festival, phase) cell with no coverage row (the fixture has gaps)? Assumption: a white dashed "?" cell ("no coverage row in this data"), never coloured as numeric. Kamla Park in Durga columns and Rani Kamlapati in Ganesh columns show as "·" (not applicable).
- The JS builds the marker strings by concatenation ("/*DATA_" + "START*/"), so the literal markers appear exactly once in index.html. build.py can safely split on the first occurrence.
- Status: index.html + vendor/chart.umd.js (Chart.js 4.5.1, local) are done; tested headless in Chrome with no JS errors.

## Phase 2: Integrate (15:40)
- Pipeline ran end to end (score → brief → build). The real ranking.json (223 KB) is embedded with brief=True. No schema mismatches between A1, A2 and A3 (keys checked).
- Edge headless screenshot (scratch/shots/full.png): Durga scope renders tiers, 14 alerts, 4 charts, hatched no_table cells for Bairagarh/Malikhedi Durga 2025, the brief and limitations. Fixture banner is hidden on real data.

## Phase 3: Verify + Docs (15:55)
- A4 VERIFY-REPORT.md: 9/9 PASS (42/116, 100/112, 6/115, 148/343, ghat-wise totals, no_table handling, 10/10 evidence rows match the CSV and PDF, no banned words, no secrets in ghatwatch/).
- A5 wrote README.md, LICENSE (MIT) and .gitignore (ignores scratch/ and CLAUDE.md, because the local file holds a secret).

## Phase 4: Fix + finalize (16:00)
- No ghatwatch fixes needed. Only remaining warning: the root CLAUDE.md API key. It is gitignored; the user must revoke the key. Ready to push after the user fills in the team name/members in README and LICENSE.

## Redesign: index.html v2 (16:25)
- index.html is now 3 tabs (Analysis / Actions & Insights / Map) with a navy top bar and card layout. The scope toggle drives all tabs. ranking.json and score.py are unchanged (Bairagarh 24/39 all-scope, 12/18 Durga).
- Added `ghat_coords.json` and an optional `coords` key embedded by build.py (schema.md updated). Leaflet 1.9.4 is vendored in `vendor/leaflet/`. Khatlapura, Hathaikheda and Malikhedi are "location unverified" and not placed on the map.
- NOTE FOR README (extra data section): map positions come from OpenStreetMap Nominatim search (https://nominatim.openstreetmap.org, © OpenStreetMap contributors, ODbL), queried 2026-10-11. Base tiles are OSM standard tiles (https://tile.openstreetmap.org), loaded online only; markers still show offline. VERIFY-REPORT test 7 ("no http") now has one intended exception: the OSM tile URL.

## Map basemap fix (16:45)
- Keyless OSM tiles return "Access blocked" and CARTO returns "API KEY REQUIRED". Both come back as 200 OK images, so errorTileUrl never fires. The user chose: no tile server. The map now draws OSM lake outlines (Upper, Lower, Shahpura; Nominatim polygon_geojson, ODbL, simplified) embedded in ghat_coords.json, on a plain background. Fully offline, and the page makes no external requests. README extra-data section updated.

## Map v3: Esri tiles + fixed circles (17:00)
- Basemap is Esri World Light Gray (keyless, "Tiles © Esri"), with errorTileUrl + a plain background fallback (tested with the network blocked). Lake polygons are no longer drawn, only name labels; the geojson stays in ghat_coords.json unused.
- Each placed ghat gets an L.circle with a fixed 350 m radius, fillOpacity 0.35, colour = tier (dark red / orange / amber). No Durga 2025 table = hatched grey (SVG pattern). No readings in scope = dashed hollow. Opens at zoom 13 (at zoom 12 a 350 m circle is only ~9 px). Ghats without coordinates are shown in a warning strip above the map. Tab renamed "Map (approximate)". README credits updated.

## Visual polish, Step 1: what looks weak (before shots: scratch/shots/before-*.png)
- Hierarchy: all 10 KPI cards have equal weight and a 26px number, so the eye has nowhere to land. The 6+4 wrap leaves a ragged hole, and label text competes with the numbers.
- Ranking: 12px bars on long grey tracks, a weak "#1" rank, and the % sits far right, away from its bar. The tier headers are low-contrast grey strips.
- Typography: the system Segoe stack with a flat scale. Section titles (15px) are barely bigger than body text, and muted grey text is low contrast.
- Cards: flat white boxes with one faint shadow and no depth or surface hierarchy. The dark summary banner on Actions feels heavy next to them.
- Colour: one accent blue is used for toggles, chips, sparklines and links, which dilutes it. The BOD series and the Ganesh lines are teal, which reads as green.
- Motion: none. Tabs and scope switch instantly, numbers just appear, and bars and charts pop in. Tooltips are native browser titles (heatmap, chips).
- Actions: chips are visually noisy, and alert rows are a long undifferentiated list. Critical alerts don't stand out from warnings.

## Visual polish, Step 3: what changed (after shots: scratch/shots/after-*.png)
- Design tokens at the top of index.html (type scale, colours, radii, 3 shadow levels, spacing, durations, easings). Inter Variable is bundled offline in vendor/fonts/ (OFL licence included).
- Hierarchy: 3 hero KPI cards (dark countdown card, Tier 1 count, highest-ranked ghat), then a 7-up metric row with meters built from the same f/n numbers. Ranking rows get tier-coloured rank badges, 14px gradient bars and larger percentages.
- Motion: count-ups that end on the exact data text (checked after the animation: 9, 4, 25/57, 50/53, 1, 2, 88%, 17, 2), bars that grow in, staggered card entrance, sliding tab and scope indicators, panel and scope cross-fades, Chart.js 650 ms animations, a blurred scrim with a slide-in drawer, and custom tooltips replacing native titles. The only loop is the pulse dot on Critical badges. prefers-reduced-motion turns all of it off.
- Colour: the BOD series and the Ganesh lines were teal (reads as green), now magenta and violet. The palette was validated (adjacent pairs pass CVD and normal-vision checks). No green anywhere. The no-data hatch, "No Durga 2025 table", "Confidence low", legends and limitations are unchanged.
- Numbers unchanged: Bairagarh Durga 12 of 18, and all ranking rows match ranking.json. Data, score.py and ranking.json were not touched.

## index.html moved to repo root (17:20)
- `index.html` now sits at the repo root, so a static host can publish the repo root (`./`) with the `resources/` PDFs and no redirect. Library and font paths changed to `ghatwatch/vendor/...`. score.py now writes `source_url` as `resources/<file>#page=N` (schema.md updated), and build.py writes to `../index.html`. Rebuilt: kpis 42/116, 100/112, 6/115, 4, 2/7 unchanged; Bairagarh 24/39 all, 12/18 Durga.
