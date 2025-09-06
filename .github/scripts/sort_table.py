import re

# File paths and markers
README_PATH = 'README.md'
TABLE_START_MARKER = '<!-- Table start -->'
TABLE_END_MARKER = '<!-- Table end -->'

# Function to extract the sort key (the title text from the Markdown link)
def get_sort_key(row):
    """Extracts text from the first column's Markdown link for sorting."""
    # Get the content of the first cell
    first_cell = row.split('|')[1].strip()
    # Find text inside the brackets, e.g., [Title Text]
    match = re.search(r'\[(.*?)\]', first_cell)
    if match:
        # Return the text, lowercased for case-insensitive sorting
        return match.group(1).lower()
    # Fallback for plain text cells
    return first_cell.lower()

# Read the entire README content
with open(README_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the table within the markers
try:
    start_index = content.index(TABLE_START_MARKER)
    end_index = content.index(TABLE_END_MARKER)
except ValueError:
    print(f"Error: Markers '{TABLE_START_MARKER}' or '{TABLE_END_MARKER}' not found in {README_PATH}.")
    exit(1)

# Isolate the table content
table_content_full = content[start_index + len(TABLE_START_MARKER):end_index]
table_lines = table_content_full.strip().split('\n')

# Separate header, separator, and data rows
header = table_lines[0]
separator = table_lines[1]
data_rows = table_lines[2:]

# Sort the data rows
sorted_data_rows = sorted(data_rows, key=get_sort_key)

# Reconstruct the full table
sorted_table_content = '\n'.join([header, separator] + sorted_data_rows)

# Reconstruct the entire README file with the sorted table
new_content = (
    content[:start_index + len(TABLE_START_MARKER)] +
    '\n' + sorted_table_content + '\n' +
    content[end_index:]
)

# Write the new content back to the README file
with open(README_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ README table sorted successfully.")