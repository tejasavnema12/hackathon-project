"""GhatWatch scoring: reads the Bhopal ghat CSV and CPCB criteria, writes ranking.json.

Deterministic, no network, no API calls. Follows ghatwatch/schema.md.
Run: python ghatwatch/score.py
"""
import json
import math
import re
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
CSV = DATA / "bhopal_ghats_2023_2025.csv"
CPCB = DATA / "cpcb_water_quality_criteria.csv"
OUT = HERE / "ranking.json"

DURGA_DATE = date(2026, 10, 20)
YEARS = [2023, 2024, 2025]
FESTIVALS = ["Ganesh", "Durga"]
PHASES = ["pre", "during", "after"]
PARAMS = ["DO", "BOD", "pH"]
PARAM_MAP = {"pH": "pH", "Dissolved oxygen": "DO", "BOD": "BOD"}
MISSING_FLAGS = {"not sampled", "*", "**", "_"}

REPORTS = {
    2023: "Idol_immer._Report_23_CPCB.pdf",
    2024: "Ganesh_and_Durga_visarjan_report-2024.pdf",
    2025: "Ganesh_and_Durga_visarjan_report-2025.pdf",
}

GHATS = [
    {"id": "bairagarh", "name": "Bairagarh (Sant Hirdaram) kund", "site_group": "Bairagarh (Sant Hirdaram) kund",
     "water_body": "Upper Lake (enclosed kund)", "site_match": "high"},
    {"id": "malikhedi", "name": "Malikhedi kund", "site_group": "Malikhedi kund",
     "water_body": "Kund", "site_match": "high"},
    {"id": "khatlapura", "name": "Khatlapura ghat", "site_group": "Khatlapura ghat",
     "water_body": "Lower Lake", "site_match": "high"},
    {"id": "kamla_park_kund", "name": "Kamla Park kund (Ganesh tables)",
     "site_group": "Rani Kamlapati ghat / Kamla Park kund", "water_body": "as printed: Kamla Park", "site_match": "medium"},
    {"id": "rani_kamlapati_ghat", "name": "Rani Kamlapati ghat, Lower Lake (Durga tables)",
     "site_group": "Rani Kamlapati ghat / Kamla Park kund", "water_body": "Lower Lake", "site_match": "medium"},
    {"id": "prempura", "name": "Prempura ghat", "site_group": "Prempura ghat",
     "water_body": "Upper Lake", "site_match": "high"},
    {"id": "hathaikheda", "name": "Hathaikheda dam / kund", "site_group": "Hathaikheda dam / kund",
     "water_body": "Hathaikheda dam", "site_match": "high"},
    {"id": "shahpura", "name": "Shahpura lake ghat", "site_group": "Shahpura lake ghat",
     "water_body": "Shahpura Lake", "site_match": "high"},
]
GHAT_BY_ID = {g["id"]: g for g in GHATS}
SITE_TO_ID = {
    "Bairagarh (Sant Hirdaram) kund": "bairagarh",
    "Malikhedi kund": "malikhedi",
    "Khatlapura ghat": "khatlapura",
    "Prempura ghat": "prempura",
    "Hathaikheda dam / kund": "hathaikheda",
    "Shahpura lake ghat": "shahpura",
}
RK_SITE = "Rani Kamlapati ghat / Kamla Park kund"


def ghat_festivals(gid):
    if gid == "kamla_park_kund":
        return ["Ganesh"]
    if gid == "rani_kamlapati_ghat":
        return ["Durga"]
    return FESTIVALS


def ghats_in_scope(scope):
    out = []
    for g in GHATS:
        fests = ghat_festivals(g["id"])
        if scope == "all" or scope.capitalize() in fests:
            out.append(g["id"])
    return out


def map_ghat(site, festival):
    if site == RK_SITE:
        return "kamla_park_kund" if festival == "Ganesh" else "rani_kamlapati_ghat"
    return SITE_TO_ID[site]


def num(x):
    """Clean number for JSON (int when whole)."""
    if x is None:
        return None
    x = float(x)
    return int(x) if x.is_integer() else round(x, 4)


def fmt(x):
    x = float(x)
    return str(int(x)) if x.is_integer() else f"{x:g}"


