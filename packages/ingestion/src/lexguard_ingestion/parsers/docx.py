import asyncio
import logging
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

from lexguard_ingestion.exceptions import ParseError
from lexguard_ingestion.models import TextBlock

logger = logging.getLogger(__name__)

_HEADING_PREFIX = "Heading"


class DocxParser:
    """Extracts structured blocks from DOCX using Word heading styles."""

    async def extract_blocks(self, file_path: Path) -> list[TextBlock]:
        return await asyncio.to_thread(self._extract_sync, file_path)

    def _extract_sync(self, file_path: Path) -> list[TextBlock]:
        blocks: list[TextBlock] = []
        try:
            document = Document(file_path)
            page_estimate = 1

            for paragraph in document.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue

                level = self._heading_level(paragraph)
                blocks.append(
                    TextBlock(
                        text=text,
                        page=page_estimate,
                        level=level,
                        is_bold=level > 0,
                        font_size=16.0 - min(level, 3) if level > 0 else 12.0,
                    )
                )

                if paragraph.paragraph_format.page_break_before:
                    page_estimate += 1

        except Exception as exc:
            raise ParseError(f"Failed to parse DOCX: {exc}") from exc

        if not blocks:
            logger.warning("No content extracted from DOCX %s", file_path.name)

        return blocks

    def _heading_level(self, paragraph: Paragraph) -> int:
        style_name = (paragraph.style.name or "") if paragraph.style else ""
        if style_name.startswith(_HEADING_PREFIX):
            try:
                return int(style_name.replace(_HEADING_PREFIX, "").strip())
            except ValueError:
                return 1
        return 0
