# scripts/check_text.py
import json

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
alltext = "\n".join(c["text"] for c in chunks)

for needle in ["weeklyleave", "employershall", "Employee Name (please print)", "_____"]:
    print(repr(needle), alltext.count(needle))

tails = [c["metadata"]["header"] for c in chunks
         if c["metadata"]["parts"] > 1 and len(c["text"]) < 150]
print("tail fragments:", len(tails), tails)
print("longest chunk:", max(len(c["text"]) for c in chunks))