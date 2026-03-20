from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Embeddings
    # English+Chinese usable baseline; switch to a stronger Chinese embedding if needed.
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Chroma
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "incidents")

    # LLM (OpenAI-compatible)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # LLM (Ollama)
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


SETTINGS = Settings()

