# DATA-UNDERSTANDING: Visarjan Ghat Watch (Track 2)

> Is document ka maksad: data ko samajhna, kuch build karna nahi.
> Koi original file modify nahi hui. Saari analysis scripts `scratch/` me hain (list sabse neeche hai).
> Har number ke saath likha hai ki wo kahan se aaya. "CSV" ka matlab hai `data/bhopal_ghats_2023_2025.csv`, jab tak kuch aur na likha ho.

---

## 1. Files ka map

### 1a. `data/` folder

| File | Rows | Kya hai | Kahan se verify kiya |
|---|---|---|---|
| `bhopal_ghats_2023_2025.csv` | 1,524 data rows + header | 7 Bhopal ghats × 3 saal × 2 festival × 3 phase × 12-13 parameters. **Main file.** | `wc -l` aur `scratch/profile1.py` |
| `sample_bhopal_2025.csv` | 453 | Upar wali file ki 2025 rows, **bilkul same** (pandas `equals` = True) | `scratch/profile1.py` |
| `mp_immersion_sites_2023_2025.csv` | 21,600 | Poore MP ke ~80-105 sites har festival me, wahi tests. Bhopal ki saari 1,524 rows isme bhi hain, values same | `scratch/profile1.py`, ek inline join |
| `cpcb_water_quality_criteria.csv` | 19 | CPCB class A-E ki limits (long format: class, parameter, limit_type, limit, unit) | direct padha |
| `DATA_DICTIONARY.md` | – | Columns, codes, ghats ka description. Problem statement wala hi content | direct padha |

**Bhopal CSV ke 14 columns:** `year, festival, site, water_body, phase, parameter, value, unit_assumed, flag, value_as_printed, parameter_as_printed, site_as_printed, site_match_confidence, source_page`

Column level par jo mila (`scratch/profile1.py`):
- `year`: 2023 = 525 rows, 2024 = 546, 2025 = 453
- `festival`: Ganesh 819, Durga 705
- `phase`: pre / during / after, har ek 508 (balanced, kyunki missing data bhi "not sampled" row ke roop me maujood hai)
- `parameter`: 12 parameters ke 120-120 rows. Suspended solids ke sirf 84, kyunki 2023 Durga aur 2025 Durga tables me ye parameter hai hi nahi
- `flag`: khali = 1,289 · `BDL` = 174 · `not sampled` = 57 · `*` = 2 · `**` = 2. **`ND` Bhopal file me ek bhi nahi hai** (statewide file me 2,040 hain)
- `value` khali hai to `flag` hamesha bhara hai, aur ulta bhi (crosstab me koi exception nahi)
- `value` aur `value_as_printed` har numeric row me exactly match karte hain (0 mismatch)
- Key (`year, festival, site, phase, parameter`) par **0 duplicates**
- `unit_assumed`: mg/l, NTU, µS/cm, aur pH ke liye khali. File UTF-8 hai. Windows console/Excel me µ ka symbol toota hua dikh sakta hai, data me koi gadbad nahi

**`mp_immersion_sites_2023_2025.csv` ke baare me** (`scratch/profile1.py` ke baad wala inline check):
- 28 alag `regional_office` labels, lekin spelling variants ki wajah se (jaise `R.O. Jabalpur` aur `R.O.Jabalpur`, `R.O. Ujjain` aur `R. O. Ujjain`) asli offices kam hain
- 401 alag `site_as_printed`. Ek festival me 80 se 105 tak (problem statement "about 100" kehta hai, data dictionary "about 200". Asal me ~100 per festival hain)
- 879 rows `needs_check = yes`
- Flags: not sampled 2,982 · BDL 2,267 · ND 2,040 · NA 36 · DRY 28 · `**` 52 · `*` 35 · `na` 1
- Key (year, festival, site_as_printed, phase, parameter) par **1,272 duplicate rows**. Ye wahi tables hain jo do pages me bat gayi aur do baar aa gayi (dictionary me bhi likha hai)

### 1b. `resources/` folder (PDFs)

Page count `pdftotext -layout` ke form-feed se gina gaya (`scratch/pdftext/*.txt`).