# ---------------------------------------------------------------- limits
def read_limits():
    c = pd.read_csv(CPCB)
    b = c[c["class"].astype(str).str.strip() == "B"]
    lim = {}
    for _, r in b.iterrows():
        p = str(r["parameter"])
        unit = "" if pd.isna(r["unit"]) else str(r["unit"])
        if p == "pH":
            lo, hi = [float(v) for v in str(r["limit"]).split("-")]
            lim["pH"] = {"type": "range", "min": num(lo), "max": num(hi), "unit": unit}
        elif p == "Dissolved oxygen":
            lim["DO"] = {"type": str(r["limit_type"]), "value": num(r["limit"]), "unit": unit}
        elif p.startswith("BOD"):
            lim["BOD"] = {"type": str(r["limit_type"]), "value": num(r["limit"]), "unit": unit}
    assert set(lim) == {"DO", "BOD", "pH"}, lim
    assert lim["DO"]["type"] == "min" and lim["BOD"]["type"] == "max"
    return lim


LIM = read_limits()
DO_MIN = LIM["DO"]["value"]
BOD_MAX = LIM["BOD"]["value"]
PH_LO, PH_HI = LIM["pH"]["min"], LIM["pH"]["max"]
LIMIT_TEXT = {"DO": f"≥ {fmt(DO_MIN)}", "BOD": f"≤ {fmt(BOD_MAX)}", "pH": f"{fmt(PH_LO)}–{fmt(PH_HI)}"}
PH_RANGE = f"{fmt(PH_LO)}–{fmt(PH_HI)}"


def is_fail(param, v):
    if param == "DO":
        return v < DO_MIN
    if param == "BOD":
        return v > BOD_MAX
    return v < PH_LO or v > PH_HI


# ---------------------------------------------------------------- load
df = pd.read_csv(CSV)
df["ghat"] = [map_ghat(s, f) for s, f in zip(df["site"], df["festival"])]


def ev_id(year, festival, ghat, phase, param):
    return f"E-{year}-{festival[0]}-{ghat}-{phase}-{param}"


evidence = []
for _, r in df[df["parameter"].isin(PARAM_MAP)].iterrows():
    p = PARAM_MAP[r["parameter"]]
    flag = "" if pd.isna(r["flag"]) else str(r["flag"]).strip()
    printed = "" if pd.isna(r["value_as_printed"]) else str(r["value_as_printed"])
    if pd.isna(r["value"]) or flag in MISSING_FLAGS:
        value, status = None, "missing"
    else:
        value = float(r["value"])
        status = "fail" if is_fail(p, value) else "within_limit"
    yr = int(r["year"])
    page = int(r["source_page"])
    evidence.append({
        "id": ev_id(yr, r["festival"], r["ghat"], r["phase"], p),
        "ghat": r["ghat"], "year": yr, "festival": r["festival"], "phase": r["phase"], "parameter": p,
        "value": num(value), "value_as_printed": printed, "limit": LIMIT_TEXT[p], "status": status,
        "source_report": REPORTS[yr], "source_page": page,
        "source_url": f"resources/{REPORTS[yr]}#page={page}",
    })

# synthetic no_table rows for any (ghat, year, festival, phase, param) with no CSV row
existing = {e["id"] for e in evidence}
for g in GHATS:
    for yr in YEARS:
        for fest in ghat_festivals(g["id"]):
            for ph in PHASES:
                for p in PARAMS:
                    eid = ev_id(yr, fest, g["id"], ph, p)
                    if eid not in existing:
                        evidence.append({
                            "id": eid, "ghat": g["id"], "year": yr, "festival": fest, "phase": ph, "parameter": p,
                            "value": None, "value_as_printed": "", "limit": LIMIT_TEXT[p], "status": "no_table",
                            "source_report": None, "source_page": None,
                            "source_url": f"resources/{REPORTS[2025] if yr == 2025 else REPORTS[yr]}",
                        })
EV = {e["id"]: e for e in evidence}
assert len(EV) == len(evidence), "duplicate evidence ids"


def numeric(e):
    return e["status"] in ("fail", "within_limit")


