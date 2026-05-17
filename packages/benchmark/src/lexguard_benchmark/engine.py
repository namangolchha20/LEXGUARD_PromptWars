import asyncio
import logging

from lexguard_ai import AIClient, AISettings
from lexguard_shared.schemas.benchmark import (
    BenchmarkComparison,
    DocumentBenchmarkResult,
    FairnessLevel,
)
from lexguard_shared.schemas.clause import ClauseExtractionResult, ExtractedClause

from lexguard_benchmark.analysis.deviation import compute_deviation
from lexguard_benchmark.analysis.fairness import assess_fairness
from lexguard_benchmark.analysis.outlier import is_outlier
from lexguard_benchmark.config import BenchmarkSettings
from lexguard_benchmark.llm.explainer import BenchmarkExplainer
from lexguard_benchmark.matching.extractor import extract_numeric, format_range
from lexguard_benchmark.matching.semantic import semantic_similarity
from lexguard_benchmark.retrieval.retriever import BenchmarkRetriever, IndustryBenchmark

logger = logging.getLogger(__name__)


class BenchmarkComparisonEngine:
    """Compares contract clauses against industry-standard benchmarks."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        settings: BenchmarkSettings | None = None,
        ai_settings: AISettings | None = None,
    ) -> None:
        self._settings = settings or BenchmarkSettings()
        self._retriever = BenchmarkRetriever(self._settings.benchmark_data_path)
        self._explainer = BenchmarkExplainer(ai_client, ai_settings)
        self._semaphore = asyncio.Semaphore((ai_settings or AISettings()).gemini_max_concurrency)

    async def compare(self, clauses: ClauseExtractionResult) -> DocumentBenchmarkResult:
        logger.info(
            "Benchmarking %d clauses for document %s",
            len(clauses.clauses),
            clauses.document_id,
        )

        tasks = [self._compare_clause(clause) for clause in clauses.clauses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        comparisons: list[BenchmarkComparison] = []
        for clause, result in zip(clauses.clauses, results, strict=True):
            if isinstance(result, Exception):
                logger.error("Benchmark failed for clause %s: %s", clause.clause_id, result)
                continue
            comparisons.extend(result)

        comparisons.sort(key=lambda c: -c.deviation_score)
        outliers = [c for c in comparisons if c.is_outlier]

        overall_deviation = (
            round(sum(c.deviation_score for c in comparisons) / len(comparisons), 2)
            if comparisons
            else 0.0
        )
        overall_fairness = self._overall_fairness(comparisons)

        return DocumentBenchmarkResult(
            document_id=clauses.document_id,
            benchmark_summary=self._document_summary(comparisons, outliers, overall_deviation),
            overall_deviation_score=overall_deviation,
            overall_fairness=overall_fairness,
            comparisons=comparisons,
            outlier_count=len(outliers),
        )

    async def _compare_clause(self, clause: ExtractedClause) -> list[BenchmarkComparison]:
        benchmarks = self._retriever.retrieve_for_clause(clause)
        if not benchmarks:
            return []

        comparisons: list[BenchmarkComparison] = []
        for benchmark in benchmarks:
            similarity = semantic_similarity(f"{clause.title} {clause.text}", benchmark)
            if similarity < self._settings.benchmark_similarity_threshold:
                continue

            comparison = await self._compare_metric(clause, benchmark, similarity)
            if comparison:
                comparisons.append(comparison)

        return comparisons

    async def _compare_metric(
        self,
        clause: ExtractedClause,
        benchmark: IndustryBenchmark,
        similarity: float,
    ) -> BenchmarkComparison | None:
        numeric = extract_numeric(clause.text, benchmark.metric, benchmark.unit)
        contract_value_str = self._format_contract_value(numeric, benchmark, clause.text)
        deviation = compute_deviation(numeric, benchmark)

        if benchmark.unit == "qualitative":
            deviation = max(deviation, 40.0) if any(
                t.lower() in clause.text.lower() for t in benchmark.qualitative_unfair
            ) else deviation

        fairness = assess_fairness(numeric, benchmark, deviation, clause.text)
        benchmark_range = format_range(benchmark)
        outlier = is_outlier(deviation, self._settings.benchmark_outlier_threshold)

        if deviation >= 20 or outlier:
            async with self._semaphore:
                try:
                    explanation = await self._explainer.explain(
                        clause,
                        benchmark,
                        contract_value_str,
                        deviation,
                        fairness,
                        benchmark_range,
                    )
                except Exception as exc:
                    logger.warning("LLM benchmark explain failed: %s", exc)
                    explanation = self._explainer.fallback_explanation(
                        clause,
                        benchmark,
                        contract_value_str,
                        deviation,
                        fairness,
                        benchmark_range,
                    )
        else:
            explanation = self._explainer.fallback_explanation(
                clause,
                benchmark,
                contract_value_str,
                deviation,
                fairness,
                benchmark_range,
            )

        return BenchmarkComparison(
            clause_id=clause.clause_id,
            clause_title=clause.title,
            metric=benchmark.metric,
            benchmark_summary=explanation.benchmark_summary,
            contract_value=explanation.contract_value,
            benchmark_range=benchmark_range,
            deviation_score=deviation,
            fairness_assessment=explanation.fairness_assessment,
            is_outlier=outlier,
            similarity_score=similarity,
            comparative_explanation=explanation.comparative_explanation,
            negotiation_recommendation=explanation.negotiation_recommendation,
        )

    def _format_contract_value(
        self,
        numeric: float | None,
        benchmark: IndustryBenchmark,
        text: str,
    ) -> str:
        if benchmark.unit == "boolean":
            return "present" if numeric and numeric >= 1.0 else "not detected"
        if benchmark.unit == "qualitative":
            for term in benchmark.qualitative_unfair:
                if term.lower() in text.lower():
                    return term
            for term in benchmark.qualitative_fair:
                if term.lower() in text.lower():
                    return term
            return "see clause text"
        if numeric is not None:
            if benchmark.unit == "days":
                return f"{numeric:g} days"
            if benchmark.unit == "months":
                return f"{numeric / 30:g} months" if benchmark.metric != "payment_net_days" else f"{numeric:g} days"
            if benchmark.unit == "years":
                return f"{numeric / 365:g} years"
            return f"{numeric:g} {benchmark.unit}"
        return "not specified"

    def _overall_fairness(self, comparisons: list[BenchmarkComparison]) -> FairnessLevel:
        if not comparisons:
            return FairnessLevel.NEUTRAL
        unfavorable = sum(1 for c in comparisons if c.fairness_assessment == FairnessLevel.UNFAVORABLE)
        favorable = sum(1 for c in comparisons if c.fairness_assessment == FairnessLevel.FAVORABLE)
        if unfavorable > favorable and unfavorable >= 2:
            return FairnessLevel.UNFAVORABLE
        if favorable > unfavorable:
            return FairnessLevel.FAVORABLE
        return FairnessLevel.NEUTRAL

    def _document_summary(
        self,
        comparisons: list[BenchmarkComparison],
        outliers: list[BenchmarkComparison],
        overall_deviation: float,
    ) -> str:
        if not comparisons:
            return "No benchmark comparisons could be generated for this document."

        top = comparisons[0]
        return (
            f"Compared {len(comparisons)} clause metrics against industry benchmarks. "
            f"Overall deviation: {overall_deviation:.0f}/100. "
            f"{len(outliers)} outlier(s) detected. "
            f"Largest gap: {top.metric} in '{top.clause_title}' "
            f"({top.contract_value} vs {top.benchmark_range})."
        )
