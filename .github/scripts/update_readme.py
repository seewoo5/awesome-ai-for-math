import re
from collections import defaultdict

# File paths and markers (using your exact strings)
README_PATH = 'README.md'
TABLE_START_MARKER = '<!-- Table start -->'
TABLE_END_MARKER = '<!-- Table end -->'


def count_by_year(data_rows):
    year_counts = defaultdict(int)
    for row in data_rows:
        # Extract published year from the third column
        # It has a form of (journal name) YYYY or (conference name) YYYY
        # We can split by space and take the last element
        year = row.split('|')[3].strip().split(' ')[-1]
        year_counts[year] += 1
    # Sort by year
    year_counts = dict(sorted(year_counts.items()))
    return year_counts


def update_text_with_year_counts(content):
    """
    Updates a block of text with paper counts from a dictionary.

    Args:
        content (str): The original text content to modify.

    Returns:
        str: The updated text content.
    """
    # 1. Build the new list of strings from the year_counts dictionary
    new_year_lines = []
    year_counts = count_by_year(data_rows)
    for year, count in year_counts.items():
        # Handle pluralization for "paper" vs "papers"
        plural = "paper" if count == 1 else "papers"
        new_year_lines.append(f"    - {count} {plural} in {year}")
    
    # Join the lines into a single string
    new_list_block = "\n".join(new_year_lines) + "\n"

    # 2. Define a regex to find the entire "By years" section
    # This pattern does two things:
    #   - Captures the header line (e.g., "- By years, there are")
    #   - Matches the entire list of year entries that follows it
    pattern = re.compile(
        r"(^- By years, there are\s*$)\n(?:    - \d+ papers? in \d{4}\n?)*",
        re.MULTILINE
    )

    # 3. Define the replacement string
    # It uses a back-reference \g<1> to keep the original header line
    # and then appends the new list block we generated.
    replacement = rf"\g<1>\n{new_list_block}"

    # 4. Perform the substitution
    # The `sub()` method finds the pattern and replaces it.
    updated_content, subs_made = pattern.subn(replacement, content)

    if subs_made == 0:
        print("Warning: Could not find the 'By years' section to update in the text.")

    return updated_content


def count_open_sourced(data_rows):
    """Count the number of papers that are open-sourced."""
    # Check the fourth (last) column and see if the string "[Code]" is present
    count = 0
    for row in data_rows:
        last_cell = row.split('|')[-2].strip()
        if '[Code]' in last_cell:
            count += 1
    return count


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

num_papers = len(data_rows) - 2  # Exclude the header and separator from the count

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

# Open-sourced count
open_sourced_count = count_open_sourced(data_rows)
paper_count_pattern = re.compile(
    r'(?:\d+)(\s+of them are open-sourced.)',
    re.IGNORECASE,
)
new_content, subs_made = paper_count_pattern.subn(rf"{open_sourced_count}\g<1>", new_content, count=1)
if subs_made == 0:
    print("ℹ️ Info: No 'XXX of them are open-sourced.' line found to update.")
else:
    print(f"✅ Updated open-sourced count to {open_sourced_count}.")

# Year-wise count update
new_content = update_text_with_year_counts(new_content)

# Write the corrected content back to the file
with open(README_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ README table sorted successfully while preserving spacing.")