def ev_in_scope(scope, ghat=None):
    out = []
    for e in evidence:
        if ghat is not None and e["ghat"] != ghat:
            continue
        if scope != "all" and e["festival"].lower() != scope:
            continue
        out.append(e)
    return out


def durga_2025_missing(gid):
    if "Durga" not in ghat_festivals(gid):
        return False
    rows = [e for e in evidence if e["ghat"] == gid and e["year"] == 2025 and e["festival"] == "Durga"]
    return all(e["status"] == "no_table" for e in rows)


# ---------------------------------------------------------------- coverage
coverage = []
for g in GHATS:
    for yr in YEARS:
        for fest in ghat_festivals(g["id"]):
            for ph in PHASES:
                sub = df[(df["ghat"] == g["id"]) & (df["year"] == yr) & (df["festival"] == fest) & (df["phase"] == ph)]
                flags = sub["flag"].fillna("").astype(str).str.strip()
                n_bdl = int((flags == "BDL").sum())
                n_num = int((sub["value"].notna() & (flags == "")).sum())
                n_mis = int(len(sub) - n_bdl - n_num)
                if len(sub) == 0:
                    status = "no_table"
                elif n_num == 0 and n_bdl == 0:
                    status = "missing"
                elif n_num == 0:
                    status = "bdl"
                else:
                    status = "numeric"
                rpn = sum(1 for p in PARAMS if numeric(EV[ev_id(yr, fest, g["id"], ph, p)]))
                coverage.append({"ghat": g["id"], "year": yr, "festival": fest, "phase": ph, "status": status,
                                 "n_numeric": n_num, "n_bdl": n_bdl, "n_missing": n_mis,
                                 "ranking_params_numeric": rpn})


# ---------------------------------------------------------------- ranking
def plural(n, one, many):
    return one if n == 1 else many


def missing_festivals(gid, scope):
    """Festival tables or whole phases with no pH/DO/BOD number."""
    out = []
    if durga_2025_missing(gid):
        out.append("Durga 2025")  # applies in every scope: the upcoming festival is Durga
    for yr in YEARS:
        for fest in ghat_festivals(gid):
            if scope != "all" and fest.lower() != scope:
                continue
            rows = [EV[ev_id(yr, fest, gid, ph, p)] for ph in PHASES for p in PARAMS]
            if all(e["status"] == "no_table" for e in rows):
                if f"{fest} {yr}" not in out:
                    out.append(f"{fest} {yr}")
                continue
            gaps = [ph for ph in PHASES
                    if not any(numeric(EV[ev_id(yr, fest, gid, ph, p)]) for p in PARAMS)]
            if gaps:
                out.append(f"{fest} {yr} {'/'.join(gaps)} (not sampled)")
    return out


def param_gap_notes(gid, scope):
    notes = []
    for yr in YEARS:
        for fest in ghat_festivals(gid):
            if scope != "all" and fest.lower() != scope:
                continue
            for p in PARAMS:
                rows = [EV[ev_id(yr, fest, gid, ph, p)] for ph in PHASES]
                miss = [e["phase"] for e in rows if e["status"] == "missing"]
                # skip phases already reported as whole-phase gaps
                whole = [ph for ph in PHASES
                         if not any(numeric(EV[ev_id(yr, fest, gid, ph, q)]) for q in PARAMS)]
                miss = [m for m in miss if m not in whole]
                if miss:
                    notes.append(f"{p} not sampled in {fest} {yr} ({'/'.join(miss)})")
    return notes


def confidence(gid, scope, n):
    g = GHAT_BY_ID[gid]
    mf = missing_festivals(gid, scope)
    notes = []
    if gid == "bairagarh":
        maxec = df[(df["ghat"] == gid) & (df["parameter"] == "Conductivity")]["value"].max()
        notes.append(f"Enclosed kund: conductivity up to {fmt(maxec)}, unlike lake water")
    if g["site_match"] == "medium":
        notes.append("Ganesh and Durga tables may describe two different places (Kamla Park kund vs Rani Kamlapati ghat on the Lower Lake); shown separately")
    if gid in ("bairagarh", "malikhedi"):
        notes.append("2025 report remarks suggest temporary kunds in 2025 (not built before immersion, removed after)")
    notes += param_gap_notes(gid, scope)
    table_missing = any(not m.endswith("(not sampled)") for m in mf)
    phase_missing = any(m.endswith("(not sampled)") for m in mf) or bool(param_gap_notes(gid, scope))
    if table_missing or n < 15:
        level = "low"
    elif g["site_match"] == "medium" or phase_missing:
        level = "medium"
    else:
        level = "high"
    return {"n_readings": n, "missing_festivals": mf, "site_match": g["site_match"], "notes": notes, "level": level}


