"""LLM service using Groq's async client for RAG answer generation."""

import logging
from functools import lru_cache
from typing import Any

from groq import AsyncGroq

from ..config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a precise and helpful document analysis assistant. "
    "Follow these rules strictly: 1) Answer ONLY using the provided context, no external knowledge. "
    "2) If the context is insufficient, state clearly: \"I cannot find the answer in the provided documents.\" "
    "3) Format your answer in clean, well-structured markdown: use headings, bullet points, numbered lists, and bold text where appropriate. "
    "4) Keep your answer concise, clear, and easy to read. "
    "5) Cite page numbers when referencing specific facts using [Page X] format. "
)


class LLMService:
    """Handles LLM interactions via the Groq API for answer generation."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model: str = settings.GROQ_MODEL
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    def _build_context_prompt(self, context_chunks: list[dict[str, Any]]) -> str:
        """Build a formatted context string from retrieved chunks.

        Args:
            context_chunks: List of chunk dicts with keys: text, page_number.

        Returns:
            Formatted context string with page number citations.
        """
        if not context_chunks:
            return "No relevant context was found in the documents."

        context_parts: list[str] = []
        for i, chunk in enumerate(context_chunks, start=1):
            page_num = chunk.get("page_number", "unknown")
            text = chunk.get("text", "")
            context_parts.append(
                f"[Source {i} - Page {page_num}]\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    async def generate_answer(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
    ) -> str:
        """Generate an answer to a question using retrieved context chunks.

        Args:
            question: The user's question.
            context_chunks: List of relevant chunk dicts from the vector store.

        Returns:
            The generated answer string.

        Raises:
            RuntimeError: If the Groq API call fails.
        """
        context_text = self._build_context_prompt(context_chunks)

        user_message = (
            f"Context from documents:\n\n{context_text}\n\n"
            f"---\n\n"
            f"Question: {question}\n\n"
            f"Please provide a comprehensive answer based ONLY on the context above. "
            f"Cite page numbers where applicable."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=2048,
            )

            answer = response.choices[0].message.content
            if not answer:
                return "I was unable to generate an answer. Please try rephrasing your question."

            return answer.strip()

        except Exception as exc:
            logger.error("Groq API call failed: %s", exc)
            raise RuntimeError(f"LLM generation failed: {exc}") from exc


@lru_cache()
def get_llm_service() -> LLMService:
    """Return a cached singleton LLMService instance."""
    return LLMService()
