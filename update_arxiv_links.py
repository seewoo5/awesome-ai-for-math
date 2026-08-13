#!/usr/bin/env python3
"""
Update arXiv paper links in README.md to their official published versions.

Strategy
--------
For each README row whose title links to an arXiv preprint, we attempt to
find the official peer-reviewed DOI via two authoritative sources, in order:

  1. arXiv API  — some authors add the published DOI to their arXiv submission
                  after acceptance; the DOI is verified against CrossRef before
                  it is accepted.
  2. CrossRef   — the DOI registration agency used by virtually all major
                  journals; searched by paper title, accepted only when the
                  returned title is sufficiently similar to ours (≥ TITLE_THRESHOLD)
                  and at least one author surname agrees.

If a DOI is found, the following columns are updated:
  - Title:   the arXiv link is replaced with https://doi.org/{DOI}
  - Venue:   if the cell currently says "arXiv …", it is replaced with the
             venue name and year from CrossRef (e.g. "Nature 2021").
             Cells that already contain a non-arXiv venue are left untouched.
  - Links:   [arXiv](original_url) is appended for free-access convenience.

If neither source returns a confident match the row is left entirely untouched.
This is intentionally conservative: a missed update is preferable to a wrong one.

Preprint server DOIs (arXiv, Research Square, …) returned by CrossRef are
explicitly rejected, since they do not represent peer-reviewed publication.

Usage
-----
  python update_arxiv_links.py                  # updates README.md in-place
  python update_arxiv_links.py README_test.md   # safe preview: writes to a copy
"""

import re
import sys
import shutil
import time
import difflib
import unicodedata
import xml.etree.ElementTree as ET
import requests

README_PATH = "README.md"

# Matches the full arXiv abstract URL and captures the paper ID (YYMM.NNNNN).
ARXIV_URL_RE = re.compile(r"https://arxiv\.org/abs/(\d{4}\.\d+)")

ARXIV_API    = "https://export.arxiv.org/api/query"
CROSSREF_API = "https://api.crossref.org/works"