ACTIONS = {
    "1m": "Test before, during and after Durga visarjan (no 2025 Durga data). Keep aeration and cleaning on standby.",
    1: "Priority: arrange aeration and extra cleaning, and test water before, during and after visarjan.",
    2: "Watch: test during and after visarjan, and plan cleaning after immersion.",
    3: "Routine: standard monitoring. Readings are still outside limits at times.",
}


def reason(ppf, worst, zeros, missing):
    d, b, p = ppf["DO"], ppf["BOD"], ppf["pH"]
    if d["n"]:
        s1 = f"{d['fails']} of {d['n']} DO readings {plural(d['fails'], 'was', 'were')} below {fmt(DO_MIN)} mg/l"
        if zeros:
            s1 += f", including {zeros} {plural(zeros, 'reading', 'readings')} of zero"
        elif worst is not None:
            s1 += f" (lowest {fmt(worst)})"
        s1 += "."
    else:
        s1 = "No DO readings in this scope."
    parts = []
    if b["n"]:
        parts.append(f"BOD was above {fmt(BOD_MAX)} mg/l in {b['fails']} of {b['n']} readings")
    if p["n"]:
        parts.append(f"pH was outside {PH_RANGE} in {p['fails']} of {p['n']}")
    s2 = ("; ".join(parts) + ".") if parts else ""
    if missing:
        s2 += (" " if s2 else "") + "No Durga 2025 table in the report."
    return (s1 + " " + s2).strip()


def build_ranking(scope):
    rows = []
    for gid in ghats_in_scope(scope):
        evs = ev_in_scope(scope, gid)
        ppf = {}
        for p in PARAMS:
            pe = [e for e in evs if e["parameter"] == p and numeric(e)]
            ppf[p] = {"fails": sum(e["status"] == "fail" for e in pe), "n": len(pe)}
        fails = sum(v["fails"] for v in ppf.values())
        n = sum(v["n"] for v in ppf.values())
        rate = fails / n if n else 0.0
        dos = [e for e in evs if e["parameter"] == "DO" and numeric(e)]
        worst = min(dos, key=lambda e: e["value"]) if dos else None
        zeros = sum(1 for e in dos if e["value"] == 0)
        miss = durga_2025_missing(gid)
        if rate >= 0.5 or miss:
            tier = 1
        elif rate >= 0.4:
            tier = 2
        else:
            tier = 3
        g = GHAT_BY_ID[gid]
        rows.append({
            "ghat": gid, "name": g["name"], "site_group": g["site_group"], "rank": 0, "tier": tier,
            "near_tie": False, "fail_rate": round(rate, 3), "_rate": rate, "fails": fails, "n": n,
            "per_param_fails": ppf,
            "worst_DO": {"value": worst["value"], "evidence_id": worst["id"]} if worst else None,
            "durga_2025_missing": miss,
            "reason_en": reason(ppf, worst["value"] if worst else None, zeros, miss),
            "action": ACTIONS["1m"] if (tier == 1 and miss) else ACTIONS[tier],
            "confidence": confidence(gid, scope, n),
            "evidence_ids": [e["id"] for e in evs],
        })
    rows.sort(key=lambda r: (r["tier"], -r["_rate"],
                             r["worst_DO"]["value"] if r["worst_DO"] else math.inf))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        if i > 0 and rows[i - 1]["tier"] == r["tier"] and abs(rows[i - 1]["_rate"] - r["_rate"]) < 0.02:
            r["near_tie"] = True
            rows[i - 1]["near_tie"] = True
    for r in rows:
        del r["_rate"]
    return rows


ranking = {s: build_ranking(s) for s in ("all", "durga", "ganesh")}

# ---------------------------------------------------------------- KPIs
today = date.today()
days = (DURGA_DATE - today).days
num_ev = [e for e in evidence if numeric(e)]


