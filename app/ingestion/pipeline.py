# app/ingestion/pipeline.py
import json
from pathlib import Path

from app.ingestion.cleaner import clean_page_text
from app.ingestion.loaders import load_docx, load_pdf
from app.ingestion.schema import Section
import uuid

from app.core.config import get_settings
from app.ingestion.chunker import make_header, merge_pages, split_law, split_oversized

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/processed/sections.jsonl")

# folder under data/raw -> doc_type tag
DOC_TYPES = {"labor-law": "law", "handbook": "handbook"}


def load_document(path: Path, doc_type: str) -> list[Section]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        sections = load_pdf(path)
        for s in sections:
            s.text = clean_page_text(s.text)
    elif suffix == ".docx":
        sections = load_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {path.name}")

    sections = [s for s in sections if s.text.strip()]
    for s in sections:
        s.metadata["doc_type"] = doc_type
    return sections


def ingest_all(raw_dir: Path = RAW_DIR) -> list[Section]:
    all_sections: list[Section] = []
    for folder_name, doc_type in DOC_TYPES.items():
        for path in sorted((raw_dir / folder_name).glob("*")):
            if path.suffix.lower() in {".pdf", ".docx"}:
                all_sections.extend(load_document(path, doc_type))
    return all_sections


def save_sections(sections: list[Section], out_path: Path = OUT_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for s in sections:
            record = {"text": s.text, "metadata": s.metadata}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

DOC_LABELS = {"law": "Labour Act 2074", "handbook": "Employee Handbook"}
CHUNKS_PATH = Path("data/processed/chunks.jsonl")


def build_chunks(sections: list[Section], max_chars: int) -> list[dict]:
    # 1. group by file, then split each file by its own structure
    by_source: dict[str, list[Section]] = {}
    for s in sections:
        by_source.setdefault(s.metadata["source"], []).append(s)

    units: list[Section] = []
    for source, secs in by_source.items():
        doc_type = secs[0].metadata["doc_type"]
        if doc_type == "law":
            text, starts = merge_pages(secs)
            units.extend(split_law(text, starts, source, doc_type))
        else:
            units.extend(secs)

    # 2. cap the size, add the header and a stable id
    chunks: list[dict] = []
    for unit in units:
        for part in split_oversized(unit, max_chars):
            meta = part.metadata
            header = make_header(meta, DOC_LABELS[meta["doc_type"]])
            where = meta.get("section_number") or meta.get("heading") or "front"
            key = f"{meta['source']}|{where}|{meta['part']}"
            chunks.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                "text": part.text,
                "embed_text": f"{header}\n{part.text}",
                "metadata": {**meta, "header": header},
            })

    ids = [c["id"] for c in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate chunk ids: two sections share the same key")
    return chunks


def save_chunks(chunks: list[dict], out_path: Path = CHUNKS_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
if __name__ == "__main__":
    sections = ingest_all()
    save_sections(sections)
    chunks = build_chunks(sections, get_settings().chunk_size)
    save_chunks(chunks)
    print(f"Saved {len(sections)} sections and {len(chunks)} chunks")