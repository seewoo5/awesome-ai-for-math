#!/usr/bin/env python3
"""
Parse the README.md table and generate assets/papers.json for the interactive table.
"""

import json
import re
from pathlib import Path

README_PATH = Path("README.md")
OUTPUT_PATH = Path("assets/papers.json")

TABLE_START_MARKER = "<!-- Table start -->"
TABLE_END_MARKER = "<!-- Table end -->"


def parse_readme():
    content = README_PATH.read_text(encoding="utf-8")

    start = content.index(TABLE_START_MARKER) + len(TABLE_START_MARKER)
    end = content.index(TABLE_END_MARKER)
    table_block = content[start:end].strip()

    lines = table_block.split("\n")
    # Skip header and separator rows
    data_rows = lines[2:]

    papers = []
    all_subjects = set()
    all_years = set()

    for row in data_rows:
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) < 4:
            continue

        title_col = cols[0].strip()
        subj_col = cols[1].strip()
        venue_col = cols[2].strip()
        links_col = cols[3].strip()

        # Parse title and URL: **[Title](URL)**
        title_match = re.search(r"\*\*\[(.*?)\]\((.*?)\)\*\*", title_col)
        if not title_match:
            continue
        title = title_match.group(1)
        url = title_match.group(2)

        # Parse subjects from linked text: [Subject](./subjects/...)
        subjects = re.findall(r"\[([^\]]+)\]\(", subj_col)
        for s in subjects:
            all_subjects.add(s)

        # Parse venue and year using rsplit
        venue_year = venue_col.strip()
        parts = venue_year.rsplit(" ", 1)
        if len(parts) == 2:
            venue = parts[0]
            try:
                year = int(parts[1])
            except ValueError:
                venue = venue_year
                year = 0
        else:
            venue = venue_year
            year = 0

        if year:
            all_years.add(year)

        # Parse resource links: [Label](URL)
        links = []
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", links_col):
            links.append({"label": m.group(1), "url": m.group(2)})

        papers.append(
            {
                "title": title,
                "url": url,
                "subjects": subjects,
                "venue": venue,
                "year": year,
                "links": links,
            }
        )

    return {
        "papers": papers,
        "subjects": sorted(all_subjects),
        "years": sorted(all_years, reverse=True),
    }


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = parse_readme()
    OUTPUT_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Generated {OUTPUT_PATH} with {len(data['papers'])} papers.")


if __name__ == "__main__":
    main()
