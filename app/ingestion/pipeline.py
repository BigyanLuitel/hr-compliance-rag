# app/ingestion/pipeline.py
import json
from pathlib import Path

from app.ingestion.cleaner import clean_page_text
from app.ingestion.loaders import load_docx, load_pdf
from app.ingestion.schema import Section

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


if __name__ == "__main__":
    sections = ingest_all()
    save_sections(sections)
    print(f"Saved {len(sections)} sections to {OUT_PATH}")