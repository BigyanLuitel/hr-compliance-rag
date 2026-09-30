# check_orphans.py
import json

from app.ingestion.cleaner import ENUM_RE

count = 0
for raw in open("data/processed/sections.jsonl", encoding="utf-8"):
    rec = json.loads(raw)
    for line in rec["text"].split("\n"):
        if ENUM_RE.match(line.strip()):
            print(rec["metadata"], repr(line))
            count += 1
print(count, "orphan marker lines")