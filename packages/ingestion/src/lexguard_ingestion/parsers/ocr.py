import asyncio
import logging
from pathlib import Path

import fitz

from lexguard_ingestion.exceptions import OCRError
from lexguard_ingestion.models import TextBlock

logger = logging.getLogger(__name__)

_ocr_engine: object | None = None


def _get_ocr_engine() -> object:
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR

            _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except ImportError as exc:
            raise OCRError(
                "PaddleOCR is not installed. Install with: uv sync --package lexguard-ingestion"
            ) from exc
    return _ocr_engine


class OcrParser:
    """OCR fallback for scanned PDFs using PaddleOCR on PyMuPDF-rendered page images."""

    def __init__(self, render_scale: float = 2.0) -> None:
        self._render_scale = render_scale

    async def extract_blocks(self, file_path: Path) -> list[TextBlock]:
        return await asyncio.to_thread(self._extract_sync, file_path)

    def _extract_sync(self, file_path: Path) -> list[TextBlock]:
        ocr = _get_ocr_engine()
        blocks: list[TextBlock] = []

        try:
            with fitz.open(file_path) as doc:
                for page_index, page in enumerate(doc, start=1):
                    matrix = fitz.Matrix(self._render_scale, self._render_scale)
                    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                    image_bytes = pixmap.tobytes("png")

                    import io

                    import numpy as np
                    from PIL import Image

                    image = Image.open(io.BytesIO(image_bytes))
                    image_array = np.array(image)

                    result = ocr.ocr(image_array, cls=True)
                    if not result or not result[0]:
                        continue

                    for line in result[0]:
                        if not line or len(line) < 2:
                            continue
                        text = line[1][0].strip()
                        confidence = float(line[1][1])
                        if text and confidence >= 0.5:
                            blocks.append(TextBlock(text=text, page=page_index))

        except OCRError:
            raise
        except Exception as exc:
            raise OCRError(f"OCR processing failed: {exc}") from exc

        if not blocks:
            raise OCRError("OCR produced no readable text")

        logger.info("OCR extracted %d text blocks from %s", len(blocks), file_path.name)
        return blocks
