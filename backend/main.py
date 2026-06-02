"""IntelliPDF RAG API — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers.chat import router as chat_router
from .routers.documents import router as documents_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create required directories on startup."""
    settings = get_settings()

    # Create data directory
    data_dir = Path(settings.DATA_DIR).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Data directory ready: %s", data_dir)

    # Create vector store directory
    vector_store_dir = Path(settings.VECTOR_STORE_DIR).resolve()
    vector_store_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Vector store directory ready: %s", vector_store_dir)

    logger.info("IntelliPDF RAG API started successfully.")

    yield

    logger.info("IntelliPDF RAG API shutting down.")


# Create FastAPI application
app = FastAPI(
    title="IntelliPDF RAG API",
    description=(
        "A Retrieval-Augmented Generation API for intelligent PDF document "
        "analysis. Upload PDFs, ask questions, and get AI-powered answers "
        "grounded in your documents."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify the API is running.

    Returns:
        Status message confirming the API is operational.
    """
    return {
        "status": "healthy",
        "service": "IntelliPDF RAG API",
        "version": "1.0.0",
    }
