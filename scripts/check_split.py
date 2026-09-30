# scripts/check_split.py
import json

from app.ingestion.chunker import merge_pages, split_law
from app.ingestion.schema import Section

law = []
for line in open("data/processed/sections.jsonl", encoding="utf-8"):
    rec = json.loads(line)
    if rec["metadata"]["doc_type"] == "law":
        law.append(Section(**rec))

text, starts = merge_pages(law)
secs = split_law(text, starts, "NepalLaborAct.pdf")

print(len(secs), "records (expect 184 = preamble + 183 sections)")
nums = [s.metadata["section_number"] for s in secs if s.metadata["section_number"]]
print("numbers 1..183 in order:", nums == list(range(1, 184)))
print("distinct chapter values:", len({s.metadata["chapter"] for s in secs}), "(expect 25 = 24 + empty preamble)")
print("chapter lines left inside bodies:",
      sum(1 for s in secs if any(l.startswith("Chapter-") for l in s.text.split("\n"))), "(expect 0)")
print("sections spanning 2+ pages:", sum(1 for s in secs if s.metadata["page"] != s.metadata["page_end"]))

lengths = sorted(len(s.text) for s in secs)
print("chars min / median / max:", lengths[0], lengths[len(lengths) // 2], lengths[-1])
big = sorted(secs, key=lambda s: -len(s.text))[:5]
print("biggest:", [(s.metadata["section_number"], s.metadata["section_title"], len(s.text)) for s in big])

s = secs[4]  # section 4: forced labour
print(s.metadata)
print(s.text[:300])