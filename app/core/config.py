# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Chunking ---
    chunk_size: int = 1200
    chunk_overlap: int = 120

    # --- Models ---
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"
    llm_model: str = "llama-3.3-70b-versatile"

    # --- Retrieval ---
    top_k_retrieve: int = 20   # candidates pulled from the database
    top_k_final: int = 5       # what survives reranking and reaches the LLM

    # --- Services ---
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "docs_v1"
    groq_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()