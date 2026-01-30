"""
Generate a bar chart showing the number of papers by year.
Reads the README.md table and creates a PNG image.
"""
import re
from collections import defaultdict
import matplotlib.pyplot as plt

README_PATH = 'README.md'
TABLE_START_MARKER = '<!-- Table start -->'
TABLE_END_MARKER = '<!-- Table end -->'
OUTPUT_PATH = 'assets/papers_by_year.png'


def extract_year_counts(readme_content):
    """Extract year counts from the README table."""
    try:
        start_index = readme_content.index(TABLE_START_MARKER)
        end_index = readme_content.index(TABLE_END_MARKER)
    except ValueError:
        print(f"Error: Markers not found.")
        return {}

    content_between_markers = readme_content[start_index + len(TABLE_START_MARKER):end_index]
    table_lines = content_between_markers.strip().split('\n')

    if len(table_lines) < 3:
        return {}

    # Skip header and separator
    data_rows = table_lines[2:]

    year_counts = defaultdict(int)
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

    return dict(sorted(year_counts.items()))


def generate_bar_chart(year_counts, output_path):
    """Generate a bar chart from year counts."""
    if not year_counts:
        print("No data to plot.")
        return

    years = list(year_counts.keys())
    counts = list(year_counts.values())

    with plt.xkcd():
        plt.figure(figsize=(10, 5))
        bars = plt.bar(years, counts, color='#4285f4', edgecolor='white', linewidth=0.7)

        # Add count labels on top of each bar
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     str(count), ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Number of Papers', fontsize=12)
        plt.title('Papers by Year', fontsize=14, fontweight='bold')

        # Set integer ticks for x-axis
        plt.xticks(years, [str(y) for y in years], fontsize=10)
        plt.yticks(fontsize=10)

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
    year_counts = extract_year_counts(content)
    print(f"Year counts: {year_counts}")

    # Generate chart
    generate_bar_chart(year_counts, OUTPUT_PATH)


if __name__ == '__main__':
    main()
