import json
import logging
from pathlib import Path

import aiofiles
from lexguard_shared.schemas.consequence import ConsequenceSimulationResult

logger = logging.getLogger(__name__)


class ConsequenceStorage:
    """Persists consequence simulation results as structured JSON."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, document_id: str) -> Path:
        return self._output_dir / f"{document_id}.consequences.json"

    async def save(self, result: ConsequenceSimulationResult) -> Path:
        path = self._path(result.document_id)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(result.model_dump_json(indent=2))
        logger.info(
            "Saved %d consequence scenarios for %s",
            len(result.scenarios),
            result.document_id,
        )
        return path

    async def load(self, document_id: str) -> ConsequenceSimulationResult | None:
        path = self._path(document_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, encoding="utf-8") as f:
            data = json.loads(await f.read())
        return ConsequenceSimulationResult.model_validate(data)
