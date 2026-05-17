import json
import logging
from pathlib import Path

import aiofiles
from lexguard_shared.schemas.risk import DocumentRiskAnalysis

logger = logging.getLogger(__name__)


class RiskStorage:
    """Persists risk analysis results as structured JSON."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, document_id: str) -> Path:
        return self._output_dir / f"{document_id}.risk.json"

    async def save(self, analysis: DocumentRiskAnalysis) -> Path:
        path = self._path(analysis.document_id)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(analysis.model_dump_json(indent=2))
        logger.info(
            "Saved risk analysis for %s (%d findings)",
            analysis.document_id,
            len(analysis.findings),
        )
        return path

    async def load(self, document_id: str) -> DocumentRiskAnalysis | None:
        path = self._path(document_id)
        if not path.exists():
            return None
        async with aiofiles.open(path, encoding="utf-8") as f:
            data = json.loads(await f.read())
        return DocumentRiskAnalysis.model_validate(data)
