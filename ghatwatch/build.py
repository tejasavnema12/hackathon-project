"""Embed ranking.json (+ brief.json, ghat_coords.json) into the repo-root index.html between the DATA markers.

Usage: python ghatwatch/build.py [--fixture]
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
START, END = "/*DATA_START*/", "/*DATA_END*/"


def main():
    src = HERE / ("fixture.json" if "--fixture" in sys.argv else "ranking.json")
    data = json.loads(src.read_text(encoding="utf-8"))
    brief = HERE / "brief.json"
    if src.name == "ranking.json" and brief.exists():
        data["brief"] = json.loads(brief.read_text(encoding="utf-8"))
    coords = HERE / "ghat_coords.json"
    if coords.exists():
        data["coords"] = json.loads(coords.read_text(encoding="utf-8"))

    html_path = HERE.parent / "index.html"
    html = html_path.read_text(encoding="utf-8")
    if html.count(START) != 1 or html.count(END) != 1:
        sys.exit("index.html must contain exactly one DATA_START/DATA_END pair")

    # "</" inside JSON would close the <script> tag early
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    html = pattern.sub(lambda _: START + payload + END, html)
    html_path.write_text(html, encoding="utf-8")
    print(f"embedded {src.name} ({len(payload):,} chars) into index.html; brief={'brief' in data}")


if __name__ == "__main__":
    main()
