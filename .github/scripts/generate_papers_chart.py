"""
Generate a bar chart showing the number of papers by year.
Reads the README.md table and creates a PNG image.
"""
import re
import shutil
from collections import defaultdict
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Install Humor Sans into matplotlib's font directory if available on the system
_humor_sans_sources = [
    Path.home() / 'Library' / 'Fonts' / 'HumorSans.ttf',  # macOS
    Path.home() / '.local' / 'share' / 'fonts' / 'HumorSans.ttf',  # Linux
]
_mpl_ttf_dir = Path(matplotlib.get_data_path()) / 'fonts' / 'ttf'
for src in _humor_sans_sources:
    if src.exists():
        dst = _mpl_ttf_dir / 'HumorSans.ttf'
        if not dst.exists():
            shutil.copy2(src, dst)
        break

# Rebuild font cache so the newly copied font is discovered
fm._load_fontmanager(try_read_cache=False)

README_PATH = 'README.md'
TABLE_START_MARKER = '<!-- Table start -->'
TABLE_END_MARKER = '<!-- Table end -->'
OUTPUT_PATH = 'assets/papers_by_year.png'


def extract_year_counts(readme_content):
    """Extract year counts and open-sourced counts from the README table."""
    try:
        start_index = readme_content.index(TABLE_START_MARKER)
        end_index = readme_content.index(TABLE_END_MARKER)
    except ValueError:
        print(f"Error: Markers not found.")
        return {}, {}

    content_between_markers = readme_content[start_index + len(TABLE_START_MARKER):end_index]
    table_lines = content_between_markers.strip().split('\n')

    if len(table_lines) < 3:
        return {}, {}

    # Skip header and separator
    data_rows = table_lines[2:]

    year_counts = defaultdict(int)
    open_source_counts = defaultdict(int)
    for row in data_rows:
        # Extract year from the third column (Venue & Year)
        # Format: "Venue YYYY" - take the last element after splitting by space
        cells = row.split('|')
        if len(cells) >= 4:
            venue_year = cells[3].strip()
            year_match = re.search(r'\d{4}', venue_year)
            if year_match:
                year = int(year_match.group())
                year_counts[year] += 1
                # Check if open-sourced (has [Code] in the last column)
                if len(cells) >= 5 and '[Code]' in cells[4]:
                    open_source_counts[year] += 1

    years = sorted(year_counts.keys())
    year_counts = {y: year_counts[y] for y in years}
    open_source_counts = {y: open_source_counts[y] for y in years}
    return year_counts, open_source_counts


def generate_bar_chart(year_counts, open_source_counts, output_path):
    """Generate a bar chart from year counts with open-source sub-bars."""
    if not year_counts:
        print("No data to plot.")
        return

    years = list(year_counts.keys())
    counts = list(year_counts.values())
    os_counts = [open_source_counts.get(y, 0) for y in years]

    with plt.xkcd():
        # Override font.family inside the xkcd context so Humor Sans is found
        matplotlib.rcParams['font.family'] = [
            'Humor Sans', 'xkcd', 'xkcd Script', 'Comic Neue', 'Comic Sans MS',
        ]
        plt.figure(figsize=(10, 5))
        # Draw total papers bar (blue)
        bars = plt.bar(years, counts, color='#4285f4', edgecolor='white', linewidth=0.7, label='Total')
        # Draw open-sourced papers bar (orange) on top
        plt.bar(years, os_counts, color='#ff9500', edgecolor='white', linewidth=0.7, label='Open-sourced')

        # Add count labels on top of each bar (total count)
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     str(count), ha='center', va='bottom', fontsize=11, fontweight='bold')

        # Add open-source count labels inside the bar, above the orange sub-bar
        for bar, os_count in zip(bars, os_counts):
            if os_count > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, os_count + 0.3,
                         str(os_count), ha='center', va='bottom', fontsize=9,
                         fontweight='bold', color='#cc7000')

        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Number of Papers', fontsize=12)
        plt.title('Papers by Year', fontsize=14, fontweight='bold')

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

    # Extract year counts
    year_counts, open_source_counts = extract_year_counts(content)
    print(f"Year counts: {year_counts}")
    print(f"Open-source counts: {open_source_counts}")

    # Generate chart
    generate_bar_chart(year_counts, open_source_counts, OUTPUT_PATH)


if __name__ == '__main__':
    main()
