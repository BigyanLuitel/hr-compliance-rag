# app/ingestion/chunker.py
import re
from bisect import bisect_right

from app.ingestion.cleaner import REFERENCE_WORDS
from app.ingestion.schema import Section

# a line that begins a new clause: "(c) ...", "5. ...", "Chapter-4 ..."
MARKER_START_RE = re.compile(r"^(\(\w{1,4}\)|\d{1,3}[A-Za-z]?\.)(\s|$)|^Chapter-")


def _joiner(prev_text: str, next_text: str) -> str:
    """'\\n' if the next page starts a new clause, ' ' if it continues one."""
    first_line = next_text.lstrip().split("\n", 1)[0]
    last_word = prev_text.rstrip().rsplit(None, 1)[-1].lower()
    starts_new = bool(MARKER_START_RE.match(first_line)) and last_word not in REFERENCE_WORDS
    return "\n" if starts_new else " "


def merge_pages(pages: list[Section]) -> tuple[str, list[tuple[int, int]]]:
    """Join page texts into one string.

    Returns (text, page_starts) where page_starts is a list of
    (character_offset, page_number), one per page.
    """
    text = ""
    page_starts: list[tuple[int, int]] = []
    for p in pages:
        if text:
            text += _joiner(text, p.text)
        page_starts.append((len(text), p.metadata["page"]))
        text += p.text
    return text, page_starts


def page_at(offset: int, page_starts: list[tuple[int, int]]) -> int:
    """Which page does this character offset fall on?"""
    offsets = [o for o, _ in page_starts]
    return page_starts[bisect_right(offsets, offset) - 1][1]

CHAPTER_LINE_RE = re.compile(r"^Chapter-\s*(\d+)\s*(.*)$")
SECTION_LINE_RE = re.compile(r"^(\d{1,3})\.\s+(.+)$")


def _section_title(rest: str) -> str:
    """'Prohibition on employing in forced labour: (1) No person...' -> the part before the colon."""
    head, sep, _ = rest.partition(":")
    return head.strip() if sep and len(head) <= 150 else rest[:80].strip()


def _to_section(cur: dict, page_starts, source: str, doc_type: str):
    body = "\n".join(cur["lines"]).strip()
    if not body:
        return None
    return Section(
        text=body,
        metadata={
            "source": source,
            "doc_type": doc_type,
            "chapter": cur["chapter"],
            "section_number": cur["number"],
            "section_title": cur["title"],
            "page": page_at(cur["start"], page_starts),
            "page_end": page_at(max(cur["end"] - 1, cur["start"]), page_starts),
        },
    )


def split_law(text: str, page_starts, source: str, doc_type: str = "law") -> list[Section]:
    """One Section per numbered legal section, plus one for the preamble."""
    sections: list[Section] = []
    chapter = ""
    expected = 1  # the next section number we will accept
    cur = {"number": None, "title": "Preamble", "chapter": "",
           "lines": [], "start": 0, "end": 0}

    offset = 0
    for line in text.split("\n"):
        start, offset = offset, offset + len(line) + 1  # +1 for the "\n"

        chapter_match = CHAPTER_LINE_RE.match(line)
        if chapter_match:
            chapter = f"Chapter-{chapter_match.group(1)} {chapter_match.group(2)}".strip()
            continue  # a chapter heading is not part of any section's text

        section_match = SECTION_LINE_RE.match(line)
        if section_match and int(section_match.group(1)) == expected:
            done = _to_section(cur, page_starts, source, doc_type)
            if done:
                sections.append(done)
            cur = {"number": expected, "title": _section_title(section_match.group(2)),
                   "chapter": chapter, "lines": [line], "start": start, "end": offset}
            expected += 1
        else:
            cur["lines"].append(line)
            cur["end"] = offset

    done = _to_section(cur, page_starts, source, doc_type)
    if done:
        sections.append(done)
    return sections

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;:])\s+")


def _split_long_line(line: str, max_chars: int) -> list[str]:
    """Fallback for a single clause longer than max_chars: cut at sentence ends."""
    pieces, current = [], ""
    for sentence in SENTENCE_SPLIT_RE.split(line):
        if current and len(current) + 1 + len(sentence) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def split_oversized(sec: Section, max_chars: int) -> list[Section]:
    """Keep small sections whole; pack big ones into groups of whole clauses."""
    if len(sec.text) <= max_chars:
        return [Section(text=sec.text, metadata={**sec.metadata, "part": 1, "parts": 1})]

    units: list[str] = []
    for line in sec.text.split("\n"):
        units.extend([line] if len(line) <= max_chars else _split_long_line(line, max_chars))

    groups, current = [], ""
    for unit in units:
        if current and len(current) + 1 + len(unit) > max_chars:
            groups.append(current)
            current = unit
        else:
            current = f"{current}\n{unit}" if current else unit
    if current:
        groups.append(current)
        # a tiny last group is merged back into the previous one (soft limit)
    if len(groups) > 1 and len(groups[-1]) < 150 and len(groups[-2]) + 1 + len(groups[-1]) <= max_chars + 150:
        last = groups.pop()
        groups[-1] = groups[-1] + "\n" + last

    return [
        Section(text=g, metadata={**sec.metadata, "part": i, "parts": len(groups)})
        for i, g in enumerate(groups, start=1)
    ]

def make_header(meta: dict, doc_label: str) -> str:
    """Breadcrumb prepended to a chunk before embedding."""
    parts = [doc_label]
    if meta.get("chapter"):
        parts.append(meta["chapter"])
    if meta.get("section_number"):
        parts.append(f"Section {meta['section_number']}. {meta['section_title']}")
    elif meta.get("section_title"):
        parts.append(meta["section_title"])      # e.g. "Preamble"
    elif meta.get("heading"):
        parts.append(meta["heading"])            # handbook: "3. Workplace Commitments > 3.1 ..."
    header = " > ".join(parts)
    if meta.get("parts", 1) > 1:
        header += f" (part {meta['part']} of {meta['parts']})"
    return header