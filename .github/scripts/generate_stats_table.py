"""
Write a papers-by-year statistics table into README.md (between the stats markers),
computed from assets/papers.json. Run after generate_papers_json.py.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

PAPERS_JSON = Path("assets/papers.json")
README_PATH = Path("README.md")
START, END = "<!-- Stats start -->", "<!-- Stats end -->"
LLM_TAGS = ("LLM (major)", "LLM (minor)", "LLM (tool)")

# Same label rules as the interactive page (index.html).
CODE_RE = re.compile(r"\bcode\b", re.I)
CHAT_RE = re.compile(r"\bchat logs?\b|\bCoT\b", re.I)


def pct(part, whole):
    if not whole:
        return "–"
    v = 100 * part / whole
    return f"{v:.1f}%" if 0 < v < 10 else f"{v:.0f}%"


def build_table(papers):
    stats = defaultdict(lambda: defaultdict(int))
    for p in papers:
        for key in (p["year"], "Total"):
            s = stats[key]
            s["papers"] += 1
            tag = next((t for t in LLM_TAGS if t in p["subjects"]), None)
            s[tag or "non-LLM"] += 1
            labels = [l["label"] for l in p["links"]]
            s["code"] += any(CODE_RE.search(l) for l in labels)
            s["chat"] += any(CHAT_RE.search(l) for l in labels)
    rows = [
        "| Year | Papers | LLM (major / minor / tool) | Non-LLM | With code | With chat logs |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    years = sorted((y for y in stats if y != "Total"), reverse=True)
    for key in years + ["Total"]:
        s = stats[key]
        name = f"**{key}**" if key == "Total" else str(key)
        rows.append(
            f"| {name} | {s['papers']:,} | {s['LLM (major)']:,} / {s['LLM (minor)']:,} / {s['LLM (tool)']:,} "
            f"| {s['non-LLM']:,} | {pct(s['code'], s['papers'])} | {pct(s['chat'], s['papers'])} |"
        )
    return "\n".join(rows)


def main():
    papers = json.loads(PAPERS_JSON.read_text(encoding="utf-8"))["papers"]
    readme = README_PATH.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit(f"Markers {START} / {END} not found in {README_PATH}.")
    a = readme.index(START) + len(START)
    b = readme.index(END)
    README_PATH.write_text(readme[:a] + "\n" + build_table(papers) + "\n" + readme[b:], encoding="utf-8")
    print(f"Updated stats table in {README_PATH} ({len(papers)} papers).")


if __name__ == "__main__":
    main()
