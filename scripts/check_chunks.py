# scripts/check_chunks.py
import json
from collections import Counter

from transformers import AutoTokenizer

from app.core.config import get_settings

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
print(len(chunks), "chunks | unique ids:", len({c["id"] for c in chunks}))
print(Counter(c["metadata"]["doc_type"] for c in chunks))

covered = {c["metadata"].get("section_number") for c in chunks if c["metadata"]["doc_type"] == "law"} - {None}
print("law sections covered:", len(covered), "(expect 183) | missing:", sorted(set(range(1, 184)) - covered))

tok = AutoTokenizer.from_pretrained(get_settings().embedding_model)
tok_lens = [len(tok(c["embed_text"])["input_ids"]) for c in chunks]
print("real tokens: max", max(tok_lens), "| over 512:", sum(t > 512 for t in tok_lens))

print("--- chunks under 150 chars ---")
for c in chunks:
    if len(c["text"]) < 150:
        m = c["metadata"]
        print(m.get("section_number"), "|", m["header"], "|", repr(c["text"]))