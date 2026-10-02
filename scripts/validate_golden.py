# scripts/validate_golden.py
import json
from collections import Counter

from evals.metrics import chunk_matches

chunks = [json.loads(l) for l in open("data/processed/chunks.jsonl", encoding="utf-8")]
golden = [json.loads(l) for l in open("evals/golden_set.jsonl", encoding="utf-8") if l.strip()]

problems = 0
seen = set()
review = []

for q in golden:
    if q["id"] in seen:
        print("DUPLICATE id", q["id"]); problems += 1
    seen.add(q["id"])
    if "TODO" in q["expected_answer"]:
        print(q["id"], "expected_answer still TODO"); problems += 1

    review.append(f"=== {q['id']} [{q['type']}] {q['question']}\nEXPECTED: {q['expected_answer']}\n")
    if q["type"] == "unanswerable":
        if q["relevant"]:
            print(q["id"], "is unanswerable but has labels"); problems += 1
        continue
    if not q["relevant"]:
        print(q["id"], "is answerable but 'relevant' is empty"); problems += 1

    for rel in q["relevant"]:
        hits = [c for c in chunks if chunk_matches(c["metadata"], rel)]
        if not hits:
            print(q["id"], "NO CHUNK MATCHES", rel); problems += 1
        for c in hits:
            review.append(f"--- {c['metadata']['header']}\n{c['text']}\n")

print(Counter(q["type"] for q in golden))
print(len(golden), "questions |", problems, "problems")

with open("data/processed/golden_review.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(review))
print("Wrote data/processed/golden_review.txt")