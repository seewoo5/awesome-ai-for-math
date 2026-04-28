"""Shared utilities for parsing the README paper table."""

import re


def parse_subjects(subject_cell: str) -> list[str]:
    """
    Parse the subject column from either plain-text or legacy markdown link format.
    Legacy markdown links are normalized to plain text first.

    Example: "Number Theory, LLM"
    """
    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", subject_cell)
    return [s.strip() for s in re.split(r",\s*", normalized) if s.strip()]
