"""ChromaDB vector store service for document chunk storage and retrieval."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import get_settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "pdf_documents"


class VectorStoreService:
    """Manages ChromaDB persistent vector store for document chunks."""

    def __init__(self) -> None:
        settings = get_settings()
        persist_dir = Path(settings.VECTOR_STORE_DIR).resolve()
        persist_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Initializing ChromaDB at: %s", persist_dir)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection '%s' ready.", COLLECTION_NAME)

    def add_document(
        self,
        doc_id: str,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Add document chunks with embeddings to the vector store.

        Args:
            doc_id: Unique document identifier.
            chunks: List of chunk dicts with keys: text, page_number, source_file.
            embeddings: Corresponding embedding vectors for each chunk.

        Raises:
            ValueError: If chunks and embeddings have different lengths.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings."
            )

        if not chunks:
            logger.warning("No chunks to add for document '%s'.", doc_id)
            return

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{idx}"
            ids.append(chunk_id)
            documents.append(str(chunk["text"]))
            metadatas.append({
                "doc_id": doc_id,
                "page_number": int(chunk["page_number"]),
                "source_file": str(chunk["source_file"]),
                "chunk_index": idx,
            })

        # ChromaDB has a batch limit; upsert in batches of 500
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self._collection.upsert(
                ids=ids[i:end],
                documents=documents[i:end],
                embeddings=embeddings[i:end],
                metadatas=metadatas[i:end],
            )

        logger.info("Added %d chunks for document '%s'.", len(ids), doc_id)

    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query the vector store for similar chunks.

        Args:
            query_embedding: The query embedding vector.
            k: Number of results to return.
            doc_id: Optional document ID to filter results.

        Returns:
            List of dicts with keys: text, page_number, source_file, distance, doc_id.
        """
        where_filter: dict[str, str] | None = None
        if doc_id:
            where_filter = {"doc_id": doc_id}

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.error("ChromaDB query failed: %s", exc)
            return []

        matched_chunks: list[dict[str, Any]] = []

        if not results or not results.get("documents") or not results["documents"][0]:
            return matched_chunks

        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)

        for doc_text, metadata, distance in zip(documents, metadatas, distances):
            matched_chunks.append({
                "text": doc_text,
                "page_number": metadata.get("page_number", 0),
                "source_file": metadata.get("source_file", ""),
                "doc_id": metadata.get("doc_id", ""),
                "distance": float(distance),
            })

        return matched_chunks

    def delete_document(self, doc_id: str) -> None:
        """Delete all chunks belonging to a specific document.

        Args:
            doc_id: The document ID whose chunks should be removed.
        """
        try:
            self._collection.delete(where={"doc_id": doc_id})
            logger.info("Deleted all chunks for document '%s'.", doc_id)
        except Exception as exc:
            logger.error("Failed to delete document '%s': %s", doc_id, exc)
            raise

    def get_chunks(self, doc_id: str) -> list[dict[str, Any]]:
        """Retrieve all chunks for a specific document.

        Args:
            doc_id: The document ID.

        Returns:
            List of chunk dicts with keys: text, page_number, source_file, chunk_index.
        """
        try:
            results = self._collection.get(
                where={"doc_id": doc_id},
                include=["documents", "metadatas"],
            )
        except Exception as exc:
            logger.error("Failed to retrieve chunks for '%s': %s", doc_id, exc)
            return []

        chunks: list[dict[str, Any]] = []

        if not results or not results.get("documents"):
            return chunks

        documents = results["documents"]
        metadatas = results["metadatas"] if results.get("metadatas") else [{}] * len(documents)

        for doc_text, metadata in zip(documents, metadatas):
            chunks.append({
                "text": doc_text,
                "page_number": metadata.get("page_number", 0),
                "source_file": metadata.get("source_file", ""),
                "chunk_index": metadata.get("chunk_index", 0),
            })

        # Sort by chunk_index for consistent ordering
        chunks.sort(key=lambda c: c.get("chunk_index", 0))

        return chunks

    def list_documents(self) -> list[dict[str, Any]]:
        """List all unique documents in the vector store.

        Returns:
            List of dicts with keys: doc_id, source_file, chunk_count.
        """
        try:
            all_results = self._collection.get(include=["metadatas"])
        except Exception as exc:
            logger.error("Failed to list documents: %s", exc)
            return []

        if not all_results or not all_results.get("metadatas"):
            return []

        doc_map: dict[str, dict[str, Any]] = {}

        for metadata in all_results["metadatas"]:
            if not metadata:
                continue
            d_id = metadata.get("doc_id", "")
            if not d_id:
                continue

            if d_id not in doc_map:
                doc_map[d_id] = {
                    "doc_id": d_id,
                    "source_file": metadata.get("source_file", ""),
                    "chunk_count": 0,
                }
            doc_map[d_id]["chunk_count"] += 1

        return list(doc_map.values())


@lru_cache()
def get_vector_store() -> VectorStoreService:
    """Return a cached singleton VectorStoreService instance."""
    return VectorStoreService()
