import re

def update_text_with_year_counts(content, year_counts):
    """
    Updates a block of text with paper counts from a dictionary.

    Args:
        content (str): The original text content to modify.
        year_counts (dict): A dictionary with years as keys and counts as values.

    Returns:
        str: The updated text content.
    """
    # 1. Build the new list of strings from the year_counts dictionary
    new_year_lines = []
    for year, count in year_counts.items():
        # Handle pluralization for "paper" vs "papers"
        plural = "paper" if count == 1 else "papers"
        new_year_lines.append(f"    - {count} {plural} in {year}")
    
    # Join the lines into a single string
    new_list_block = "\n".join(new_year_lines)

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

# --- Example Usage ---

# Your dictionary of year counts
year_counts = {
    2017: 1, 
    2020: 3, 
    2023: 4, 
    2024: 19
}

# The original text you want to update
original_text = """
Some introductory text here.

- By years, there are
    - 1 paper in 2020
    - 3 papers in 2023
    - 19 papers in 2024

Some concluding text here.
"""

# Call the function to get the updated text
new_text = update_text_with_year_counts(original_text, year_counts)

# Print the result
print(new_text)