| PDF | Pages | Kya hai | CSV se link |
|---|---|---|---|
| `Idol_immer._Report_23_CPCB.pdf` | 87 | MPPCB idol immersion report 2023 | CSV me `year=2023` rows ka `source_page` isi PDF ka physical page hai |
| `Ganesh_and_Durga_visarjan_report-2024.pdf` | 118 | MPPCB report 2024 | `year=2024` → isi PDF ka page |
| `Ganesh_and_Durga_visarjan_report-2025.pdf` | 92 | MPPCB report 2025 (Action Taken Report, NGT OA 673/2018) | `year=2025` → isi PDF ka page |
| `Bhopal-2023-24_upper_lake.pdf` | 7 | Upper Lake ke 6 stations (Yacht Club, Karbala, Bairagarh intake, Kamla Park, Khanugaon, Sehore Naka), monthly 2023-24 | CSV se direct link nahi. **Baseline** ke kaam aa sakta hai |
| `comparatives-uppe-lak-lower-lake-2003-2023.pdf` | 112 | Upper Lake stations ka saal-dar-saal data, 2003-04 se 2022-23. Naam me "lower lake" hai, lekin text me "Lower Lake" ek baar bhi nahi milta (grep = 0) | Direct link nahi. Long-term baseline |
| `Upper_Lower_Lake_monthly_2025-26_from_xgn.pdf` | 12 | 7 stations monthly 2025-26. Isme **Lower Lake near Kalighat** (page 9) bhi hai | Direct link nahi. Baseline |

Root me `Track 2 - Visarjan Ghat Watch - Participant guide.pdf` bhi hai. Main maan raha hoon ki ye `PROBLEM-STATEMENT.md` ka PDF version hai. Isse alag se compare nahi kiya.

**`source_page` kis page par le jaata hai:** ye PDF ka *physical* page number hai (1 se shuru), report par chhapa page number nahi. 6 tables khol kar confirm kiya (section 4).

| Saal | Festival | Bhopal tables kis page par | Ghats |
|---|---|---|---|
| 2023 | Ganesh | 26, 27, 28 | 7 |
| 2023 | Durga | 59, 60, 61 | 7 |
| 2024 | Durga | 23, 24, 25, 26 | 7 (2024 report me Durga pehle aata hai) |
| 2024 | Ganesh | 69, 70, 71, 72 | 7 |
| 2025 | Ganesh | 28, 29, 30 | 7 |
| 2025 | Durga | 64, 65 | **5** (Bairagarh aur Malikhedi nahi) |

---

## 2. Bhopal CSV ki profiling

### 2a. Coverage table: ghat × saal × festival × phase

Har cell me **pre · during · after** hai, aur har phase ke liye `numeric / BDL / missing` (missing = not sampled + `*` + `**`).
Source: `scratch/coverage_md.py` (status logic `scratch/profile2.py` me hai).