# XML namespaces used in arXiv Atom feed responses.
ARXIV_NS = {
    "atom":  "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

# DOI prefixes belonging to preprint servers rather than peer-reviewed venues.
# Matches on any of these cause the candidate to be skipped.
PREPRINT_DOI_PREFIXES = (
    "10.48550",  # arXiv
    "10.21203",  # Research Square
    "10.20944",  # Preprints.org
    "10.22541",  # Authorea
)

# Minimum SequenceMatcher ratio (0–1) to accept a CrossRef title match.
# 0.90 tolerates minor subtitle or punctuation differences while rejecting
# clearly different papers.
TITLE_THRESHOLD = 0.90

# Delay between consecutive arXiv API calls. arXiv's guideline is ≤ 3 req/s.
ARXIV_DELAY = 3.0

# Delay after CrossRef calls. CrossRef is more permissive but we stay polite.
CROSSREF_DELAY = 1.0

# Preferred short names for venues whose CrossRef container titles differ from
# the naming convention used in the README.
VENUE_ALIASES = {
    "advances in neural information processing systems": "NeurIPS",
}


# ---------------------------------------------------------------------------
# Step 1: arXiv API
# ---------------------------------------------------------------------------

def query_arxiv(arxiv_id: str) -> dict | None:
    """
    Fetch metadata for a single paper from the arXiv Atom API.

    Returns a dict {'title': str, 'doi': str | None, 'authors': list[str]}, or
    None on network / parse error. The title has internal whitespace normalised
    (arXiv XML often contains newlines inside the title element). The doi field
    is the journal-ref DOI submitted by the authors after publication, or None
    if they have not added one. It is still verified against CrossRef metadata
    before use.
    """
    try:
        r = requests.get(ARXIV_API, params={"id_list": arxiv_id}, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"\n  [arxiv error] {e}")
        return None

    root = ET.fromstring(r.text)
    entries = root.findall("atom:entry", ARXIV_NS)
    if not entries:
        return None

    entry = entries[0]
    title_el = entry.find("atom:title", ARXIV_NS)
    doi_el   = entry.find("arxiv:doi",  ARXIV_NS)
    author_els = entry.findall("atom:author/atom:name", ARXIV_NS)

    return {
        # Collapse whitespace: arXiv XML titles may contain literal newlines.
        "title": " ".join(title_el.text.split()) if title_el is not None else "",
        "doi":   doi_el.text.strip()              if doi_el   is not None else None,
        "authors": [
            " ".join(author_el.text.split())
            for author_el in author_els
            if author_el.text
        ],
    }


# ---------------------------------------------------------------------------
# Step 2: CrossRef API
# ---------------------------------------------------------------------------

def title_similarity(a: str, b: str) -> float:
    """Return case-insensitive SequenceMatcher ratio between two title strings."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def author_surname(author: str) -> str:
    """
    Return a comparison key for an author surname.

    arXiv exposes full names while CrossRef has a dedicated family-name field.
    Comparing their final normalised token handles accents (for example,
    "Bradač" versus "Bradac") and multi-word family names conservatively enough
    for use alongside the existing title-similarity threshold.
    """
    ascii_name = unicodedata.normalize("NFKD", author).encode("ascii", "ignore").decode()
    tokens = re.findall(r"[a-z0-9]+", ascii_name.lower())
    return tokens[-1] if tokens else ""


def authors_overlap(arxiv_authors: list[str], crossref_authors: list[str]) -> bool:
    """Return whether the two metadata records share an author surname."""
    arxiv_surnames = {author_surname(author) for author in arxiv_authors}
    crossref_surnames = {author_surname(author) for author in crossref_authors}
    arxiv_surnames.discard("")
    crossref_surnames.discard("")
    return bool(arxiv_surnames & crossref_surnames)


def metadata_matches(
    arxiv_title: str,
    arxiv_authors: list[str],
    crossref_item: dict,
) -> bool:
    """
    Return whether CrossRef metadata confidently describes the arXiv paper.

    Title similarity alone is not sufficient for short, generic titles:
    "Off-diagonal Ramsey numbers" and the unrelated "Off-diagonal book Ramsey
    numbers" score 0.915, above TITLE_THRESHOLD. Requiring an author match
    rejects that false positive and other similarly named papers.
    """
    return (
        title_similarity(arxiv_title, crossref_item.get("title", "")) >= TITLE_THRESHOLD
        and authors_overlap(arxiv_authors, crossref_item.get("authors", []))
    )


def extract_venue_from_item(item: dict) -> str:
    """
    Extract a 'Venue Year' string from a CrossRef work item.

    Uses container-title (journal / proceedings name) and the year from the
    'published' date-parts field. Returns an empty string if neither is found.

    CrossRef sometimes appends a volume number to the container-title
    (e.g. 'Advances in Neural Information Processing Systems 36'). Since we
    already have the year as a separate field, trailing integers are stripped
    from the venue name to avoid redundant or confusing output.
    """
    titles = item.get("container-title", [])
    # CrossRef sometimes returns both a series and a conference name, e.g.
    # ['Lecture Notes in Computer Science', 'Discovery Science']. The last
    # element is always the most specific (the actual venue), so we use that.
    venue_name = titles[-1] if titles else ""
    # Strip trailing volume/issue number (a bare integer at the end of the name).
    venue_name = re.sub(r"\s+\d+$", "", venue_name).strip()
    venue_name = VENUE_ALIASES.get(venue_name.casefold(), venue_name)

    year = ""
    date_parts = item.get("published", {}).get("date-parts", [[]])
    if date_parts and date_parts[0]:
        year = str(date_parts[0][0])

    return f"{venue_name} {year}".strip()


def extract_crossref_metadata(item: dict) -> dict:
    """Extract the DOI, title, author surnames, and venue from a CrossRef item."""
    titles = item.get("title", [])
    authors = [
        author.get("family", "")
        for author in item.get("author", [])
        if author.get("family")
    ]
    return {
        "doi": item.get("DOI", ""),
        "title": titles[0] if titles else "",
        "authors": authors,
        "venue": extract_venue_from_item(item),
    }


def query_crossref_by_title(title: str, authors: list[str]) -> dict | None:
    """
    Search CrossRef for a paper by title.

    Fetches the top 3 scored results and returns metadata for the first result
    whose title similarity exceeds TITLE_THRESHOLD and whose authors overlap
    the arXiv authors. Results whose DOI belongs to a known preprint server
    (PREPRINT_DOI_PREFIXES) are skipped before the metadata checks, since
    CrossRef sometimes indexes preprints alongside journal articles.

    Returns None if no sufficiently similar peer-reviewed match is found.
    The 'venue' value may be an empty string if CrossRef has no container-title.
    """
    try:
        r = requests.get(
            CROSSREF_API,
            params={
                "query.title": title,
                "rows": 3,
                "select": "DOI,title,author,container-title,published",
            },
            timeout=15,
        )
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
    except Exception as e:
        print(f"\n  [crossref error] {e}")
        return None

    for item in items:
        metadata = extract_crossref_metadata(item)
        if not metadata["title"]:
            continue
        doi = metadata["doi"]
        if any(doi.startswith(p) for p in PREPRINT_DOI_PREFIXES):
            continue  # skip preprint server entries
        if metadata_matches(title, authors, metadata):
            return metadata

    return None


def query_crossref_by_doi(doi: str) -> dict | None:
    """
    Fetch venue metadata from CrossRef for a known DOI.

    Used when a DOI was found via the arXiv API. Its title and authors are
    returned along with the venue so the caller can verify that the DOI belongs
    to the same paper. Returns None on error.
    """
    try:
        r = requests.get(f"{CROSSREF_API}/{doi}", timeout=15)
        r.raise_for_status()
        item = r.json().get("message", {})
        return extract_crossref_metadata(item)
    except Exception as e:
        print(f"\n  [crossref doi error] {e}")
        return None


# ---------------------------------------------------------------------------
# README parsing & updating
# ---------------------------------------------------------------------------

def parse_row(line: str) -> list[str] | None:
    """
    Parse a markdown table row into its 4 cell values, or return None.

    Accepts only lines that start and end with '|' and split into exactly 4
    cells on ' | '. The header row ('| Title | … |') and separator row
    ('| :--- | … |') are rejected because their first cell does not start
    with '**[', which is the marker for a paper entry.
    """
    stripped = line.rstrip("\n")
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    # Remove leading and trailing '|', then split on the cell delimiter.
    cells = [c.strip() for c in stripped[1:-1].split(" | ")]
    if len(cells) != 4 or not cells[0].startswith("**["):
        return None
    return cells


def update_readme(input_path: str = README_PATH, output_path: str = README_PATH):
    """
    Read the README at input_path, update arXiv paper rows where a published
    DOI can be found, and write the result to output_path.

    For each updated row, three columns may change:
      - Title:  arXiv URL → https://doi.org/{DOI}
      - Venue:  'arXiv YYYY' → '{Venue Name} {Year}' from CrossRef
                (only overwritten when the current value starts with 'arXiv';
                already-correct venue strings are preserved)
      - Links:  [arXiv](url) appended for free-access convenience

    input_path and output_path may be the same file (in-place update) or
    different files (safe preview). All lines that are not paper rows, or
    whose title link is already non-arXiv, are written through unchanged.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    changes = 0
    skipped = 0

    for line in lines:
        cells = parse_row(line)
        if cells is None:
            updated_lines.append(line)
            continue

        title_cell, subjects_cell, venue_cell, links_cell = cells

        # Extract the hyperlink URL from **[Title](url)**.
        url_match = re.search(r"\*\*\[.+?\]\((.+?)\)\*\*", title_cell)
        if not url_match:
            updated_lines.append(line)
            continue

        current_url = url_match.group(1)

        # Only process rows whose title links to arXiv.
        arxiv_match = ARXIV_URL_RE.fullmatch(current_url)
        if not arxiv_match:
            updated_lines.append(line)
            continue

        arxiv_id  = arxiv_match.group(1)
        arxiv_url = current_url

        print(f"{arxiv_id} ...", end=" ", flush=True)

        doi = None
        venue_str = ""

        # Step 1: check arXiv metadata for an author-submitted DOI.
        meta = query_arxiv(arxiv_id)
        time.sleep(ARXIV_DELAY)
        paper_title = meta["title"] if meta else ""

        authors = meta.get("authors", []) if meta else []

        if meta and meta["doi"]:
            # DOI found via arXiv; verify its title and authors against CrossRef
            # before trusting it, then reuse the CrossRef venue metadata.
            arxiv_doi = meta["doi"]
            cr_meta = query_crossref_by_doi(arxiv_doi)
            time.sleep(CROSSREF_DELAY)
            if cr_meta and metadata_matches(paper_title, authors, cr_meta):
                doi = arxiv_doi
                venue_str = cr_meta["venue"]
                print("arXiv→DOI  ", end="", flush=True)
            else:
                print("arXiv DOI metadata mismatch  ", end="", flush=True)

        if not doi and paper_title:
            # Step 2: fall back to CrossRef title-and-author search.
            cr_meta = query_crossref_by_title(paper_title, authors)
            time.sleep(CROSSREF_DELAY)
            if cr_meta:
                doi = cr_meta["doi"]
                venue_str = cr_meta["venue"]
                print("CrossRef→DOI  ", end="", flush=True)

        if not doi:
            print("no DOI found")
            skipped += 1
            updated_lines.append(line)
            continue

        # Update title link.
        doi_url = f"https://doi.org/{doi}"
        new_title_cell = title_cell.replace(f"]({arxiv_url})", f"]({doi_url})")

        # Update venue only when it currently says "arXiv …" and we have a
        # better value; otherwise keep whatever is already there.
        new_venue_cell = venue_cell
        if venue_cell.lower().startswith("arxiv") and venue_str:
            new_venue_cell = venue_str

        # Append arXiv tag to links.
        arxiv_tag = f"[arXiv]({arxiv_url})"
        new_links_cell = (links_cell + " " + arxiv_tag).strip() if links_cell else arxiv_tag

        new_line = f"| {new_title_cell} | {subjects_cell} | {new_venue_cell} | {new_links_cell} |\n"
        updated_lines.append(new_line)
        changes += 1

        venue_note = f"  (venue: {new_venue_cell})" if new_venue_cell != venue_cell else ""
        print(f"→ {doi_url}{venue_note}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"\nDone. {changes} updated, {skipped} skipped.")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        output = sys.argv[1]
        shutil.copy(README_PATH, output)
        print(f"Working on copy: {output}\n")
        update_readme(output, output)
    else:
        update_readme()
