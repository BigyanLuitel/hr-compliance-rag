
import json

from app.core.config import get_settings
from app.retrieval.embedder import embed_documents, embedding_dim
from app.retrieval.vector_store import (
    ensure_collection, get_client, reset_collection, upsert_chunks,
)


def main() -> None:
    with open("data/processed/chunks.jsonl", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    client = get_client()
    reset_collection(client)
    ensure_collection(client, embedding_dim())

    vectors = embed_documents([c["embed_text"] for c in chunks])
    upsert_chunks(client, chunks, vectors)

    count = client.count(get_settings().collection_name, exact=True).count
    print(f"Indexed {len(chunks)} chunks -> collection has {count} points")


if __name__ == "__main__":
    main()