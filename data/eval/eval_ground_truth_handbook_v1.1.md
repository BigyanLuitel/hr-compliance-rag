# Ground Truth: Known Discrepancies in Nepal_Employee_Handbook_v1.1.docx

This file is NOT part of the RAG corpus. Keep it out of `handbook/` and
`labor-law/` — it exists purely so you (and your eval script) know what the
"correct" answer is when testing the system's ability to catch a handbook
provision that falls short of the Labour Act, 2074 (2017).

## Discrepancy 1 — Sick leave below statutory minimum

- **Handbook says (Section 7, leave table):** 8 days per year, fully paid
- **Law requires (Labour Act §41):** 12 days per year, fully paid
- **Correct system behavior:** when asked "does our sick leave policy comply
  with the law?" or "how many sick days am I entitled to?", the system
  should surface BOTH figures, flag the shortfall, and cite both sources
  (handbook Section 7 + Labour Act §41) — not just answer "8 days" from the
  handbook alone.

## Discrepancy 2 — Paternity leave omitted entirely

- **Handbook says:** nothing — the row was removed from the Section 7 leave
  table between Maternity leave and Leave in lieu.
- **Law requires:** 15 days, fully paid (as correctly stated in the original
  draft, and consistent with Nepal's statutory paternity leave provision).
- **Correct system behavior:** when asked "what's our paternity leave
  policy?" or "am I entitled to paternity leave?", a naive retriever will
  find nothing in the handbook and may either hallucinate an answer or
  answer "not specified." The correct behavior is to check `labor-law/`,
  find the statutory entitlement, and state clearly that the *law*
  guarantees 15 days even though the *handbook* is silent on it — silence
  in a handbook never overrides a statutory minimum (this is explicitly
  stated in the handbook's own Section 1.2).

## Why these two specific cases matter for eval design

- Discrepancy 1 tests **numeric contradiction detection** — two documents
  giving two different numbers for the same entitlement.
- Discrepancy 2 tests **absence-based reasoning** — the harder and more
  common real-world failure mode, where a document's silence gets
  misread as "no entitlement" instead of triggering a check against the
  authoritative source.

Both should appear in your hand-labeled eval query set (from the
requirements doc, Section 3) as cases where a "confidently wrong from a
single source" answer is a failure, and "correctly cites both sources and
flags the gap" is a pass.
