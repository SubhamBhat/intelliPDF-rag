"""Pydantic schemas for API request and response models."""

from typing import Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Response model for document metadata."""

    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    page_count: int = Field(..., description="Number of pages in the PDF")
    uploaded_at: str = Field(..., description="ISO timestamp of when the document was uploaded")
    chunk_count: int = Field(..., description="Number of text chunks extracted from the document")


class ChatRequest(BaseModel):
    """Request model for chat/question endpoint."""

    question: str = Field(..., min_length=1, description="The question to ask about the document(s)")
    doc_id: Optional[str] = Field(default=None, description="Optional document ID to restrict search to")


class SourceChunk(BaseModel):
    """A source chunk returned as evidence for an answer."""

    text: str = Field(..., description="The text content of the chunk")
    page_number: int = Field(..., description="The page number this chunk was extracted from")
    relevance_score: float = Field(..., description="Similarity/relevance score (lower distance = more relevant)")


class ChatResponse(BaseModel):
    """Response model for chat/question endpoint."""

    answer: str = Field(..., description="The generated answer from the LLM")
    sources: list[SourceChunk] = Field(default_factory=list, description="Source chunks used to generate the answer")


class UploadResponse(BaseModel):
    """Response model for document upload."""

    doc_id: str = Field(..., description="Unique document identifier assigned to the upload")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    chunk_count: int = Field(..., description="Number of text chunks created from the document")
    message: str = Field(..., description="Status message")


class DeleteResponse(BaseModel):
    """Response model for document deletion."""

    message: str = Field(..., description="Status message")
    doc_id: str = Field(..., description="The ID of the deleted document")
