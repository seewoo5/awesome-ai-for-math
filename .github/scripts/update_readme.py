import re

# File paths and markers (using your exact strings)
README_PATH = 'README.md'
TABLE_START_MARKER = '<!-- Table start -->'
TABLE_END_MARKER = '<!-- Table end -->'
TITLE_LINK_RE = re.compile(r"\*\*\[(.*?)\]\((.*?)\)\*\*")


def parse_row_cells(row):
    """Return parsed table cells for valid paper rows, else None."""
    cols = [c.strip() for c in row.strip('|').split('|')]
    if len(cols) < 4:
        return None
    if not TITLE_LINK_RE.search(cols[0]):
        return None
    return cols


def get_valid_data_rows(data_rows):
    """Keep rows that match the paper-row format used by JSON generation."""
    return [row for row in data_rows if parse_row_cells(row)]


def get_sort_key(row):
    """Extracts text from the first column's Markdown link for sorting."""
    first_cell = row.split('|')[1].strip()
    # Handles bold links like **[Title]**
    match = re.search(r'\[(.*?)\]', first_cell)
    if match:
        return match.group(1).lower()
    return first_cell.lower() # Fallback for plain text


try:
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f"Error: {README_PATH} not found.")
    exit(1)

# Find the table block within the markers
try:
    start_index = content.index(TABLE_START_MARKER)
    end_index = content.index(TABLE_END_MARKER)
except ValueError:
    print(f"Error: Markers '{TABLE_START_MARKER}' or '{TABLE_END_MARKER}' not found.")
    exit(1)

# 1. Isolate the full block between markers, PRESERVING original whitespace
content_between_markers = content[start_index + len(TABLE_START_MARKER):end_index]

# 2. Isolate just the table lines for sorting, removing the surrounding whitespace for now
table_core_content = content_between_markers.strip()
table_lines = table_core_content.split('\n')

# 3. Separate header, separator, and data rows
if len(table_lines) < 2:
    print("Error: Table format is incorrect (must have a header and separator).")
    exit(1)

header = table_lines[0]
separator = table_lines[1]
data_rows = table_lines[2:]
valid_data_rows = get_valid_data_rows(data_rows)
num_papers = len(valid_data_rows)

# 4. Sort only the data rows
sorted_data_rows = sorted(data_rows, key=get_sort_key)

# 5. Reconstruct the sorted core of the table
sorted_table_core = '\n'.join([header, separator] + sorted_data_rows)

# 6. Replace the old table core with the new sorted one, keeping the original surrounding whitespace
new_content_between_markers = content_between_markers.replace(
    table_core_content,
    sorted_table_core
)

# 7. Rebuild the entire README file (with the sorted table)
new_content = (
    content[:start_index + len(TABLE_START_MARKER)] +
    new_content_between_markers +
    content[end_index:]
)

# 8. Update the paper count in the README intro line.
#    The README contains an integer in the phrase below; replace it with the computed count.
#    Example target text: "A curated list of 123 awesome papers ..." (number may use commas, e.g., 1,234)

# Total count
paper_count_pattern = re.compile(
    r'(A curated list of\s+)(?:\d+)(\s+awesome papers)',
    re.IGNORECASE,
)
new_content, subs_made = paper_count_pattern.subn(rf"\g<1>{num_papers}\g<2>", new_content, count=1)

if subs_made == 0:
    print("ℹ️ Info: No 'A curated list of XXX awesome papers' line found to update.")
else:
    print(f"✅ Updated paper count to {num_papers}.")

# Write the corrected content back to the file
with open(README_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ README table sorted successfully while preserving spacing.")
