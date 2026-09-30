# app/ingestion/loaders.py
import re
from pathlib import Path

import pymupdf
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.ingestion.schema import Section

NUM_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")  # "1. Welcome", "1.1 About"
PLACEHOLDER_PREFIXES = ("use this section",)


# ---------- PDF ----------
def load_pdf(file_path: Path) -> list[Section]:
    sections = []
    with pymupdf.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            if not text.strip():
                continue  # skip blank pages
            sections.append(
                Section(
                    text=text,
                    metadata={"source": file_path.name, "page": page_number},
                )
            )
    return sections


# ---------- DOCX helpers ----------
def _iter_block_items(doc):
    """Yield paragraphs and tables in the order they appear on the page."""
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield Table(child, doc)


def _is_bold(par) -> bool:
    runs = [r for r in par.runs if r.text.strip()]
    return bool(runs) and all(
        r.bold or (r.style is not None and r.style.name == "Strong") for r in runs
    )


def _heading_level(par):
    text = par.text.strip()
    match = NUM_HEADING_RE.match(text)
    if match and _is_bold(par):
        return len(match.group(1).split("."))  # "1" -> 1, "1.1" -> 2
    return None


def _table_to_text(table) -> str:
    rows = table.rows
    if len(rows) < 2:
        return ""
    headers = [c.text.strip() for c in rows[0].cells]
    lines = []
    for row in rows[1:]:
        cells = [c.text.strip() for c in row.cells]
        lines.append("; ".join(f"{h}: {v}" for h, v in zip(headers, cells) if v))
    return "\n".join(lines)


# ---------- DOCX loader ----------
def load_docx(file_path: Path) -> list[Section]:
    doc = Document(file_path)
    sections: list[Section] = []
    heading_path: dict[int, str] = {}  # level -> heading text
    buffer: list[str] = []
    in_toc = False

    def flush():
        text = "\n".join(buffer).strip()
        buffer.clear()
        if text:
            trail = " > ".join(heading_path[k] for k in sorted(heading_path))
            sections.append(
                Section(text=text, metadata={"source": file_path.name, "heading": trail})
            )

    for block in _iter_block_items(doc):
        if isinstance(block, Table):
            buffer.append(_table_to_text(block))
            continue

        text = block.text.strip()
        if not text:
            continue
        if text.lower() == "table of contents":
            in_toc = True
            continue

        level = _heading_level(block)
        if level:
            flush()
            for k in [k for k in heading_path if k >= level]:
                del heading_path[k]       # a new "1.2" ends the old "1.1"
            heading_path[level] = text
            in_toc = False
            continue

        if in_toc or text.lower().startswith(PLACEHOLDER_PREFIXES):
            continue
        if text.lower().startswith("acknowledgement of receipt"):
            break  # everything after this is the sign-off form
        buffer.append(text)

    flush()
    return sections