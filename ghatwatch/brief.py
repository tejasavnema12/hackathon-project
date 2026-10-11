"""GhatWatch brief generator (A3).

Reads ghatwatch/ranking.json (fallback ghatwatch/fixture.json, or a path given
as the first CLI argument), fills the English template from
brief_templates.json and writes ghatwatch/brief.json.

Deterministic: no network, no LLM, no API keys. Every number comes from the JSON.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOP_N = 3
BANNED = ["unsafe", "safe", "unhealthy", "healthy", "clean", "disease", "illness",
          "skin", "fish death", "polluted beyond repair"]
ALLOWED_PHRASE = "missing is not a clean result"


def load_input():
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if not p.is_absolute() and not p.exists():
            p = HERE / sys.argv[1]
    else:
        p = HERE / "ranking.json"
        if not p.exists():
            p = HERE / "fixture.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f), p


def fmt_num(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return f"{v:g}" if isinstance(v, float) else str(v)


def join_names(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def action_short(action):
    head = action.split(":", 1)[0]
    if ":" in action and len(head.split()) <= 2:
        return head  # "Priority", "Watch", "Routine"
    first = action.split(".", 1)[0]
    return re.sub(r"\s*\([^)]*\)", "", first).strip()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    data, src = load_input()
    with open(HERE / "brief_templates.json", encoding="utf-8") as f:
        T = json.load(f)["en"]

    meta = data["meta"]
    rows = sorted(data["ranking"]["durga"], key=lambda r: r["rank"])
    years = meta.get("years") or []
    year_min, year_max = (min(years), max(years)) if years else ("", "")

    vdate = date.fromisoformat(meta["durga_visarjan_date"])
    visarjan_date_long = f"{vdate.day} {vdate:%B %Y}"
    days = meta.get("days_to_durga")
    if days is None:
        days = (vdate - date.fromisoformat(meta["generated_on"])).days
    if days > 1:
        days_phrase = T["days_left"].format(days_to_durga=days)
    elif days == 1:
        days_phrase = T["days_one"].format(days_to_durga=days)
    elif days == 0:
        days_phrase = T["days_today"]
    else:
        days_phrase = T["days_past"]

    do_unit = (meta.get("class_b_limits", {}).get("DO", {}) or {}).get("unit", "mg/l")

    lines = [T["title"].format(visarjan_date_long=visarjan_date_long, days_phrase=days_phrase), ""]
    lines.append(T["top_header"].format(year_min=year_min, year_max=year_max))

    top = rows[:TOP_N]
    for i, r in enumerate(rows[:TOP_N]):
        tie_note = ""
        if r.get("near_tie"):
            partners = [rows[j]["name"] for j in (i - 1, i + 1)
                        if 0 <= j < len(rows) and rows[j].get("near_tie")
                        and rows[j]["tier"] == r["tier"]]
            tie_note = (T["tie_note_with"].format(tie_partner=join_names(partners))
                        if partners else T["tie_note_alone"].format(tier=r["tier"]))
        wd = r.get("worst_DO")
        if not wd or wd.get("value") is None:
            do_phrase = T["do_null"]
        elif wd["value"] == 0:
            do_phrase = T["do_zero"]
        else:
            do_phrase = T["do_value"].format(worst_do=fmt_num(wd["value"]), do_unit=do_unit)
        gap_note = T["gap_note_durga"].format(latest_year=year_max) if r.get("durga_2025_missing") else ""
        lines.append(T["ghat_line"].format(ghat_name=r["name"], tier=r["tier"], tie_note=tie_note,
                                           fails=r["fails"], n=r["n"], do_phrase=do_phrase,
                                           gap_note=gap_note))
        lines.append(T["action_line"].format(action_short=action_short(r["action"])))

    # Data gaps (all Durga rows, not only the top ones)
    durga_missing = [r["name"] for r in rows if r.get("durga_2025_missing")]
    partial = [r["name"] for r in rows if not r.get("durga_2025_missing")
               and (r.get("confidence") or {}).get("missing_festivals")]
    lines.append("")
    if durga_missing:
        partial_sentence = T["gaps_partial"].format(partial_list=join_names(partial)) if partial else ""
        lines.append(T["gaps_line"].format(latest_year=year_max, durga_missing_list=join_names(durga_missing),
                                           partial_sentence=partial_sentence))
    elif partial:
        lines.append(T["gaps_none_durga"].format(partial_list=join_names(partial)))
    else:
        lines.append(T["gaps_none"])

    # Recommended actions: deduplicated action strings of the top ghats
    actions = []
    for r in top:
        if r["action"] not in actions:
            actions.append(r["action"])
    lines.append("")
    lines.append(T["actions_header"])
    for a in actions[:3]:
        lines.append(T["action_item"].format(action=a))

    lines.append("")
    lines.append(T["limitation"])
    lines.append(T["source"].format(year_min=year_min, year_max=year_max))

    text = "\n".join(lines)

    # Guard: banned words (the allowed phrase is removed before checking)
    check = text.lower().replace(ALLOWED_PHRASE, "")
    hits = [w for w in BANNED if re.search(r"\b" + re.escape(w) + r"\b", check)]
    if hits:
        print(f"WARNING: banned words in brief: {hits}", file=sys.stderr)

    out = {"text_en": text, "generated_on": meta["generated_on"], "scope": "durga"}
    with open(HERE / "brief.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(text)
    print(f"\n[brief.py] source: {src.name}, {len(text)} characters, wrote brief.json", file=sys.stderr)


if __name__ == "__main__":
    main()