| Ghat | 2023 Ganesh | 2023 Durga | 2024 Ganesh | 2024 Durga | 2025 Ganesh | 2025 Durga |
|---|---|---|---|---|---|---|
| Bairagarh | 10/3/0 · 12/1/0 · 11/2/0 | 10/2/0 · 11/1/0 · 10/2/0 | 13/0/0 · 13/0/0 · 13/0/0 | 9/4/0 · 9/4/0 · 9/4/0 | **0/0/13** · 13/0/0 · **0/0/13** | **koi table nahi** |
| Malikhedi | 10/3/0 · 12/1/0 · 11/2/0 | 9/3/0 · 11/1/0 · 10/2/0 | 13/0/0 · 13/0/0 · 13/0/0 | 9/4/0 · 9/4/0 · 9/4/0 | **0/0/13** · 13/0/0 · **0/0/13** | **koi table nahi** |
| Khatlapura | 10/3/0 · 9/0/**4** · 11/2/0 | 9/3/0 · 8/3/**1** · 9/3/0 | 13/0/0 · 13/0/0 · 13/0/0 | 9/4/0 · 9/4/0 · 9/4/0 | 13/0/0 · 13/0/0 · 13/0/0 | 12/0/0 · 11/1/0 · 12/0/0 |
| Rani Kamlapati / Kamla Park | 10/3/0 · 12/1/0 · 11/2/0 | 10/2/0 · 10/2/0 · 10/2/0 | 13/0/0 · 13/0/0 · 13/0/0 | 9/4/0 · 9/4/0 · 9/4/0 | 13/0/0 · 13/0/0 · 13/0/0 | 12/0/0 · 11/1/0 · 12/0/0 |
| Prempura | 10/3/0 · 12/1/0 · 11/2/0 | 8/3/**1** · 9/1/**2** · 9/2/**1** | 13/0/0 · 13/0/0 · 13/0/0 | 9/4/0 · 9/4/0 · 9/4/0 | 13/0/0 · 13/0/0 · 13/0/0 | 12/0/0 · 12/0/0 · 12/0/0 |
| Hathaikheda | 10/3/0 · 12/1/0 · 11/2/0 | 9/3/0 · 11/1/0 · 11/1/0 | 12/1/0 · 13/0/0 · 13/0/0 | 9/4/0 · 9/4/0 · 9/4/0 | 13/0/0 · 13/0/0 · 13/0/0 | 12/0/0 · 11/1/0 · 12/0/0 |
| Shahpura | 10/3/0 · 10/3/0 · 11/2/0 | 10/2/0 · 11/1/0 · 10/2/0 | 12/1/0 · 13/0/0 · 13/0/0 | 9/4/0 · 9/4/0 · 9/4/0 | 13/0/0 · 13/0/0 · 13/0/0 | 12/0/0 · 12/0/0 · 12/0/0 |

(2023 Durga aur 2025 Durga me 12 parameters hain, Suspended solids nahi hai. Baaki sab me 13.)

### 2b. Jahan data bilkul nahi hai, ya bahut kam hai

Source: `scratch/profile2.py` ("MISSING combos" aur "missing rows detail").

1. **Bairagarh, Durga 2025: koi row nahi** (pre, during, after teeno)
2. **Malikhedi, Durga 2025: koi row nahi** (teeno phase). 2025 PDF me "Hirdaram" sirf page 28 par milta hai aur "alikhedi" sirf page 29 par, dono Ganesh pages (grep, `scratch/pdftext`)
3. **Bairagarh aur Malikhedi, Ganesh 2025: sirf "during"** hai. Pre aur after ke 13-13 parameters missing hain. PDF me pH row par `*` (pre) aur `**` (after) chhapa hai, baaki cells khali hain. 2025 report ke page 62 par remark hai: `*` = *"Temporary/Artificial kunds were not fabricated during pre immersion sampling"*, `**` = *"...dismantled during post immersion sampling"*. **Iska matlab: 2025 me ye dono shayad temporary/artificial kund the.** (Remark page 62 par Ganesh section ke end me hai, Bhopal page par nahi. Isliye "shayad".)
4. Chhote gaps (sab `_` ke roop me chhape hain):
   - Khatlapura 2023 Ganesh during: Chromium, Lead, Zinc, Copper (page 26)
   - Khatlapura 2023 Durga during: BOD (page 59)
   - Prempura 2023 Durga: during pH, aur **BOD teeno phase** (page 60). Matlab Prempura ke paas 2023 Durga ka koi BOD nahi hai

Total missing rows: 61 = not sampled 57 + `*` 2 + `**` 2.

### 2c. Har parameter me kitna data hai

Source: `scratch/profile2.py` ("Per parameter status"). "Total" = CSV me us parameter ki rows.

| Parameter | Total | Numeric | BDL | Missing | CPCB class B limit? |
|---|---|---|---|---|---|
| pH | 120 | 115 | 0 | 5 | **Haan:** 6.5 se 8.5 |
| Dissolved oxygen | 120 | 116 | 0 | 4 | **Haan:** kam se kam 5 mg/l |
| BOD | 120 | 112 | 0 | 8 | **Haan:** zyada se zyada 3 mg/l (5 din, 20°C) |
| COD | 120 | 116 | 0 | 4 | Nahi |
| Total solids | 120 | 116 | 0 | 4 | Nahi |
| Dissolved solids | 120 | 116 | 0 | 4 | Nahi |
| Suspended solids | 84 | 80 | 0 | 4 | Nahi |
| Turbidity | 120 | 116 | 0 | 4 | Nahi |
| Conductivity | 120 | 116 | 0 | 4 | Class B me nahi. Class E me 2,250 max. Bhopal ki max reading 1,882 hai, to 0 readings 2,250 se upar |
| Chromium | 120 | 50 | **65** | 5 | Nahi |
| Lead | 120 | 63 | **52** | 5 | Nahi |
| Zinc | 120 | 94 | 21 | 5 | Nahi |
| Copper | 120 | 79 | 36 | 5 | Nahi |
| **Total** | 1,524 | 1,289 | 174 | 61 | |

**CPCB file se verify kiya** (`data/cpcb_water_quality_criteria.csv`, class B ki 4 rows): Total coliform ≤ 500 MPN/100ml, pH 6.5-8.5, Dissolved oxygen ≥ 5 mg/l, BOD ≤ 3 mg/l.
→ Hamare 13 me se **sirf 3 (pH, DO, BOD)** par class B limit hai. **Baaki 10 par koi class B limit nahi.**
→ Class B ki chauthi limit (**Total coliform**) Bhopal data me **test hi nahi hui**. Isliye hum ye nahi keh sakte ki koi ghat "class B pass karta hai". Zyada se zyada itna: "jo 3 test hue, unme pass/fail".
→ Saare BDL sirf metals me hain.

### 2d. Unusual values

Source: `scratch/profile2.py` aur `scratch/profile3.py`.

- **Negative values: 0**
- **value != value_as_printed: 0**
- **Exact zero: 4 rows, chaaron Bairagarh DO.** 2023 Ganesh after (p26), 2023 Durga pre (p60), 2023 Durga during (p60), 2025 Ganesh during (p28). Problem statement ka "four times across 2023 and 2025" isse **match karta hai**. Asli zero ho sakta hai, lekin ye bhi ho sakta hai ki lab ne "detect nahi hua" ko 0 likh diya. PDF me sirf `0` chhapa hai
- **Bairagarh DO 0 se 4.2:** 2023 Durga during 0 tha, ek hafte baad after 4.2 (p60). Possible hai, lekin jaldi recovery hai. Ye ek grab sample hai
- **DO 9 se upar (supersaturation):** 5 readings. Sabse ajeeb: **Hathaikheda 2024 Ganesh after: DO 11.0 aur BOD 22 ek saath** (p71). Itna BOD aam taur par oxygen kha jaata hai. Algae bloom me din ke time aisa ho sakta hai. PDF me yahi chhapa hai, isliye parse error nahi hai. Baaki 4: Hathaikheda 2023 Durga during 10.2, Malikhedi 2023 Durga after 10.4, Rani Kamlapati 2023 Ganesh after 9.5, Hathaikheda 2025 Durga after 10.8
- **Metals ka 2024 Ganesh spike:** chaaron metals ki top-5 readings **saari 2024 Ganesh** ki hain (Chromium 1.98, Copper 2.66, Zinc 1.96: Khatlapura during p69 · Lead 1.77 Bairagarh after p69 · Zinc 2.67 Hathaikheda after p71). 2024 Durga me chaaron metals har ghat par BDL hain (21/21 har metal). Itna bada saal-dar-saal farak lab ya method ke change jaisa lagta hai. Asli bhi ho sakta hai, data se pata nahi chalta
- **2025 metals me "0.03" aur "0.031" baar-baar:** Chromium = 0.03 in 29 rows (2025 Ganesh 17 + 2025 Durga 12). Lead = 0.031 in 17 rows (2025 Ganesh), har ghat aur har phase me same. Ye shayad **detection limit ko number ki tarah chhap diya gaya hai**, yaani asal me BDL. Inhe "measured 0.03" maanna galat ho sakta hai
- **Bairagarh ka conductivity / TDS bahut zyada:** 2023 Durga me EC 1,686 / 1,688 / 1,882 aur TDS 1,150 / 1,418 / 1,422 (p60). Upper Lake stations par EC ~250-480 hai (dekho 2025 Prempura, aur lake reports). `water_body` column me "Upper Lake" likha hai, lekin chemistry se ye **lake ka paani nahi, band kund** lagta hai
- **Consistency checks** (saare `scratch/profile3.py`):
  - BOD > COD: 0 cases (theek)
  - TDS > TS: 0 cases (theek)
  - TS = TDS + SS: 80 me se 79 me exact. 1 me gap 30 hai (Malikhedi 2024 Ganesh pre: 276 vs 190 + 56). PDF p71 par bhi yahi chhapa hai, to source ki galti hai, parser ki nahi
  - TDS/EC ratio: 0.51 se 0.92, median 0.66 (normal range). Sirf 1 outlier: Prempura 2024 Ganesh pre (0.92)
- **pH 6.5-8.5 ke bahar: 6 readings** (2c aur 3 dekho). Sabse zyada: Hathaikheda 2024 Durga pre, pH 9.20

### 2e. "Rani Kamlapati ghat / Kamla Park kund": ek jagah ya do?

Source: `scratch/profile1.py` (site_as_printed), `scratch/rani.py`, aur lake PDFs ka grep.

**Naam:**
- Ganesh tables (2023, 2024, 2025): *"Rani kamlapati, kamla park, murti visarjan **kund**, Bhopal"*
- Durga tables (2023, 2024, 2025): *"Rani kamlapati visarjan **ghat (lower lake)**"*
- CSV ka `water_body` sab 228 rows me "Lower Lake (as printed in Durga tables)" hai. Matlab **Ganesh rows ko bhi Durga ka label de diya gaya hai**

**Do jagah lagne ke points:**
1. "Kund" (alag banaya hua tank) aur "ghat (lower lake)" (lake ka kinara) alag cheezein hain
2. MPPCB ki apni lake reports me **"Kamla Park" Upper Lake ka station hai** (*"Upper Lake at Kamla Park near w/s intake well"*: `Bhopal-2023-24_upper_lake.pdf`, aur `Upper_Lower_Lake_monthly_2025-26` page 1). Durga table kehti hai "lower lake"
3. Ek hi pattern 3 saal tak repeat hota hai: Ganesh = kund, Durga = ghat. Ye typo jaisa nahi lagta

**Ek jagah lagne ke points:**
1. Chemistry dono festivals me milti-julti hai, aur Khatlapura (Lower Lake) jaisi hai. Average TDS: RK Ganesh 300-396, RK Durga 298-332, Khatlapura 298-533. EC: RK 437-535, Khatlapura 467-801
2. Kund me lake ka paani bhara ho to bhi chemistry same aayegi. Isliye ye point kamzor hai

**Nateeja:** data se ye tay nahi ho sakta. Lagta zyada hai ki ye **do alag sampling points** hain (Ganesh ke liye Kamla Park par ek kund, Durga ke liye Lower Lake par Rani Kamlapati ghat). Ranking me ise "ek ghat, 6 festivals" maan kar average karna risky hai. Safe tarika: Ganesh aur Durga ko alag dikhao, ya kam se kam warning label lagao.

---

## 3. Limit se comparison (sirf descriptive)

Rule: pH < 6.5 ya > 8.5 · DO < 5 · BOD > 3 (strict, jaisa CPCB file me min/max hai). Sirf numeric readings gini gayi. Missing aur BDL bahar hain (in 3 parameters me koi BDL hai bhi nahi).
Source: `scratch/limits.py`.

### 3a. Ghat-wise

| Ghat | pH bahar / total | DO < 5 / total | BOD > 3 / total |
|---|---|---|---|
| Bairagarh (Sant Hirdaram) kund | 0 / 13 | **11 / 13** | **13 / 13** |
| Malikhedi kund | 0 / 13 | **9 / 13** | 11 / 13 |
| Khatlapura ghat | 1 / 18 | 8 / 18 | 15 / 17 |
| Rani Kamlapati / Kamla Park | 0 / 18 | 6 / 18 | **18 / 18** |
| Shahpura lake ghat | 0 / 18 | 5 / 18 | **18 / 18** |
| Prempura ghat | 2 / 17 | 3 / 18 | 9 / 15 |
| Hathaikheda dam / kund | **3 / 18** | **0 / 18** | 16 / 18 |
| **Total** | **6 / 115** | **42 / 116** | **100 / 112** |

Dhyan do: Bairagarh aur Malikhedi ke paas sirf 13 readings hain, baaki ghats ke paas 18 (2025 ka gap). Ghats ko compare karte waqt count aur percentage dono dekhne padenge.

pH ki 6 readings: Hathaikheda 8.92 (2023 G during), 9.20 (2024 D pre), 8.71 (2025 G during) · Prempura 8.53 (2023 G during), 8.55 (2024 G during) · Khatlapura 6.49 (2024 G during).

### 3b. Phase-wise (immersion se pehle bhi kharab tha?)

| | pre | during | after |
|---|---|---|---|
| DO < 5 | 12 / 38 | 18 / 40 | 12 / 38 |
| BOD > 3 | **32 / 37** | 34 / 38 | 34 / 37 |

**Immersion se pehle bhi BOD 37 me se 32 baar limit se upar tha.** Lower Lake (Kalighat) ka 2025-26 ka saal bhar ka average BOD **5.54** hai (range 3.7-6.8) aur DO 5.20 (min 3.9) (`Upper_Lower_Lake_monthly_2025-26` page 9). Upper Lake Kamla Park station par BOD ~1.7 aur DO ~6.6 hai (page 1). Lekin ye lake reports BOD "3 days 27°C" se naapti hain, CPCB "5 days 20°C" se. Exact comparison nahi ho sakta.

### 3c. Problem statement ke numbers: reproduce hue?

| Claim | CSV se | Match? |
|---|---|---|
| "42 of 116 DO readings below 5" | DO numeric = 116 (120 − 4 missing), DO < 5 = **42** | ✅ Exact |
| "100 of 112 BOD readings above 3" | BOD numeric = 112 (120 − 8 missing), BOD > 3 = **100** | ✅ Exact |
| "Bairagarh DO 0 four times across 2023 and 2025" | 4 zeros, sab Bairagarh, 2023 me 3 aur 2025 me 1 | ✅ Exact |

**Boundary sensitivity:** 3 readings exactly DO = 5.0 hain, aur 1 reading exactly BOD = 3.0 (Prempura 2025 G after). Agar koi "≤ 5" ya "≥ 3" use kare to counts **45/116** aur **101/112** ho jaate hain. Strict rule hi CPCB ke wording se match karta hai. Isse tool me fix karke likhna hoga.

Extra context: 17 / 116 DO readings 4 se bhi kam hain (class C/D ki limit). 59 / 112 BOD readings limit ke double (6) se zyada hain.

---

## 4. PDF se spot-check

Har row ka `source_page` `pdftotext -layout` se khola (`scratch/page.py <report> <page>`). Main 5 rows + 1 bonus.

| # | CSV row | CSV value | PDF me kya dikha | Match? |
|---|---|---|---|---|
| 1 | 2023 · Durga · Bairagarh · **pre** · Dissolved oxygen (p60, 2023 report) | `0` | "Sant Hirdaram visarjan kund, Bairagarh (upper lake)" table, row "4 D.Oxygen  **0**  0" | ✅ |
| 2 | 2024 · Durga · Khatlapura · pre · Chromium (p24, 2024 report) | khali, flag `BDL` | "Khatlapura Visarjan Ghat (Lower lake)", row "10 Chromium **BDL** BDL BDL" | ✅ |
| 3 | 2025 · Ganesh · Malikhedi · **pre** · Dissolved oxygen (p29, 2025 report) | khali, flag `not sampled` | "Maalikhedi visarjan kund", D.Oxygen row me sirf during = 0.6, pre aur after khali. pH row: `*  7.53  **` | ✅ |
| 4 | 2024 · Ganesh · Hathaikheda · after · BOD (p71, 2024 report) | `22` | "Hathaikheda Visarjan Kund", row "6 BOD 7.2 13.2 **22**". DO row "9 5.3 11" bhi match | ✅ |
| 5 | 2025 · Durga · Rani Kamlapati · after · Dissolved oxygen (p64, 2025 report) | `2.6` | "Rani kamlapati visarjan ghat (lower lake)". "After one week" column text me alag block me aata hai (7.38, 346, 308, **2.6**, 4.8 ...). Chautha value 2.6 hai | ✅ (layout tricky hai, value sahi) |
| bonus | 2023 · Durga · Prempura · during · pH (p60) | khali, flag `not sampled`, printed `_` | "1 pH  7.66  **_**" | ✅ |

**Automated check bhi kiya** (`scratch/autocheck.py`): jin 1,476 rows me kuch chhapa hai, unka `value_as_printed` uske `source_page` ke text me milta hai: **1,476 / 1,476**. Har site ka naam bhi apne page par mila. Ye kamzor check hai: sirf itna batata hai ki number page par *kahin* hai, ye nahi ki sahi row/column me hai. Gross parse errors pakadne ke liye kaafi hai.

**Layout trap:** 2023 p60, 2024 p71 aur 2025 p64 jaise pages par "After one week" column table se alag hokar text me upar-neeche chala jaata hai. Jo samples dekhe wo sahi the. Phir bhi koi dubara parse kare to yahan galti ka risk sabse zyada hai.

---

## 5. Data ke traps jo ranking galat kar sakte hain

1. **Blank ≠ clean.** 61 missing rows hain, aur 2 ghats ka poora Durga 2025 gayab hai. Wahi 2 ghats (Bairagarh, Malikhedi) DO me sabse kharab hain. "Latest year" ko zyada weight diya aur missing ko skip kiya, to **sabse kharab ghats acche dikhenge**
2. **Unequal sample size.** 13 vs 18 readings. Raw count ("kitni baar fail") se 18 readings wale ghat zyada kharab dikhenge. Pure percentage me 13 readings ka noise bada lagega
3. **BDL ≠ 0 ≠ missing.** 174 BDL hain, sab metals me. Detection limit kya hai, report nahi batati. Aur 2025 ke "0.03 / 0.031" shayad BDL hi hain jo number ki tarah chhape gaye
4. **BOD sab jagah fail hai (100/112).** Ranking me iska weight zyada rakha to sab ghats ek jaise dikhenge, discrimination nahi hoga
5. **Pre-immersion bhi fail.** BOD pre me 32/37 fail hai, aur Lower Lake ka annual BOD 5.54 hai. **Kharab paani ka kaaran sirf visarjan nahi maana ja sakta.** Sewage ya baseline bhi ho sakta hai
6. **Ek reading = ek grab sample.** Replicates nahi hain, time ya temperature nahi hai. Ek ajeeb reading (DO 11 + BOD 22, ya DO 0) poori ranking palat sakti hai
7. **Saal ka effect (lab/method?).** 2024 Ganesh me metals 10-100× zyada aur 2024 Durga me sab BDL. Saalon ko mix karke average kiya to 2024 Ganesh hi dominate karega
8. **Season.** Ganesh (Aug-Sep, monsoon ke paas) aur Durga (Oct) ka paani alag hota hai. Officer Durga plan kar raha hai, to Durga readings zyada relevant hain. Lekin Durga 2025 hi missing hai 2 ghats ke liye
9. **Rani Kamlapati / Kamla Park shayad 2 jagah hai** (2e). Merge kiya to dono ka signal mix ho jaayega
10. **Bairagarh "Upper Lake" label galat context deta hai.** Chemistry band kund ki hai (EC 1,700+). Upper Lake ke data ko Bairagarh ka baseline maanna galat hoga
11. **Units assumed hain, BOD method unknown.** CPCB class B "BOD 5 days 20°C" kehta hai. Lake reports "3 days 27°C" use karti hain. Immersion reports kuch nahi batati
12. **Boundary.** DO = 5.0 (3 readings) aur BOD = 3.0 (1 reading). `<` aur `<=` se counts badal jaate hain
13. **Suspended solids** 2023 Durga aur 2025 Durga me test hi nahi hua. "Average SS" saalon ke beech fair nahi hoga
14. **Statewide file use ki to:** 1,272 duplicate keys aur 879 unreadable site names hain. Bina dedupe ke counts double ho jaayenge
15. **Temporary kund.** 2025 me Bairagarh/Malikhedi shayad temporary kund the (remark p62). Saal-dar-saal ye "wahi jagah" hai ya nahi, pakka nahi

---

## 6. Data kya NAHI batata (ye claim mat karna)

- **Health effect:** koi bimari, skin problem ya hospital data nahi hai. "Paani se log beemar hote hain" claim nahi kar sakte. Sirf "reading limit se bahar hai" bol sakte hain
- **Fish deaths:** DO 0 par machhli nahi jee sakti. Ye general fact hai, lekin **is data me fish deaths ka record nahi hai**
- **Coliform / bacteria:** class B ki ek limit test hi nahi hui. "Bathing ke liye safe" kabhi nahi bol sakte
- **Metals safe hain ya unsafe:** class B me metals ki koi limit nahi hai. Drinking-water standards alag hain aur use apply karna hamara assumption hoga
- **Pollution ka kaaran:** visarjan, sewage, ya algae? Pre-immersion bhi kharab hai, to "visarjan ne kharab kiya" sabit nahi hota. Zyada se zyada "during/after me badla" bol sakte hain
- **2026 ki halat:** latest data 2025 ka hai. 20 Oct 2026 ka paani kaisa hoga, data nahi batata. "Pichhle 3 saal ka pattern" bolna safe hai, prediction nahi
- **Naye BMC ghats:** NGT ban ke baad jo naye ghats ban rahe hain, unka koi data nahi hai
- **Trend:** har ghat ke liye max 3 Durga points hain. "Saal-dar-saal behtar/kharab ho raha hai" statistically claim nahi kar sakte
- **Exact location / GPS:** CSV me coordinates nahi hain. Rani Kamlapati ek jagah hai ya do, ye bhi tay nahi
- **Idols ki sankhya, bheed, sampling ka exact date/time:** ye kuch nahi hai
- **Bairagarh/Malikhedi Durga 2025:** sample hua tha ya nahi, ya report me chhuta, pata nahi. Bas report me table nahi hai

---

## 7. Scoring approaches ke 3 options (recommendation baad me)

Teeno me common rule: missing ko "clean" nahi maanna. Har ghat ke saath "kitni readings pe based hai" dikhana.

### Option A: Exceedance rate (kitni baar limit fail)
Har ghat ke liye: (pH, DO, BOD me limit se bahar readings) / (kul numeric readings). Chahein to Durga ko ya recent saal ko zyada weight.
- **Pros:** sabse simple aur sabse traceable ("Bairagarh: 13 me se 11 DO readings 5 se kam, page 26/60/25/69/28"). Officer turant samajh jaata hai. CPCB limit se seedha juda hai
- **Cons:** magnitude ignore karta hai (DO 4.9 aur DO 0 ek barabar). BOD sab jagah fail hai, to farak sirf DO aur pH se aata hai. 13 vs 18 readings se percentage ka noise. Metals, COD aur turbidity ka koi role nahi (limit nahi hai)

### Option B: Severity (limit se kitna door)
Har reading ke liye "limit se kitna bura": DO ke liye (5 − DO)/5, BOD ke liye BOD/3, pH ke liye range se doori. Ghat ka score = median, ya worst-case (max), ya dono. DO = 0 ko "critical" flag.
- **Pros:** Bairagarh ke DO 0 jaise dangerous cases sahi se upar aate hain. BOD 22 aur BOD 3.5 me farak dikhta hai
- **Cons:** parameters ko jodne ka formula hamara apna choice hai, CPCB ka nahi (judges pooch sakte hain "ye weight kyun?"). Ek galat reading (DO 11 + BOD 22) worst-case ko hila deti hai. Officer ko samjhana Option A se mushkil

### Option C: Immersion impact (pre → during/after ka badlav) + baseline
Do hisse: (1) baseline = pre reading limit se kitna bahar, (2) impact = during/after me pre ke mukable kitna bigda (DO kitna gira, BOD kitna badha). Is tarah alag dikhega ki kaun ghat "pehle se kharab" hai aur kaun "visarjan ke baad bigadta hai".
- **Pros:** officer ke decision se seedha juda hai (aeration/cleaning *visarjan ke baad* kahan bhejein). Ye bhi honestly dikhata hai ki kuch problem baseline ki hai, visarjan ki nahi. Idea ke liye zyada original
- **Cons:** poora pre/during/after triplet chahiye. Bairagarh aur Malikhedi 2025 me sirf "during" hai aur Prempura 2023 Durga me BOD hi nahi, to sabse kharab ghats ka impact compute hi nahi hoga. Ek grab sample ka difference noisy hai. "Visarjan ki wajah se" causal claim jaisa sunai de sakta hai, jo data support nahi karta

(Teeno ke saath alag se ek "data confidence" label chal sakta hai, jaise readings ki sankhya, missing festivals, aur medium site-match. Ise score me mix na karke alag dikhana behtar rahega. Ye decision baad me.)

---

## Scripts (`scratch/`)

| File | Kya karta hai |
|---|---|
| `scratch/pdftext/*.txt` | 6 resource PDFs ka `pdftotext -layout` output (page = form-feed) |
| `scratch/page.py <report> <page>` | Kisi report ka ek page print karta hai |
| `scratch/profile1.py` | Columns, flags, units, site names, source pages, sample = 2025 check, duplicates |
| `scratch/profile2.py` | Coverage pivot, missing combos, per-parameter status, describe, zeros, negatives. `scratch/df.pkl` banata hai |
| `scratch/profile3.py` | Consistency checks (BOD vs COD, TS vs TDS+SS, TDS/EC), outliers, repeated values |
| `scratch/coverage_md.py` | Section 2a ki markdown table |
| `scratch/limits.py` | pH/DO/BOD vs class B, ghat-wise, phase-wise, boundary sensitivity |
| `scratch/rani.py` | Rani Kamlapati vs Khatlapura vs Prempura ke averages |
| `scratch/autocheck.py` | Har printed value apne source_page par hai ya nahi |

Dubara chalane ke liye project root se: `python scratch/profile2.py` pehle (ye `df.pkl` banata hai), phir baaki.
