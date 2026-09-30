from functools import lru_cache

from sentence_transformers import SentenceTransformer
from app.core.config import get_settings

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

@lru_cache()
def get_model()-> SentenceTransformer:
    """
    Load the sentence transformer model with caching to avoid reloading it multiple times.
    """
    settings = get_settings()       
    return SentenceTransformer(settings.embedding_model)

def embedding_dim() -> int:
    """
    Get the embedding dimension of the model.
    """
    return get_model().get_sentence_embedding_dimension()

def embed_documents(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    Embed a list of documents using the sentence transformer model.

    Args:
        texts (list[str]): List of document texts to embed.
        batch_size (int): Batch size for embedding.

    Returns:
        list[list[float]]: List of embeddings for each document.
    """
    vectors = get_model().encode(texts, batch_size=batch_size, show_progress_bar=True,normalize_embeddings=True)
    return vectors.tolist()

def embed_query(query: str) -> list[float]:
    """
    Embed a query string using the sentence transformer model.

    Args:
        query (str): The query string to embed.

    Returns:
        list[float]: The embedding for the query.
    """
    prompt = QUERY_PREFIX + query
    vector = get_model().encode([prompt], normalize_embeddings=True)
    return vector[0].tolist()