def kpi_param(p, pred=None):
    pe = [e for e in num_ev if e["parameter"] == p]
    hit = [e for e in pe if (pred(e) if pred else e["status"] == "fail")]
    return len(hit), len(pe), [e["id"] for e in hit]


do_f, do_n, do_ids = kpi_param("DO")
bod_f, bod_n, bod_ids = kpi_param("BOD")
ph_f, ph_n, ph_ids = kpi_param("pH")
z_f, z_n, z_ids = kpi_param("DO", lambda e: e["value"] == 0)
csv_sites = sorted(df["site"].unique())
missing_ghats = [g["id"] for g in GHATS if durga_2025_missing(g["id"])]
missing_ids = [e["id"] for e in evidence if e["status"] == "no_table"]
kpis = [
    {"id": "days_to_durga", "label": "Days to Durga visarjan (20 October 2026)", "value": days, "n": None,
     "scope": "all", "evidence_ids": []},
    {"id": "do_below_5", "label": f"DO readings below {fmt(DO_MIN)} mg/l", "value": do_f, "n": do_n,
     "scope": "all", "evidence_ids": do_ids},
    {"id": "bod_above_3", "label": f"BOD readings above {fmt(BOD_MAX)} mg/l", "value": bod_f, "n": bod_n,
     "scope": "all", "evidence_ids": bod_ids},
    {"id": "ph_out_of_range", "label": f"pH readings outside {PH_RANGE}", "value": ph_f, "n": ph_n,
     "scope": "all", "evidence_ids": ph_ids},
    {"id": "do_zero", "label": "DO readings of zero", "value": z_f, "n": z_n, "scope": "all", "evidence_ids": z_ids},
    {"id": "ghats_no_durga_2025", "label": "Ghats with no Durga 2025 table", "value": len(missing_ghats),
     "n": len(csv_sites), "scope": "all", "evidence_ids": missing_ids},
]

# ---------------------------------------------------------------- alerts
alerts = []


def add_alert(sev, rule, gid, params, text, ids, scope="all"):
    alerts.append({"id": f"A{len(alerts) + 1:02d}", "severity": sev, "rule_id": rule, "ghat": gid,
                   "text_params": params, "text_en": text, "evidence_ids": ids, "scope": scope})


def label(e):
    return f"{e['festival']} {e['year']} {e['phase']}"


for g in GHATS:
    gid, name = g["id"], g["name"]
    evs = ev_in_scope("all", gid)
    dos = [e for e in evs if e["parameter"] == "DO" and numeric(e)]
    bods = [e for e in evs if e["parameter"] == "BOD" and numeric(e)]
    phs = [e for e in evs if e["parameter"] == "pH" and numeric(e)]

    zeros = [e for e in dos if e["value"] == 0]
    if zeros:
        add_alert("critical", "DO_ZERO", gid,
                  {"count": len(zeros), "years": sorted({e["year"] for e in zeros}),
                   "samples": [label(e) for e in zeros]},
                  f"{name}: zero dissolved oxygen recorded {len(zeros)} {plural(len(zeros), 'time', 'times')} "
                  f"({', '.join(label(e) for e in zeros)}).",
                  [e["id"] for e in zeros])

    if durga_2025_missing(gid):
        ids = [e["id"] for e in evs if e["year"] == 2025 and e["festival"] == "Durga"]
        add_alert("data", "DURGA_MISSING", gid, {"year": 2025, "festival": "Durga"},
                  f"{name}: no Durga 2025 table in the report. Missing data is not counted as within the limit; "
                  f"test before, during and after visarjan.",
                  ids, scope="durga")

    dfail = [e for e in dos if e["status"] == "fail"]
    if dos and len(dfail) / len(dos) > 0.5:
        add_alert("critical", "DO_FAIL_MAJORITY", gid, {"fails": len(dfail), "n": len(dos), "limit": DO_MIN},
                  f"{name}: DO was below {fmt(DO_MIN)} mg/l in {len(dfail)} of {len(dos)} readings.",
                  [e["id"] for e in dfail])

    bfail = [e for e in bods if e["status"] == "fail"]
    if bods and len(bfail) == len(bods):
        add_alert("warning", "BOD_ALL_FAIL", gid, {"fails": len(bfail), "n": len(bods), "limit": BOD_MAX},
                  f"{name}: BOD was above {fmt(BOD_MAX)} mg/l in all {len(bods)} readings.",
                  [e["id"] for e in bfail])

    pfail = [e for e in phs if e["status"] == "fail"]
    if pfail:
        add_alert("warning", "PH_OUT", gid,
                  {"values": [e["value"] for e in pfail], "samples": [label(e) for e in pfail]},
                  f"{name}: pH outside the {PH_RANGE} range {len(pfail)} {plural(len(pfail), 'time', 'times')} ("
                  + ", ".join(f"{fmt(e['value'])} in {label(e)}" for e in pfail) + ").",
                  [e["id"] for e in pfail])

    for yr in YEARS:
        for fest in ghat_festivals(gid):
            for ph in PHASES:
                d = EV[ev_id(yr, fest, gid, ph, "DO")]
                b = EV[ev_id(yr, fest, gid, ph, "BOD")]
                if numeric(d) and numeric(b) and d["value"] > 9 and b["value"] > 15:
                    add_alert("data", "SUSPECT_DO_BOD", gid,
                              {"DO": d["value"], "BOD": b["value"], "sample": label(d)},
                              f"{name}, {label(d)}: DO {fmt(d['value'])} mg/l and BOD {fmt(b['value'])} mg/l in the "
                              f"same sample. Unusual combination, check the report.",
                              [d["id"], b["id"]])

