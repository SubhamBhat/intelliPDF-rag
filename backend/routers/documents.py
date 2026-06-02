"""Document management endpoints: upload, list, delete, and get chunks."""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, status

from ..config import get_settings
from ..models.schemas import DeleteResponse, DocumentResponse, UploadResponse
from ..services.embedding_service import get_embedding_service
from ..services.pdf_service import PDFService
from ..services.vector_store import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


def _generate_doc_id(filename: str) -> str:
    """Generate a unique document ID from filename and current timestamp.

    Args:
        filename: Original filename of the uploaded PDF.

    Returns:
        A unique document ID string.
    """
    name_without_ext = Path(filename).stem
    timestamp_hash = hashlib.md5(
        f"{name_without_ext}_{time.time()}".encode()
    ).hexdigest()[:8]
    # Clean the name: replace spaces and special chars with underscores
    clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name_without_ext)
    return f"{clean_name}_{timestamp_hash}"


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
)
async def upload_document(file: UploadFile) -> UploadResponse:
    """Upload a PDF file, extract text, create embeddings, and store in ChromaDB.

    Args:
        file: The uploaded PDF file.

    Returns:
        Upload response with document ID and chunk count.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted. Please upload a .pdf file.",
        )

    settings = get_settings()
    data_dir = Path(settings.DATA_DIR).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique document ID
    doc_id = _generate_doc_id(file.filename)
    save_path = data_dir / f"{doc_id}.pdf"

    try:
        # Save uploaded file to disk
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        with open(save_path, "wb") as f:
            f.write(content)

        logger.info("Saved uploaded PDF to: %s", save_path)

        # Extract text and create chunks
        pdf_service = PDFService()
        chunks = pdf_service.process_pdf(save_path, file.filename)

        if not chunks:
            # Clean up saved file if no text was extracted
            save_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract any text from the uploaded PDF.",
            )

        # Generate embeddings
        embedding_service = get_embedding_service()
        texts = [str(chunk["text"]) for chunk in chunks]
        embeddings = embedding_service.embed_texts(texts)

        # Store in vector database
        vector_store = get_vector_store()
        vector_store.add_document(doc_id, chunks, embeddings)

        # Store metadata about upload time and page count
        page_count = pdf_service.get_page_count(save_path)

        # Save metadata file alongside the PDF
        meta_path = data_dir / f"{doc_id}.meta"
        with open(meta_path, "w", encoding="utf-8") as meta_file:
            meta_file.write(
                f"filename={file.filename}\n"
                f"page_count={page_count}\n"
                f"chunk_count={len(chunks)}\n"
                f"uploaded_at={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
            )

        logger.info(
            "Document '%s' uploaded: %d pages, %d chunks.",
            doc_id,
            page_count,
            len(chunks),
        )

        return UploadResponse(
            doc_id=doc_id,
            filename=file.filename,
            chunk_count=len(chunks),
            message=f"Successfully uploaded and processed '{file.filename}'.",
        )

    except HTTPException:
        raise
    except Exception as exc:
        # Clean up on failure
        save_path.unlink(missing_ok=True)
        logger.error("Upload failed for '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {exc}",
        ) from exc


def _read_meta_file(meta_path: Path) -> dict[str, str]:
    """Read a .meta file and return its contents as a dict.

    Args:
        meta_path: Path to the .meta file.

    Returns:
        Dict of metadata key-value pairs.
    """
    metadata: dict[str, str] = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    metadata[key.strip()] = value.strip()
    return metadata


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List all uploaded documents",
)
async def list_documents() -> list[DocumentResponse]:
    """List all documents that have been uploaded and processed.

    Returns:
        List of document metadata.
    """
    settings = get_settings()
    data_dir = Path(settings.DATA_DIR).resolve()

    if not data_dir.exists():
        return []

    vector_store = get_vector_store()
    stored_docs = vector_store.list_documents()

    # Build a map of doc_id -> chunk_count from vector store
    vs_doc_map: dict[str, int] = {}
    for doc_info in stored_docs:
        vs_doc_map[doc_info["doc_id"]] = doc_info.get("chunk_count", 0)

    documents: list[DocumentResponse] = []

    # Iterate over metadata files in data directory
    for meta_file in sorted(data_dir.glob("*.meta")):
        doc_id = meta_file.stem
        metadata = _read_meta_file(meta_file)

        filename = metadata.get("filename", f"{doc_id}.pdf")
        page_count = int(metadata.get("page_count", "0"))
        uploaded_at = metadata.get("uploaded_at", "unknown")
        chunk_count = vs_doc_map.get(doc_id, int(metadata.get("chunk_count", "0")))

        documents.append(
            DocumentResponse(
                id=doc_id,
                filename=filename,
                page_count=page_count,
                uploaded_at=uploaded_at,
                chunk_count=chunk_count,
            )
        )

    return documents


@router.delete(
    "/{doc_id}",
    response_model=DeleteResponse,
    summary="Delete a document",
)
async def delete_document(doc_id: str) -> DeleteResponse:
    """Delete a document's PDF file and its embeddings from ChromaDB.

    Args:
        doc_id: The document ID to delete.

    Returns:
        Confirmation of deletion.
    """
    settings = get_settings()
    data_dir = Path(settings.DATA_DIR).resolve()

    pdf_path = data_dir / f"{doc_id}.pdf"
    meta_path = data_dir / f"{doc_id}.meta"

    # Check if the document exists (either as file or in vector store)
    vector_store = get_vector_store()
    chunks = vector_store.get_chunks(doc_id)

    if not pdf_path.exists() and not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found.",
        )

    # Delete from vector store
    try:
        vector_store.delete_document(doc_id)
    except Exception as exc:
        logger.error("Failed to delete embeddings for '%s': %s", doc_id, exc)

    # Delete PDF file
    pdf_path.unlink(missing_ok=True)

    # Delete metadata file
    meta_path.unlink(missing_ok=True)

    logger.info("Document '%s' deleted successfully.", doc_id)

    return DeleteResponse(
        message=f"Document '{doc_id}' has been deleted.",
        doc_id=doc_id,
    )


@router.get(
    "/{doc_id}/chunks",
    response_model=list[dict[str, Any]],
    summary="Get all chunks for a document",
)
async def get_document_chunks(doc_id: str) -> list[dict[str, Any]]:
    """Retrieve all text chunks for a specific document.

    Args:
        doc_id: The document ID.

    Returns:
        List of chunk dicts with text, page_number, source_file, and chunk_index.
    """
    vector_store = get_vector_store()
    chunks = vector_store.get_chunks(doc_id)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chunks found for document '{doc_id}'.",
        )

    return chunks
