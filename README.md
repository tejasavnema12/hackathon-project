# GhatWatch

**One-line pitch:** GhatWatch turns three years of MPPCB visarjan water-test reports into a ranked, evidence-linked list of Bhopal ghats, so the officer planning Durga visarjan knows where to send extra cleaning, aeration and water testing first.

- **Team name:** `<TEAM NAME>`
- **Members:** `<member 1>`, `<member 2>`, `<member 3>`, `<member 4>`
- **Track:** Track 2 – Visarjan Ghat Watch (Claude Impact Lab × Cerebras, Bhopal)

## The one user

The **Bhopal Municipal Corporation (BMC) officer who plans Durga visarjan at the ghats**. Before **20 October 2026** this officer has to decide which ghats get extra cleaning, aeration and water testing. GhatWatch is built for that one decision.

## What it does

- **Ranked tiers with plain-English reasons.** Each ghat is placed in Tier 1 (priority), Tier 2 (watch) or Tier 3 (routine), with a short reason such as "6 of 6 DO readings were below 5 mg/l, including 2 readings of zero ... No Durga 2025 table in the report." (Bairagarh, Durga scope), and a fixed recommended action.
- **Every number links to its source.** Click a ghat or a number to open the evidence drawer: each reading shows the report and page it came from, and the link opens the original PDF in `resources/` at that page.
- **Coverage view.** A grid of ghat × year × festival × phase. Missing data is shown as missing (hatched, "not sampled" or "no table in report"), never coloured as a pass.
- **Alerts.** Rule-based alerts (critical / warning / data gap), for example zero dissolved oxygen recorded, or no Durga 2025 table.
- **Charts.** Fail rate by ghat, DO readings against the 5 mg/l limit and more (Chart.js, works offline).
- **Scope toggle.** Durga only / Ganesh only / All festivals.
- **Copy-ready English brief.** A short brief for the officer's file or message, with one copy button.

## How to run (5 steps)

The prebuilt `index.html` (repo root) already works without running anything: just do step 5.

1. Clone the repo: `git clone <this repo URL>` and `cd` into it.
2. Install the one dependency (Python 3.10+): `pip install pandas`
3. Score the data: `python ghatwatch/score.py` (writes `ghatwatch/ranking.json`)
4. Make the brief and build the page: `python ghatwatch/brief.py` then `python ghatwatch/build.py` (embeds the data into `index.html`)
5. Open `index.html` (repo root) in a browser. It works offline straight from disk; the PDF evidence links open `resources/*.pdf` at the right page.

Windows note: if the console shows an encoding error, first run `set PYTHONIOENCODING=utf-8` (cmd) or `$env:PYTHONIOENCODING="utf-8"` (PowerShell).

## How the ranking works

- **Standard used: CPCB class B (outdoor bathing).** People bathe and immerse idols at these ghats, so outdoor bathing is the closest designated use. Limits are read at runtime from `data/cpcb_water_quality_criteria.csv`.
- **Only pH, DO and BOD have class B limits** in the data, so only these three affect rank. The other parameters (metals, conductivity, turbidity, etc.) are shown but never ranked.
- **Strict inequality:** a reading fails if DO < 5 mg/l, BOD > 3 mg/l, or pH is outside 6.5–8.5. A value exactly at the limit (DO = 5.0, BOD = 3.0) counts as within the limit.
- **Fail rate = fails / numeric readings** (pH + DO + BOD) in the chosen scope. Missing readings are counted in neither number.
- **Tiers:**
  - **Tier 1:** fail rate ≥ 50%, OR the ghat has no Durga 2025 table (the upcoming festival is Durga, so a gap is treated as a priority, not as a pass).
  - **Tier 2:** fail rate from 40% up to (not including) 50%.
  - **Tier 3:** fail rate below 40%.
  - Order inside a tier: higher fail rate first, then lowest DO.
  - **Near ties:** adjacent ghats in the same tier within 2 percentage points are shown as tied, not as one ranked above the other.
- **Key numbers (all Bhopal readings, 2023–2025):**
  - DO below 5 mg/l: **42 of 116** readings
  - BOD above 3 mg/l: **100 of 112** readings
  - pH outside 6.5–8.5: **6 of 115** readings
  - Total: **148 of 343** readings outside the class B limit

## Assumptions

- **Class B** (outdoor bathing) is the right comparison standard (see above).
- **Strict inequality:** values exactly at a limit count as within the limit.
- **Rani Kamlapati / Kamla Park are shown as two separate points.** The Ganesh tables say "Kamla Park kund"; the Durga tables say "Lower Lake ghat". We cannot confirm they are the same spot, so they are listed separately (combined: 24 of 54 readings outside the limit).
- **2025 metal values 0.03 / 0.031** repeat across every ghat and phase and are probably detection limits printed as numbers. Metals are not used for ranking anyway.
- **Units are assumed** (mg/l etc.). The reports print none.
- **Missing, "not sampled" and "no table" are never treated as passing.** They are shown as gaps and can push a ghat up (Tier 1 rule), never down.

## What works and what does not

