import logging
from pathlib import Path
from uuid import uuid4

from lexguard_shared.schemas.document import ParsedDocument

from lexguard_ingestion.config import IngestionSettings
from lexguard_ingestion.exceptions import ParseError
from lexguard_ingestion.extractors.sections import SectionExtractor
from lexguard_ingestion.models import DocumentFormat
from lexguard_ingestion.parsers.docx import DocxParser
from lexguard_ingestion.parsers.ocr import OcrParser
from lexguard_ingestion.parsers.pdf import PdfParser

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates document parsing, OCR fallback, and section extraction."""

    def __init__(self, settings: IngestionSettings | None = None) -> None:
        self._settings = settings or IngestionSettings()
        self._pdf_parser = PdfParser()
        self._docx_parser = DocxParser()
        self._ocr_parser = OcrParser()
        self._section_extractor = SectionExtractor()

    async def process(
        self,
        document_id: str,
        file_path: Path,
        doc_format: DocumentFormat,
    ) -> ParsedDocument:
        logger.info("Processing %s as %s", document_id, doc_format.value)

        if doc_format == DocumentFormat.PDF:
            sections = await self._process_pdf(file_path)
        elif doc_format == DocumentFormat.DOCX:
            sections = await self._process_docx(file_path)
        else:
            raise ParseError(f"Unsupported format: {doc_format}")

        if not sections:
            raise ParseError("No sections extracted from document")

        return ParsedDocument(document_id=document_id, sections=sections)

    async def _process_pdf(self, file_path: Path) -> list:
        use_ocr = await self._pdf_parser.needs_ocr(
            file_path,
            self._settings.ingestion_ocr_min_chars_per_page,
        )

        if use_ocr:
            logger.info("PDF appears scanned — using PaddleOCR fallback for %s", file_path.name)
            blocks = await self._ocr_parser.extract_blocks(file_path)
        else:
            blocks = await self._pdf_parser.extract_blocks(file_path)
            if not blocks:
                logger.info("No text in PDF — falling back to OCR for %s", file_path.name)
                blocks = await self._ocr_parser.extract_blocks(file_path)

        nodes = self._section_extractor.from_blocks(blocks)
        return self._section_extractor.to_schema(nodes)

    async def _process_docx(self, file_path: Path) -> list:
        blocks = await self._docx_parser.extract_blocks(file_path)
        nodes = self._section_extractor.from_blocks(blocks)
        return self._section_extractor.to_schema(nodes)

    async def health_check(self) -> bool:
        return True

    @staticmethod
    def new_document_id() -> str:
        return uuid4().hex
