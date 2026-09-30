# scripts/smoke_search.py
from app.core.config import get_settings
from app.retrieval.embedder import embed_query
from app.retrieval.vector_store import get_client

QUERIES = [
    "How much weekly leave do employees get?",
    "What is the maximum overtime per week?",
    "Is forced labour allowed?",
    "What is the company's remote work stipend?",   # not in the documents
    "Section 151",                                    # exact reference, not a meaning
]

client = get_client()
for q in QUERIES:
    result = client.query_points(
        get_settings().collection_name,
        query=embed_query(q),
        limit=3,
        with_payload=True,
    )
    print("\nQ:", q)
    for p in result.points:
        print(f"  {p.score:.3f} | {p.payload['header']}")