**Works**
- Offline dashboard: a single `index.html` with the data embedded; opens from disk, no server.
- Scope toggle: Durga / Ganesh / All.
- Evidence drawer with report + page links that open the source PDF at the right page.
- English brief with a copy button.
- Deterministic pipeline: same CSV in, same output out.
- No API keys, no LLM calls at runtime.

**Does not work / not done**
- No Hindi brief yet.
- No map of ghat locations.
- No data for the new BMC immersion ghats (no test results exist in the provided files).
- The statewide file (`mp_immersion_sites_2023_2025.csv`) is not used.
- No automated PDF re-parsing: GhatWatch relies on the organiser-provided CSV.
- The 5-test acceptance verification is recorded separately; see `ghatwatch/VERIFY-REPORT.md` for what passed and what did not.

## Limitations

- Brief English me hai, Hindi brief abhi nahi bana. (The brief is in English; a Hindi brief has not been made yet.)
- **Coliform is a class B limit but was not tested** in these reports, so no site can be said to meet class B. GhatWatch only says "outside" or "within" the limit for pH, DO and BOD.
- **Pre-immersion readings already exceed the limits**, so the data does not show that immersion caused them.
- **One grab sample per phase** (before, during, after). A single reading may not be representative.
- **Bairagarh and Malikhedi have no Durga 2025 table** in the report; they are in Tier 1 because of that gap.
- **No health claims are made.** The tool reports readings against limits only.
- **The latest data is 2025.** Nothing here predicts conditions on 20 October 2026; it shows where problems were recorded before.

## Data used

Only the files provided by the organisers in `data/` and `resources/` (source: https://github.com/Laaaaksh/bhopal-impact-lab-2026, folder `tracks/02-visarjan-ghat-watch`).

`data/`
- `bhopal_ghats_2023_2025.csv`: the only source of readings used for ranking
- `cpcb_water_quality_criteria.csv`: CPCB class limits (class B rows used), from https://cpcb.gov.in/water-quality-criteria/
- `sample_bhopal_2025.csv`, `mp_immersion_sites_2023_2025.csv`, `DATA_DICTIONARY.md`: provided, not used for ranking

`resources/` (original reports; evidence links point here)
- `Ganesh_and_Durga_visarjan_report-2025.pdf`: https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2025.pdf
- `Ganesh_and_Durga_visarjan_report-2024.pdf`: https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2024.pdf
- `Idol_immer._Report_23_CPCB.pdf`: https://www.mppcb.mp.gov.in/proc/mon/Idol_immer._Report_23_CPCB.pdf
- `Upper_Lower_Lake_monthly_2025-26_from_xgn.pdf`: https://xgn.mp.nic.in/File_Upload/MONITORING//Yearly%20Water%20Quality%20Status/2026/July/UPPER%20LAKE-2025-26..pdf
- `Bhopal-2023-24_upper_lake.pdf`: https://www.mppcb.mp.gov.in/proc/mon/Bhopal-2023-24_upper_lake.pdf
- `comparatives-uppe-lak-lower-lake-2003-2023.pdf`: https://www.mppcb.mp.gov.in/proc/mon/comparatives-uppe-lak-lower-lake-2003-2023.pdf

**Extra data (map tab only, never used for ranking):**
- **Basemap tiles:** Esri World Light Gray Base (https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer), "Tiles © Esri". They load online with no API key. If they fail, the ghat circles still show on a plain background. (Keyless CARTO and OSM tiles were tried first. Opened from disk, they return "API key required" / "Access blocked" images.)
- **Circles:** every placed ghat gets a circle with the same fixed 350 m radius, coloured by tier. The circle marks the ghat's area and its reading status. It is not a measured spread of pollution.
- **Ghat positions are approximate.** They come from OpenStreetMap Nominatim search (https://nominatim.openstreetmap.org, © OpenStreetMap contributors, ODbL), queried 2026-10-11, and are stored in `ghatwatch/ghat_coords.json`. Each position marks a named place or landmark, not the exact MPPCB sampling point. Khatlapura, Hathaikheda and Malikhedi could not be found, so they are listed as "location unverified" and not placed on the map.

## Project structure

```
index.html              the offline dashboard (open this; repo root so the resources/ PDFs deploy with it)
resources/              the original MPPCB report PDFs (evidence links open these)
data/                   the provided CSVs
ghatwatch/
  score.py              scoring: CSV + CPCB limits -> ranking.json
  brief.py              builds the English brief (brief.json) from ranking.json
  brief_templates.json  sentence templates used by brief.py
  build.py              embeds ranking.json + brief.json + ghat_coords.json into ../index.html
  ghat_coords.json      approximate map positions (OpenStreetMap)
  ranking.json          generated tiers, alerts, evidence and coverage
  brief.json            generated brief
  fixture.json          small test fixture (python ghatwatch/build.py --fixture)
  schema.md             data contract between score.py, brief.py and index.html
  BUILD-LOG.md          build decisions, questions and assumptions
  VERIFY-REPORT.md      acceptance test results
  vendor/               Chart.js, Leaflet and the Inter font (all local, with licences)
```

## Built with

- Built with [Claude Code](https://claude.com/claude-code).
- [Chart.js](https://www.chartjs.org/) (MIT licence), vendored in `ghatwatch/vendor/` so the page works offline.
- Python 3 + pandas.

## Licence

MIT, see `LICENSE`.
