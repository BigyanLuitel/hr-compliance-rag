# Data setup

Source documents are kept out of version control (see `.gitignore`) —
committing binary PDFs/DOCX bloats repo history and isn't something a
recruiter reading your code needs to clone. This file documents exactly
what belongs in each folder and where to get it.

## `labor-law/`

Download the official English translation of the Nepal Labour Act, 2074
(2017) from the Law Commission of Nepal (via FAOLEX):

https://faolex.fao.org/docs/pdf/NEP225978.pdf

Save it as `data/labor-law/nepal_labour_act_2074.pdf`.

## `handbook/`

`Nepal_Employee_Handbook_v1.1.docx` — a synthetic company handbook for a
fictional company ("Himalayan Tech Solutions Pvt. Ltd."), written for this
project and grounded in the Labour Act above. It contains two
**deliberately seeded compliance gaps** (see `data/eval/`) used to test
whether the RAG system correctly flags a handbook provision that falls
short of the statutory minimum.

Since this file is small and project-authored (not a large external
download), it's fine to keep it out of `.gitignore` if you'd rather
version it directly — currently it's excluded for consistency with the
"don't commit binaries" rule above. Adjust `.gitignore` if you want it
tracked.

## `eval/`

`eval_ground_truth_handbook_v1.1.md` — the answer key for the two seeded
discrepancies in the handbook. This file IS committed (it's small, plain
text, and documents your eval methodology — worth showing in the repo).
It must never be ingested into the RAG corpus itself; it exists purely
for scoring retrieval/answer quality.
