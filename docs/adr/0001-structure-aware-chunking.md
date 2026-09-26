# ADR 0001: Structure-aware chunking instead of fixed-size chunking

## Status
Accepted

## Context
The corpus mixes prose (handbook narrative, Labour Act sections) with
tables (leave entitlements, minimum wage, SSF contribution rates). Naive
fixed-size (character/token count) chunking splits by raw length with no
awareness of sentence or table-row boundaries.

## Decision
Chunk prose and tables differently, based on document structure rather
than character count:

- **Prose**: split along paragraph/sentence boundaries, never mid-sentence.
- **Tables**: never chunk by character count. Flatten each row into a
  self-contained unit that repeats the column headers as labels — e.g.
  `Leave Type: Sick leave. Entitlement: 8 days per year, fully paid.
  Key conditions: ...` — instead of relying on the header row being
  retrieved alongside the data row.

## Alternatives considered
- **Fixed-size chunking with overlap**: simplest to implement, but
  demonstrably breaks table rows (splits a leave-type label from its
  entitlement value into separate chunks, so retrieval loses the
  connection between the two) and can cut prose mid-sentence, producing
  embeddings for semantically incomplete fragments.
- **Whole-table-as-one-chunk**: keeps a table intact, but for a table
  with many rows this produces an oversized chunk with poor retrieval
  precision — a query about one leave type would retrieve the entire
  table, including irrelevant rows.

## Consequences
- Requires a document parser that classifies blocks (prose vs. table)
  before chunking, rather than a single one-size-fits-all splitter.
- Table row flattening means the same information is stored slightly
  more verbosely (headers repeated per row), which is an acceptable
  tradeoff for retrieval correctness.
- Heading detection in this corpus relies on a bold-numbered-title regex
  (`**1.1 Title**`) rather than real markdown headings, because the
  source .docx has no semantic heading structure. This is fragile if a
  future document uses a different convention — worth revisiting if the
  corpus grows.
