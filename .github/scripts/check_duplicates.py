#!/usr/bin/env python3
"""
Script to check for duplicate papers in the README table.
Duplicates are detected by:
1. Exact title match (case-insensitive)
2. Same URL in the title link

Exits with code 1 if duplicates are found, 0 otherwise.
"""

import re
import sys
from collections import defaultdict

README_PATH = 'README.md'
TABLE_START_MARKER = '<!-- Table start -->'
TABLE_END_MARKER = '<!-- Table end -->'


def extract_title_and_url(cell: str) -> tuple[str, str | None]:
    """
    Extract the title text and URL from a table cell.
    Handles formats like: **[Title](url)**
    Returns (title, url) where url may be None if not found.
    """
    # Match markdown link pattern: [text](url)
    link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', cell)
    if link_match:
        title = link_match.group(1).strip()
        url = link_match.group(2).strip()
        return title, url
    # Fallback: return the cell text without formatting
    plain_text = re.sub(r'[*_`]', '', cell).strip()
    return plain_text, None


def parse_table_rows(content: str) -> list[dict]:
    """
    Parse the README content and extract paper information from the table.
    Returns a list of dicts with 'title', 'url', and 'row_num' keys.
    """
    try:
        start_index = content.index(TABLE_START_MARKER)
        end_index = content.index(TABLE_END_MARKER)
    except ValueError:
        print(f"Error: Markers '{TABLE_START_MARKER}' or '{TABLE_END_MARKER}' not found.")
        sys.exit(1)

    table_content = content[start_index + len(TABLE_START_MARKER):end_index].strip()
    table_lines = table_content.split('\n')

    if len(table_lines) < 3:
        print("Error: Table must have header, separator, and at least one data row.")
        sys.exit(1)

    # Skip header (line 0) and separator (line 1)
    data_rows = table_lines[2:]
    papers = []

    for i, row in enumerate(data_rows, start=1):
        cols = row.split('|')
        if len(cols) < 2:
            continue
        title_cell = cols[1].strip()
        title, url = extract_title_and_url(title_cell)
        if title:
            papers.append({
                'title': title,
                'url': url,
                'row_num': i
            })

    return papers


def find_duplicates(papers: list[dict]) -> tuple[dict, dict]:
    """
    Find duplicate papers by title and URL.
    Returns two dicts:
    - title_duplicates: {normalized_title: [list of paper dicts]}
    - url_duplicates: {url: [list of paper dicts]}
    """
    title_groups = defaultdict(list)
    url_groups = defaultdict(list)

    for paper in papers:
        # Normalize title for comparison (lowercase, strip extra whitespace)
        normalized_title = ' '.join(paper['title'].lower().split())
        title_groups[normalized_title].append(paper)

        if paper['url']:
            url_groups[paper['url']].append(paper)

    # Filter to only groups with duplicates
    title_duplicates = {k: v for k, v in title_groups.items() if len(v) > 1}
    url_duplicates = {k: v for k, v in url_groups.items() if len(v) > 1}

    return title_duplicates, url_duplicates


def main():
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {README_PATH} not found.")
        sys.exit(1)

    papers = parse_table_rows(content)
    print(f"Found {len(papers)} papers in the table.")

    title_duplicates, url_duplicates = find_duplicates(papers)

    has_duplicates = False

    if title_duplicates:
        has_duplicates = True
        print("\n❌ Duplicate titles found:")
        for title, papers_list in title_duplicates.items():
            print(f"\n  Title: \"{papers_list[0]['title']}\"")
            for p in papers_list:
                print(f"    - Row {p['row_num']}: {p['url'] or 'no URL'}")

    if url_duplicates:
        has_duplicates = True
        print("\n❌ Duplicate URLs found:")
        for url, papers_list in url_duplicates.items():
            print(f"\n  URL: {url}")
            for p in papers_list:
                print(f"    - Row {p['row_num']}: \"{p['title']}\"")

    if has_duplicates:
        print("\n❌ Duplicate check failed!")
        sys.exit(1)
    else:
        print("\n✅ No duplicates found!")
        sys.exit(0)


if __name__ == '__main__':
    main()
