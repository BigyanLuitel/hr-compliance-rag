"""
Splits a markdown document into an ordered list of typed blocks
(prose paragraphs vs. tables) so each type can be chunked differently.
"""
from dataclasses import dataclass
from enum import Enum


class BlockType(Enum):
    PROSE = "prose"
    TABLE = "table"
    HEADING = "heading"


@dataclass
class Block:
    block_type: BlockType
    content: str        # raw text/markdown for this block
    heading_path: list  # e.g. ["7. Leave Entitlements"] — which section this block sits under


import re

# Matches: **1. Welcome**  or  **1.1 About Himalayan Tech Solutions...**
# Group 1 = the section number ("1" or "1.1")
# Group 2 = the title text
HEADING_PATTERN = re.compile(r"^\*\*(\d+(?:\.\d+)?)\.?\s+(.+)\*\*$")


def parse_heading(line: str):
    """
    Returns (number_str, title, depth) if this line is a bold numbered
    heading, else None.

    depth is derived by counting dots in the number: "1" -> depth 1,
    "1.1" -> depth 2. This tells us where to place the heading in the
    heading_path stack (replace the current depth-1 entry, or push/replace
    a depth-2 entry under it).

    Limitation: this only handles up to two levels (N or N.N). If any
    section goes to N.N.N, this pattern won't match it — worth checking
    the document for that before trusting this in production.
    """
    match = HEADING_PATTERN.match(line.strip())
    if not match:
        return None
    number, title = match.group(1), match.group(2)
    depth = number.count(".") + 1
    return number, title, depth


def is_table_line(line: str) -> bool:
    """
    A markdown table row looks like: | col1 | col2 | col3 |
    The header-separator row looks like: |---|---|---|
    We just need to detect 'this line is part of a table', not parse it yet.
    """
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")
