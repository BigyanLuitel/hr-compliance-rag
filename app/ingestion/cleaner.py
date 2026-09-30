# app/ingestion/cleaner.py
import re

SITE_NOISE = "lawcommission.gov.np"
# a line that is ONLY a clause marker: "(x)", "(ii)", "5.", "43A."
ENUM_RE = re.compile(r"^(\(\w{1,4}\)|\d{1,3}[A-Za-z]?\.)$")
# "Chapter-2 ..." and "Chapter- 11 ..." (the source has both spellings)
CHAPTER_RE = re.compile(r"^Chapter-\s*\d+")
# a line ending in one of these words is a wrapped cross-reference,
# e.g. "...pursuant to Section" / "151."
REFERENCE_WORDS = {
    "section", "sections", "sub-section", "chapter",
    "rule", "rules", "clause", "article", "schedule",
}
QUOTE_TABLE = str.maketrans(
    {"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'"}
)


def is_block_start(line: str) -> bool:
    return bool(ENUM_RE.match(line) or CHAPTER_RE.match(line))


def remove_page_noise(text: str) -> str:
    """Drop the site header and the lone page number at the top of a page."""
    kept = []
    nonempty_seen = 0
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            nonempty_seen += 1
            if SITE_NOISE in stripped:
                continue
            if nonempty_seen <= 3 and stripped.isdigit():
                continue
        kept.append(line)
    return "\n".join(kept)


def fix_hyphenation(text: str) -> str:
    """'employ-\\nment' -> 'employment'."""
    return re.sub(r"([a-z])-[ \t]*\n[ \t]*([a-z])", r"\1\2", text)


def rebuild_paragraphs(text: str) -> str:
    """Join wrapped lines; start a new block at each clause or chapter marker."""
    lines = [raw.strip() for raw in text.split("\n") if raw.strip()]
    blocks: list[str] = []
    for i, line in enumerate(lines):
        if not blocks:
            blocks.append(line)
            continue
        prev_word = lines[i - 1].split()[-1].lower()
        wrapped_reference = ENUM_RE.match(line) and prev_word in REFERENCE_WORDS
        if is_block_start(line) and not wrapped_reference:
            blocks.append(line)          # new clause starts here
        else:
            blocks[-1] += " " + line     # continuation of the current clause
    return "\n".join(blocks)


def clean_page_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.translate(QUOTE_TABLE)
    text = remove_page_noise(text)
    text = fix_hyphenation(text)
    text = rebuild_paragraphs(text)
    return re.sub(r"[ \t]+", " ", text).strip()