rk_ids = [e["id"] for e in evidence if e["ghat"] in ("kamla_park_kund", "rani_kamlapati_ghat") and numeric(e)]
rk_f = sum(EV[i]["status"] == "fail" for i in rk_ids)
add_alert("data", "SITE_TWO_PLACES", "rani_kamlapati_ghat",
          {"site_group": RK_SITE, "fails": rk_f, "n": len(rk_ids)},
          "The report names this point \"Rani Kamlapati, Kamla Park, murti visarjan kund\" in Ganesh tables and "
          "\"Rani Kamlapati visarjan ghat (lower lake)\" in Durga tables. These may be two places, so they are shown "
          f"separately. Combined: {rk_f} of {len(rk_ids)} readings outside the limit.",
          rk_ids)

# ---------------------------------------------------------------- insights
insights = []


def add_insight(tid, params, text, ids):
    assert ids, tid
    insights.append({"id": f"I{len(insights) + 1:02d}", "template_id": tid, "params": params,
                     "text_en": text, "evidence_ids": ids})


pre_bod = [e for e in num_ev if e["parameter"] == "BOD" and e["phase"] == "pre"]
pre_bod_f = [e for e in pre_bod if e["status"] == "fail"]
add_insight("BASELINE_ALREADY_HIGH", {"fails": len(pre_bod_f), "n": len(pre_bod)},
            f"BOD was already above {fmt(BOD_MAX)} mg/l before immersion in {len(pre_bod_f)} of {len(pre_bod)} "
            f"pre-immersion readings. The data does not show what caused these readings.",
            [e["id"] for e in pre_bod_f])

per_ghat_bod = {}
for r in ranking["all"]:
    b = r["per_param_fails"]["BOD"]
    per_ghat_bod[r["ghat"]] = b
lowest = min(per_ghat_bod.items(), key=lambda kv: kv[1]["fails"] / kv[1]["n"])
add_insight("BOD_EVERYWHERE",
            {"fails": bod_f, "n": bod_n, "lowest_ghat": lowest[0], "lowest_fails": lowest[1]["fails"],
             "lowest_n": lowest[1]["n"]},
            f"BOD was above {fmt(BOD_MAX)} mg/l in {bod_f} of {bod_n} readings across all ghats. Even the ghat with the "
            f"lowest share ({GHAT_BY_ID[lowest[0]]['name']}) was above the limit in {lowest[1]['fails']} of "
            f"{lowest[1]['n']}. BOD alone does not separate the ghats; DO does.",
            bod_ids)

