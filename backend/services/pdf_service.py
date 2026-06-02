"""PDF text extraction and chunking service."""

import logging
from pathlib import Path

from pypdf import PdfReader

from ..config import get_settings

logger = logging.getLogger(__name__)


class PDFService:
    """Handles PDF text extraction and text chunking."""

    def __init__(self) -> None:
        settings = get_settings()
        self.chunk_size: int = settings.CHUNK_SIZE
        self.chunk_overlap: int = settings.CHUNK_OVERLAP

    def extract_text_by_page(self, pdf_path: str | Path) -> list[dict[str, object]]:
        """Extract text from each page of a PDF file.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of dicts with keys: text, page_number (1-indexed).

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            ValueError: If the PDF has no extractable text.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        reader = PdfReader(str(pdf_path))
        pages: list[dict[str, object]] = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append({
                    "text": text,
                    "page_number": page_num,
                })

        return pages

    def get_page_count(self, pdf_path: str | Path) -> int:
        """Return the total number of pages in a PDF.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Number of pages.
        """
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)

    def _recursive_character_split(self, text: str) -> list[str]:
        """Split text into chunks using a recursive character splitting strategy.

        Tries to split on paragraph breaks first, then sentences, then words,
        and finally characters as a last resort. Each chunk respects chunk_size
        and chunk_overlap settings.

        Args:
            text: The input text to split.

        Returns:
            List of text chunks.
        """
        separators = ["\n\n", "\n", ". ", " ", ""]
        return self._split_with_separators(text, separators)

    def _split_with_separators(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using a hierarchy of separators.

        Args:
            text: Text to split.
            separators: Ordered list of separators to try.

        Returns:
            List of text chunks within the configured chunk_size.
        """
        if len(text) <= self.chunk_size:
            stripped = text.strip()
            return [stripped] if stripped else []

        if not separators:
            # Last resort: hard split by character count
            chunks: list[str] = []
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i : i + self.chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
            return chunks

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # Character-level splitting
            chunks = []
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i : i + self.chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
            return chunks

        parts = text.split(separator)

        # Merge small parts into chunks that respect chunk_size
        chunks = []
        current_chunk = ""

        for part in parts:
            part_with_sep = part + separator if separator != "" else part

            if not current_chunk:
                current_chunk = part_with_sep
            elif len(current_chunk) + len(part_with_sep) <= self.chunk_size:
                current_chunk += part_with_sep
            else:
                # Current chunk is big enough or adding would exceed limit
                stripped = current_chunk.strip()
                if stripped:
                    if len(stripped) > self.chunk_size:
                        # This chunk is too large, recursively split with next separator
                        sub_chunks = self._split_with_separators(stripped, remaining_separators)
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(stripped)

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.chunk_overlap :]
                    current_chunk = overlap_text + part_with_sep
                else:
                    current_chunk = part_with_sep

        # Handle the remaining text
        stripped = current_chunk.strip()
        if stripped:
            if len(stripped) > self.chunk_size:
                sub_chunks = self._split_with_separators(stripped, remaining_separators)
                chunks.extend(sub_chunks)
            else:
                chunks.append(stripped)

        return chunks

    def process_pdf(self, pdf_path: str | Path, source_file: str) -> list[dict[str, object]]:
        """Extract text from a PDF and split it into chunks.

        Args:
            pdf_path: Path to the PDF file.
            source_file: The original filename to store in chunk metadata.

        Returns:
            List of dicts with keys: text, page_number, source_file.
        """
        pages = self.extract_text_by_page(pdf_path)

        if not pages:
            logger.warning("No text extracted from PDF: %s", pdf_path)
            return []

        all_chunks: list[dict[str, object]] = []

        for page_data in pages:
            page_text: str = str(page_data["text"])
            page_number: int = int(page_data["page_number"])  # type: ignore[arg-type]

            page_chunks = self._recursive_character_split(page_text)

            for chunk_text in page_chunks:
                all_chunks.append({
                    "text": chunk_text,
                    "page_number": page_number,
                    "source_file": source_file,
                })

        logger.info(
            "Processed PDF '%s': %d pages, %d chunks",
            source_file,
            len(pages),
            len(all_chunks),
        )
        return all_chunks
