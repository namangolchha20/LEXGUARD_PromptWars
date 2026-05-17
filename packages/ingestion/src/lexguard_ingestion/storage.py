import json
import logging
from pathlib import Path

import aiofiles
from lexguard_shared.schemas.document import (
    IngestionStatus,
    IngestionStatusResponse,
    ParsedDocument,
)

logger = logging.getLogger(__name__)


class DocumentStorage:
    """Persists parsed documents and job metadata as structured JSON."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _document_path(self, document_id: str) -> Path:
        return self._output_dir / f"{document_id}.json"

    def _status_path(self, document_id: str) -> Path:
        return self._output_dir / f"{document_id}.status.json"

    async def save_result(self, document: ParsedDocument) -> Path:
        path = self._document_path(document.document_id)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(document.model_dump_json(indent=2))
        logger.info("Saved parsed document to %s", path)
        return path

    async def save_status(self, response: IngestionStatusResponse) -> None:
        path = self._status_path(response.document_id)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(response.model_dump_json(indent=2))

    async def get_status(self, document_id: str) -> IngestionStatusResponse | None:
        path = self._status_path(document_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, encoding="utf-8") as f:
            raw = await f.read()
        if not raw.strip():
            return None
        return IngestionStatusResponse.model_validate(json.loads(raw))

    async def get_result(self, document_id: str) -> ParsedDocument | None:
        path = self._document_path(document_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, encoding="utf-8") as f:
            data = json.loads(await f.read())
        return ParsedDocument.model_validate(data)

    async def update_status(
        self,
        document_id: str,
        status: IngestionStatus,
        *,
        error: str | None = None,
        result: ParsedDocument | None = None,
    ) -> IngestionStatusResponse:
        response = IngestionStatusResponse(
            document_id=document_id,
            status=status,
            error=error,
            result=result,
        )
        await self.save_status(response)
        return response
