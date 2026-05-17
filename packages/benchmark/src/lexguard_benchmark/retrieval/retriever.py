import json
import logging
from functools import lru_cache
from pathlib import Path

from lexguard_shared.schemas.clause import ExtractedClause
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DEFAULT_FILE = _DATA_DIR / "benchmarks.json"


class IndustryBenchmark(BaseModel):
    id: str
    clause_types: list[str]
    metric: str
    label: str
    typical_min: float | None = None
    typical_max: float | None = None
    unit: str
    description: str
    keywords: list[str] = Field(default_factory=list)
    qualitative_fair: list[str] = Field(default_factory=list)
    qualitative_unfair: list[str] = Field(default_factory=list)


class BenchmarkRetriever:
    """Retrieves industry-standard benchmarks relevant to a clause."""

    def __init__(self, data_path: Path | None = None) -> None:
        self._benchmarks = self._load(data_path or _DEFAULT_FILE)

    @staticmethod
    @lru_cache(maxsize=1)
    def _load(path: Path) -> list[IndustryBenchmark]:
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
        benchmarks = [IndustryBenchmark.model_validate(b) for b in raw]
        logger.info("Loaded %d industry benchmarks from %s", len(benchmarks), path)
        return benchmarks

    def retrieve_for_clause(self, clause: ExtractedClause) -> list[IndustryBenchmark]:
        clause_type = clause.clause_type.value
        text_lower = clause.text.lower()
        title_lower = clause.title.lower()
        combined = f"{title_lower} {text_lower}"

        matched: list[tuple[float, IndustryBenchmark]] = []
        for benchmark in self._benchmarks:
            if clause_type not in benchmark.clause_types and clause_type != "other":
                continue
            score = self._relevance_score(benchmark, combined)
            if score >= 0.15 or clause_type in benchmark.clause_types:
                matched.append((score, benchmark))

        matched.sort(key=lambda x: -x[0])
        seen_metrics: set[str] = set()
        results: list[IndustryBenchmark] = []
        for score, benchmark in matched:
            if benchmark.metric in seen_metrics:
                continue
            if score >= 0.15 or clause_type in benchmark.clause_types:
                seen_metrics.add(benchmark.metric)
                results.append(benchmark)
        return results[:5]

    def _relevance_score(self, benchmark: IndustryBenchmark, text: str) -> float:
        if not benchmark.keywords:
            return 0.5
        hits = sum(1 for kw in benchmark.keywords if kw.lower() in text)
        return min(hits / max(len(benchmark.keywords) * 0.4, 1), 1.0)
