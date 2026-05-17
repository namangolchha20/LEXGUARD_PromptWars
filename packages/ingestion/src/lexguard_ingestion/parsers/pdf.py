import asyncio
import logging
from pathlib import Path

import fitz

from lexguard_ingestion.exceptions import ParseError
from lexguard_ingestion.models import TextBlock

logger = logging.getLogger(__name__)


class PdfParser:
    """Extracts text blocks from PDFs using PyMuPDF, preserving page and font metadata."""

    async def extract_blocks(self, file_path: Path) -> list[TextBlock]:
        return await asyncio.to_thread(self._extract_sync, file_path)

    def _extract_sync(self, file_path: Path) -> list[TextBlock]:
        blocks: list[TextBlock] = []
        try:
            with fitz.open(file_path) as doc:
                outline_blocks = self._extract_outline_sections(doc)
                blocks.extend(outline_blocks)

                for page_index, page in enumerate(doc, start=1):
                    page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                    for block in page_dict.get("blocks", []):
                        if block.get("type") != 0:
                            continue
                        for line in block.get("lines", []):
                            spans = line.get("spans", [])
                            if not spans:
                                continue
                            text = "".join(span.get("text", "") for span in spans).strip()
                            if not text:
                                continue
                            primary = max(spans, key=lambda s: len(s.get("text", "")))
                            font_size = float(primary.get("size", 12.0))
                            flags = int(primary.get("flags", 0))
                            is_bold = bool(flags & 2**4)
                            blocks.append(
                                TextBlock(
                                    text=text,
                                    page=page_index,
                                    font_size=font_size,
                                    is_bold=is_bold,
                                )
                            )

        except Exception as exc:
            raise ParseError(f"Failed to parse PDF: {exc}") from exc

        if not blocks:
            logger.warning("No text extracted from PDF %s", file_path.name)

        return blocks

    def _extract_outline_sections(self, doc: fitz.Document) -> list[TextBlock]:
        """Use PDF bookmarks/outline as heading hints for hierarchy preservation."""
        toc = doc.get_toc()
        if not toc:
            return []

        blocks: list[TextBlock] = []
        for level, title, page in toc:
            blocks.append(
                TextBlock(
                    text=title.strip(),
                    page=max(page, 1),
                    level=level,
                    is_bold=True,
                    font_size=14.0 + (4 - min(level, 4)),
                )
            )
        return blocks

    async def needs_ocr(self, file_path: Path, min_chars_per_page: int) -> bool:
        return await asyncio.to_thread(self._needs_ocr_sync, file_path, min_chars_per_page)

    def _needs_ocr_sync(self, file_path: Path, min_chars_per_page: int) -> bool:
        try:
            with fitz.open(file_path) as doc:
                if doc.page_count == 0:
                    return True
                total_chars = sum(len(page.get_text().strip()) for page in doc)
                avg_chars = total_chars / doc.page_count
                return avg_chars < min_chars_per_page
        except Exception:
            return True
