from qdrant_client import QdrantClient, models
from app.core.config import get_settings
    
def get_client() -> QdrantClient:
    """
    Create and return a Qdrant client instance using the configured URL and API key.

    Returns:
        QdrantClient: An instance of the Qdrant client.
    """
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url)

def reset_collection(client: QdrantClient) -> None:
    """Drop the collection if it exists (full rebuild)."""
    name = get_settings().collection_name
    if client.collection_exists(name):
        client.delete_collection(name)


def ensure_collection(client: QdrantClient, dim: int) -> None:
    name = get_settings().collection_name
    if client.collection_exists(name):
        existing = client.get_collection(name).config.params.vectors.size
        if existing != dim:
            raise ValueError(
                f"Collection '{name}' has {existing}-dim vectors but the model makes {dim}. "
                "Use a new collection_name when you change the embedding model."
            )
        return
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
    )
    # lets us filter by document type quickly (law vs handbook)
    client.create_payload_index(
        name, field_name="doc_type", field_schema=models.PayloadSchemaType.KEYWORD
    )


def upsert_chunks(client: QdrantClient, chunks: list[dict],
                  vectors: list[list[float]], batch_size: int = 64) -> None:
    name = get_settings().collection_name
    for i in range(0, len(chunks), batch_size):
        points = [
            models.PointStruct(
                id=c["id"],
                vector=v,
                payload={"text": c["text"], **c["metadata"]},
            )
            for c, v in zip(chunks[i : i + batch_size], vectors[i : i + batch_size])
        ]
        client.upsert(collection_name=name, points=points, wait=True)