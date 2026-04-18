"""
Generate a bar chart showing the number of papers by year.
Reads the README.md table and creates a PNG image.
"""
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Install Humor Sans into matplotlib's font directory if available on the system
_humor_sans_sources = [
    Path.home() / 'Library' / 'Fonts' / 'HumorSans.ttf',  # macOS
    Path.home() / '.local' / 'share' / 'fonts' / 'HumorSans.ttf',  # Linux
]
_mpl_ttf_dir = Path(matplotlib.get_data_path()) / 'fonts' / 'ttf'
copied_humor_sans = False
for src in _humor_sans_sources:
    if src.exists():
        dst = _mpl_ttf_dir / 'HumorSans.ttf'
        if not dst.exists():
            shutil.copy2(src, dst)
            copied_humor_sans = True
        break

# Rebuild the font cache only when we actually install Humor Sans.
if copied_humor_sans:
    fm._load_fontmanager(try_read_cache=False)

README_PATH = 'README.md'
TABLE_START_MARKER = '<!-- Table start -->'
TABLE_END_MARKER = '<!-- Table end -->'
OUTPUT_PATH = 'assets/papers_by_year.png'
LLM_OUTPUT_PATH = 'assets/llm_papers_by_year.png'
RESOURCE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def extract_table_rows(readme_content):
    """Extract raw table rows from the README table."""
    try:
        start_index = readme_content.index(TABLE_START_MARKER)
        end_index = readme_content.index(TABLE_END_MARKER)
    except ValueError:
        print(f"Error: Markers not found.")
        return []

    content_between_markers = readme_content[start_index + len(TABLE_START_MARKER):end_index]
    table_lines = content_between_markers.strip().split('\n')

    if len(table_lines) < 3:
        return []

    # Skip header and separator
    return table_lines[2:]


def extract_year_counts(data_rows, row_filter=None, subcount_label='[Code]'):
    """Extract per-year counts and sub-counts for rows matching a filter."""
    if row_filter is None:
        row_filter = lambda _row: True

    target_label = subcount_label.strip().strip('[]')
    year_counts = defaultdict(int)
    sub_counts = defaultdict(int)
    for row in data_rows:
        if not row_filter(row):
            continue

        # Extract year from the third column (Venue & Year)
        # Format: "Venue YYYY" - take the last element after splitting by space
        cells = row.split('|')
        if len(cells) >= 4:
            venue_year = cells[3].strip()
            year_match = re.search(r'\d{4}', venue_year)
            if year_match:
                year = int(year_match.group())
                year_counts[year] += 1
                if len(cells) >= 5 and cell_has_resource_label(cells[4], target_label):
                    sub_counts[year] += 1

    years = sorted(year_counts.keys())
    year_counts = {y: year_counts[y] for y in years}
    sub_counts = {y: sub_counts[y] for y in years}
    return year_counts, sub_counts


def cell_has_resource_label(cell, label):
    """Return True if any resource link in cell matches the target label."""
    labels = [m.group(1).strip().lower() for m in RESOURCE_LINK_RE.finditer(cell)]
    target = label.strip().lower()
    if target == 'code':
        return any(re.search(r'\bcode\b', lab) for lab in labels)
    return any(lab == target or lab.startswith(f'{target} ') or lab.startswith(f'{target}(') for lab in labels)


def generate_bar_chart(
    year_counts,
    sub_counts,
    output_path,
    *,
    title,
    sub_label,
    y_label='Number of Papers',
):
    """Generate a bar chart from year counts with an overlaid subset bar."""
    if not year_counts:
        print("No data to plot.")
        return

    years = list(year_counts.keys())
    counts = list(year_counts.values())
    overlay_counts = [sub_counts.get(y, 0) for y in years]

    with plt.xkcd():
        # Override font.family inside the xkcd context so Humor Sans is found
        matplotlib.rcParams['font.family'] = [
            'Humor Sans', 'xkcd', 'xkcd Script', 'Comic Neue', 'Comic Sans MS',
        ]
        plt.figure(figsize=(10, 5))
        # Draw total papers bar (blue)
        bars = plt.bar(years, counts, color='#4285f4', edgecolor='white', linewidth=0.7, label='Total')
        plt.bar(years, overlay_counts, color='#ff9500', edgecolor='white', linewidth=0.7, label=sub_label)

        # Add count labels on top of each bar (total count)
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     str(count), ha='center', va='bottom', fontsize=11, fontweight='bold')

        # Add open-source count labels inside the bar, above the orange sub-bar
        for bar, overlay_count in zip(bars, overlay_counts):
            if overlay_count > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, overlay_count + 0.3,
                         str(overlay_count), ha='center', va='bottom', fontsize=9,
                         fontweight='bold', color='#cc7000')

        plt.xlabel('Year', fontsize=12)
        plt.ylabel(y_label, fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')

        # Set integer ticks for x-axis
        plt.xticks(years, [str(y) for y in years], fontsize=10)
        plt.yticks(fontsize=10)

        # Add legend
        plt.legend(loc='upper left', fontsize=10)

        # Add some padding at the top for labels
        plt.ylim(0, max(counts) * 1.15)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    print(f"Chart saved to {output_path}")


def main():
    # Read README
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    data_rows = extract_table_rows(content)

    # Generate all-papers chart
    year_counts, open_source_counts = extract_year_counts(data_rows, subcount_label='[Code]')
    print(f"All paper year counts: {year_counts}")
    print(f"All paper open-source counts: {open_source_counts}")
    generate_bar_chart(
        year_counts,
        open_source_counts,
        OUTPUT_PATH,
        title='Papers by Year',
        sub_label='Open-sourced',
    )

    # Generate LLM-only chart
    llm_year_counts, llm_chat_log_counts = extract_year_counts(
        data_rows,
        row_filter=lambda row: '[LLM]' in row,
        subcount_label='[Chat Logs]',
    )
    print(f"LLM paper year counts: {llm_year_counts}")
    print(f"LLM paper chat-log counts: {llm_chat_log_counts}")
    generate_bar_chart(
        llm_year_counts,
        llm_chat_log_counts,
        LLM_OUTPUT_PATH,
        title='LLM Papers by Year',
        sub_label='Chat Logs',
    )


if __name__ == '__main__':
    main()
