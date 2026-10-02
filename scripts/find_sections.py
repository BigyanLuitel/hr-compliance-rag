# scripts/find_sections.py
import json
import sys

keyword = " ".join(sys.argv[1:]).lower()
for line in open("data/processed/chunks.jsonl", encoding="utf-8"):
    chunk = json.loads(line)
    if keyword in chunk["text"].lower():
        print(chunk["metadata"]["header"])