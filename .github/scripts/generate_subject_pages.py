#!/usr/bin/env python3
"""
Script to generate subject-specific pages from a README table and update the README
with links. Intended to be run from the root of the repository. The resulting
subject pages will be written to the `subjects/` directory, and the README
will be updated in place.
"""

import re
from pathlib import Path


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug: lower-case, hyphens for non-alphanum."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def main():
    repo_root = Path('.')
    readme_path = repo_root / 'README.md'
    subjects_dir = repo_root / 'subjects'
    subjects_dir.mkdir(exist_ok=True)

    # Read README into lines
    lines = readme_path.read_text(encoding='utf-8').splitlines()

    # Locate table boundaries: header row with 'Title' and blank line after table
    header_idx = next(
        i for i, line in enumerate(lines)
        if line.strip().startswith('|') and 'Title' in line
    )
    body_start = header_idx + 2  # two lines after header is table body
    # Find first blank line after table or use end of file
    body_end = next(
        (i for i in range(body_start, len(lines)) if lines[i].strip() == ''),
        len(lines)
    )

    header = lines[header_idx]
    separator = lines[header_idx + 1]
    table_rows = lines[body_start:body_end]

    unique_subjects = set()
    parsed_rows = []
    for row in table_rows:
        cols = [c.strip() for c in row.strip('|').split('|')]
        if len(cols) < 4:
            parsed_rows.append((row, []))
            continue
        subj_col = cols[1]
        raw_subjects = [s.strip() for s in re.split(r',\s*', subj_col)]
        subjects = []
        for s in raw_subjects:
            # Remove leading/trailing brackets or parentheses
            s_clean = re.sub(r'^[\[\(]+|[\)\]]+$', '', s).strip()
            if s_clean:
                subjects.append(s_clean)
                unique_subjects.add(s_clean)
        parsed_rows.append((row, subjects))

    # Generate/update subject pages
    for subject in sorted(unique_subjects):
        slug = slugify(subject)
        page_path = subjects_dir / f'{slug}.md'
        # Filter rows containing this subject
        rows_for_subject = [r for r, subs in parsed_rows if subject in subs]
        # Build page content
        md_lines = []
        md_lines.append('---')
        md_lines.append(f'title: {subject}')
        md_lines.append('layout: default')
        md_lines.append('---\n')
        md_lines.append(f'# {subject} papers\n')
        md_lines.append(header)
        md_lines.append(separator)
        md_lines.extend(rows_for_subject)
        page_path.write_text('\n'.join(md_lines), encoding='utf-8')

    # Rewrite subject column in README with links
    new_rows = []
    for row, subjects in parsed_rows:
        if not subjects:
            new_rows.append(row)
            continue
        cols = [c.strip() for c in row.strip('|').split('|')]
        links = [f'[{s}](./subjects/{slugify(s)}.md)' for s in subjects]
        cols[1] = ', '.join(links)
        new_rows.append('| ' + ' | '.join(cols) + ' |')

    updated_lines = lines[:body_start] + new_rows + lines[body_end:]
    readme_path.write_text('\n'.join(updated_lines), encoding='utf-8')


if __name__ == '__main__':
    main()
