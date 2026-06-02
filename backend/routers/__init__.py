"""API routers for the IntelliPDF RAG application."""

from .chat import router as chat_router
from .documents import router as documents_router

__all__ = ["documents_router", "chat_router"]
