"""Chat endpoint for RAG-based question answering."""

import logging

from fastapi import APIRouter, HTTPException, status

from ..models.schemas import ChatRequest, ChatResponse, SourceChunk
from ..services.embedding_service import get_embedding_service
from ..services.llm_service import get_llm_service
from ..services.vector_store import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask a question about uploaded documents",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat question using RAG: embed query, retrieve context, generate answer.

    Args:
        request: Chat request with question and optional doc_id filter.

    Returns:
        Chat response with generated answer and source chunks.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    try:
        # Step 1: Embed the question
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.embed_query(question)

        # Step 2: Query ChromaDB for relevant chunks
        vector_store = get_vector_store()
        matched_chunks = vector_store.query(
            query_embedding=query_embedding,
            k=5,
            doc_id=request.doc_id,
        )

        if not matched_chunks:
            return ChatResponse(
                answer="I couldn't find any relevant information in the uploaded documents to answer your question. Please make sure you have uploaded relevant documents.",
                sources=[],
            )

        # Step 3: Generate answer using LLM with context
        llm_service = get_llm_service()
        answer = await llm_service.generate_answer(question, matched_chunks)

        # Step 4: Build source chunks for the response
        sources: list[SourceChunk] = []
        for chunk in matched_chunks:
            # Convert distance to a relevance score (cosine distance: lower = more similar)
            # Score = 1 - distance for cosine, clamped to [0, 1]
            distance = chunk.get("distance", 0.0)
            relevance_score = round(max(0.0, min(1.0, 1.0 - distance)), 4)

            sources.append(
                SourceChunk(
                    text=chunk.get("text", ""),
                    page_number=chunk.get("page_number", 0),
                    relevance_score=relevance_score,
                )
            )

        logger.info(
            "Chat query processed: '%s' -> %d sources, doc_id=%s",
            question[:50],
            len(sources),
            request.doc_id or "all",
        )

        return ChatResponse(answer=answer, sources=sources)

    except RuntimeError as exc:
        logger.error("LLM generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service is currently unavailable: {exc}",
        ) from exc
    except Exception as exc:
        logger.error("Chat processing failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your question: {exc}",
        ) from exc
