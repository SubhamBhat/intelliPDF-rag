"""Embedding service using SentenceTransformers with singleton model caching."""

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from ..config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Manages text embedding using a cached SentenceTransformer model."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model_name: str = settings.EMBEDDING_MODEL
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load and cache the SentenceTransformer model."""
        if self._model is None:
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of text strings into vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each a list of floats).

        Raises:
            ValueError: If texts list is empty.
        """
        if not texts:
            raise ValueError("Cannot embed an empty list of texts.")

        logger.debug("Embedding %d texts...", len(texts))
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into a vector.

        Args:
            text: The query text to embed.

        Returns:
            Embedding vector as a list of floats.

        Raises:
            ValueError: If text is empty.
        """
        if not text.strip():
            raise ValueError("Cannot embed empty text.")

        logger.debug("Embedding query: %.50s...", text)
        embedding = self.model.encode(text, show_progress_bar=False, convert_to_numpy=True)
        return embedding.tolist()


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Return a cached singleton EmbeddingService instance."""
    return EmbeddingService()