do_rank = sorted(ranking["all"], key=lambda r: -(r["per_param_fails"]["DO"]["fails"] / max(r["per_param_fails"]["DO"]["n"], 1)))
top2 = do_rank[:2]
add_insight("WORST_DO_SITES",
            {"ghats": [r["ghat"] for r in top2],
             "fails": [r["per_param_fails"]["DO"]["fails"] for r in top2],
             "n": [r["per_param_fails"]["DO"]["n"] for r in top2]},
            "Lowest dissolved oxygen: " + " and ".join(
                f"{r['name']} ({r['per_param_fails']['DO']['fails']} of {r['per_param_fails']['DO']['n']} DO readings "
                f"below {fmt(DO_MIN)} mg/l)" for r in top2) + ".",
            [e["id"] for e in num_ev if e["parameter"] == "DO" and e["ghat"] in {r["ghat"] for r in top2}
             and e["status"] == "fail"])

fest_stats = {}
for fest in FESTIVALS:
    fe = [e for e in num_ev if e["festival"] == fest]
    fest_stats[fest] = (sum(e["status"] == "fail" for e in fe), len(fe))
dg, gn = fest_stats["Durga"], fest_stats["Ganesh"]
add_insight("DURGA_VS_GANESH",
            {"durga_fails": dg[0], "durga_n": dg[1], "ganesh_fails": gn[0], "ganesh_n": gn[1]},
            f"Across pH, DO and BOD, Durga readings were outside the limit {dg[0]} of {dg[1]} times "
            f"({dg[0] / dg[1]:.0%}) and Ganesh readings {gn[0]} of {gn[1]} times ({gn[0] / gn[1]:.0%}). "
            f"The two festivals fall in different seasons.",
            [e["id"] for e in num_ev if e["status"] == "fail"])

gap_worst = [r for r in top2 if r["durga_2025_missing"]]
if gap_worst:
    add_insight("DATA_GAP_WORST_SITES", {"ghats": [r["ghat"] for r in gap_worst]},
                f"{' and '.join(r['name'] for r in gap_worst)}, the "
                f"{plural(len(gap_worst), 'ghat', 'ghats')} with the lowest DO, "
                f"{plural(len(gap_worst), 'has', 'have')} no Durga 2025 table, so the most recent Durga readings are "
                f"missing where DO was lowest before.",
                [e["id"] for e in evidence if e["status"] == "no_table" and e["ghat"] in {r["ghat"] for r in gap_worst}])

only_during = []
for gid in [g["id"] for g in GHATS]:
    for fest in ghat_festivals(gid):
        rows = {ph: any(numeric(EV[ev_id(2025, fest, gid, ph, p)]) for p in PARAMS) for ph in PHASES}
        if rows["during"] and not rows["pre"] and not rows["after"]:
            only_during.append((gid, fest))
if only_during:
    ids = [ev_id(2025, f, g, ph, p) for g, f in only_during for ph in PHASES for p in PARAMS]
    add_insight("ONLY_DURING_2025",
                {"ghats": [g for g, _ in only_during], "festival": sorted({f for _, f in only_during})},
                f"In {', '.join(sorted({f for _, f in only_during}))} 2025, "
                f"{' and '.join(GHAT_BY_ID[g]['name'] for g, _ in only_during)} have only \"during\" readings; "
                f"pre and after were not sampled (the report suggests temporary kunds).",
                ids)

ph_by_phase = {}
for ph in PHASES:
    pe = [e for e in num_ev if e["parameter"] == "DO" and e["phase"] == ph]
    ph_by_phase[ph] = (sum(e["status"] == "fail" for e in pe), len(pe))
add_insight("DO_BY_PHASE", {ph: {"fails": v[0], "n": v[1]} for ph, v in ph_by_phase.items()},
            f"DO below {fmt(DO_MIN)} mg/l by phase: pre {ph_by_phase['pre'][0]} of {ph_by_phase['pre'][1]}, "
            f"during {ph_by_phase['during'][0]} of {ph_by_phase['during'][1]}, "
            f"after {ph_by_phase['after'][0]} of {ph_by_phase['after'][1]}.",
            do_ids)

