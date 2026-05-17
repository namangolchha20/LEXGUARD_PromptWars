import json
import logging
from pathlib import Path

import aiofiles
from lexguard_shared.schemas.clause import ClauseExtractionResult

logger = logging.getLogger(__name__)


class ClauseStorage:
    """Persists clause extraction results as structured JSON."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, document_id: str) -> Path:
        return self._output_dir / f"{document_id}.clauses.json"

    async def save(self, result: ClauseExtractionResult) -> Path:
        path = self._path(result.document_id)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(result.model_dump_json(indent=2))
        logger.info("Saved %d clauses for document %s", len(result.clauses), result.document_id)
        return path

    async def load(self, document_id: str) -> ClauseExtractionResult | None:
        path = self._path(document_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, encoding="utf-8") as f:
            data = json.loads(await f.read())
        return ClauseExtractionResult.model_validate(data)
