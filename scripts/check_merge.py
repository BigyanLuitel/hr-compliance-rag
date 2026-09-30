# check_merge.py
import json
import re

from app.ingestion.chunker import merge_pages, page_at
from app.ingestion.schema import Section

law, handbook = [], []
for line in open("data/processed/sections.jsonl", encoding="utf-8"):
    rec = json.loads(line)
    (law if rec["metadata"]["doc_type"] == "law" else handbook).append(Section(**rec))

text, starts = merge_pages(law)
print(len(text), "chars,", len(starts), "pages")

# 1. the two seams we know about
for want in (3, 5):
    off = next(o for o, p in starts if p == want)
    print(f"seam before page {want}:", repr(text[off - 50 : off + 50]))
    print("  page_at ->", page_at(off, starts), "and", page_at(off - 1, starts))

# 2. chapters and section numbering
print(len(re.findall(r"^Chapter-\s*\d+", text, re.M)), "chapter headings (expect 24)")
nums = [int(m.group(1)) for m in re.finditer(r"^(\d{1,3})\. ", text, re.M)]
missing = sorted(set(range(1, max(nums) + 1)) - set(nums))
dupes = sorted({n for n in nums if nums.count(n) > 1})
print("sections found:", len(set(nums)), "| max:", max(nums), "| missing:", missing, "| dupes:", dupes)

# 3. the handbook space check that's still open
hb_text = "\n".join(s.text for s in handbook)
for bad in ["sexualharassment", "ofup", "anyjob", "achild"]:
    print(bad, hb_text.count(bad))