# ---------------------------------------------------------------- limitations
limitations = [
    "Only pH, DO and BOD have CPCB class B limits. Total coliform (also a class B limit) was not tested, so no site can be said to meet class B.",
    "Pre-immersion readings already exceed limits often, so the data does not show that immersion caused them.",
    "Units are not printed in the reports; standard units are assumed (mg/l for DO and BOD).",
    "One grab sample per phase; no replicates, sampling times or temperatures are reported.",
    "Bairagarh and Malikhedi have no Durga 2025 table, and only \"during\" readings for Ganesh 2025.",
    "Rani Kamlapati ghat (Durga tables) and Kamla Park kund (Ganesh tables) may be two places; they are shown separately.",
    "2025 metal values of 0.03 / 0.031 repeat across sites and may be detection limits. Metals are not used for ranking.",
    "Latest data is 2025; nothing here predicts conditions on 20 October 2026.",
    "Missing readings (not sampled, or no table in the report) are never counted as within the limit and are left out of the counts.",
    "A value exactly at a limit (DO = 5.0, BOD = 3.0) is counted as within the limit.",
    "The brief is in English only; a Hindi brief has not been produced.",
]

# ---------------------------------------------------------------- write
out = {
    "meta": {
        "generated_on": today.isoformat(),
        "durga_visarjan_date": DURGA_DATE.isoformat(),
        "days_to_durga": days,
        "class_b_limits": LIM,
        "source_csv": "data/bhopal_ghats_2023_2025.csv",
        "years": YEARS,
        "ghats": GHATS,
        "schema_version": "1.0",
    },
    "kpis": kpis,
    "ranking": ranking,
    "alerts": alerts,
    "insights": insights,
    "evidence": evidence,
    "coverage": coverage,
    "limitations": limitations,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- self-check
def self_check():
    k = {x["id"]: (x["value"], x["n"]) for x in kpis}
    print("KPIs:", k)
    assert k["do_below_5"] == (42, 116) and k["bod_above_3"] == (100, 112)
    assert k["ph_out_of_range"] == (6, 115) and k["do_zero"][0] == 4 and k["ghats_no_durga_2025"][0] == 2
    assert all(EV[i]["ghat"] == "bairagarh" for i in z_ids)
    tf = sum(r["fails"] for r in ranking["all"])
    tn = sum(r["n"] for r in ranking["all"])
    print(f"scope all total: {tf}/{tn}")
    assert (tf, tn) == (148, 343)
    for s, rows in ranking.items():
        print(f"-- {s}")
        for r in rows:
            print(f"  {r['rank']}. {r['ghat']:<20} tier {r['tier']} {r['fails']}/{r['n']} "
                  f"rate={r['fail_rate']} tie={r['near_tie']} conf={r['confidence']['level']}")
        for r in rows:
            if r["ghat"] in ("bairagarh", "malikhedi"):
                assert r["tier"] == 1
    exp = {"bairagarh": (24, 39), "malikhedi": (20, 39), "khatlapura": (24, 53), "kamla_park_kund": (12, 27),
           "rani_kamlapati_ghat": (12, 27), "shahpura": (23, 54), "hathaikheda": (19, 54), "prempura": (14, 50)}
    for r in ranking["all"]:
        assert (r["fails"], r["n"]) == exp[r["ghat"]], r["ghat"]
    for c in coverage:
        if c["ghat"] in ("bairagarh", "malikhedi") and c["year"] == 2025 and c["festival"] == "Durga":
            assert c["status"] == "no_table"
    assert len(evidence) == 378 and len(coverage) == 126
    refs = set()
    for x in kpis + alerts + insights:
        refs.update(x["evidence_ids"])
    for rows in ranking.values():
        for r in rows:
            refs.update(r["evidence_ids"])
            if r["worst_DO"]:
                refs.add(r["worst_DO"]["evidence_id"])
    assert refs <= set(EV), refs - set(EV)
    text = json.dumps({k2: v for k2, v in out.items() if k2 != "evidence"}, ensure_ascii=False)
    banned = re.findall(r"\b(safe|unsafe|healthy|unhealthy|clean|disease|illness|skin|dangerous)\b", text, re.I)
    assert not banned, banned
    print(f"evidence={len(evidence)} coverage={len(coverage)} alerts={len(alerts)} insights={len(insights)}")
    print("self-check OK")


if __name__ == "__main__":
    self_check()
