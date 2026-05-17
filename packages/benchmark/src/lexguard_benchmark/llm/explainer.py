import logging

from lexguard_ai import AIClient, AISettings
from lexguard_shared.schemas.benchmark import FairnessLevel
from lexguard_shared.schemas.clause import ExtractedClause

from lexguard_benchmark.llm.models import BenchmarkExplanationResponse
from lexguard_benchmark.llm.prompts import BENCHMARK_SYSTEM, BENCHMARK_USER
from lexguard_benchmark.matching.extractor import format_range
from lexguard_benchmark.retrieval.retriever import IndustryBenchmark

logger = logging.getLogger(__name__)


class BenchmarkExplainer:
    """LLM-powered comparative explanations and negotiation advice."""

    def __init__(self, ai_client: AIClient | None = None, settings: AISettings | None = None) -> None:
        self._ai = ai_client or AIClient(settings)

    async def explain(
        self,
        clause: ExtractedClause,
        benchmark: IndustryBenchmark,
        contract_value_str: str,
        deviation_score: float,
        rule_fairness: FairnessLevel,
        benchmark_range: str,
    ) -> BenchmarkExplanationResponse:
        prompt = BENCHMARK_USER.format(
            title=clause.title,
            clause_type=clause.clause_type.value,
            text=clause.text,
            metric=benchmark.metric,
            label=benchmark.label,
            benchmark_range=benchmark_range,
            contract_value=contract_value_str,
            deviation_score=deviation_score,
            rule_fairness=rule_fairness.value,
        )
        return await self._ai.gemini.generate_structured(
            prompt=prompt,
            response_model=BenchmarkExplanationResponse,
            system_instruction=BENCHMARK_SYSTEM,
        )

    def fallback_explanation(
        self,
        clause: ExtractedClause,
        benchmark: IndustryBenchmark,
        contract_value_str: str,
        deviation_score: float,
        rule_fairness: FairnessLevel,
        benchmark_range: str,
    ) -> BenchmarkExplanationResponse:
        bench_range = format_range(benchmark)
        if deviation_score < 15:
            explanation = (
                f"The {benchmark.label} in '{clause.title}' ({contract_value_str}) "
                f"falls within the typical industry range of {bench_range}."
            )
            recommendation = "No change needed — term aligns with market standards."
        elif rule_fairness == FairnessLevel.UNFAVORABLE:
            explanation = (
                f"The {benchmark.label} is {contract_value_str}, compared to industry "
                f"standard of {bench_range}. This is significantly outside the norm "
                f"(deviation: {deviation_score:.0f}/100)."
            )
            recommendation = (
                f"Negotiate to bring {benchmark.label} within {bench_range}. "
                f"Request a cap, shorter duration, or mutual obligations."
            )
        else:
            explanation = (
                f"'{clause.title}' shows {benchmark.label} of {contract_value_str} vs "
                f"industry {bench_range} (deviation {deviation_score:.0f}/100)."
            )
            recommendation = "Review with counsel; consider requesting alignment with industry norms."

        return BenchmarkExplanationResponse(
            benchmark_summary=f"Industry standard for {benchmark.label}: {bench_range}",
            comparative_explanation=explanation,
            negotiation_recommendation=recommendation,
            fairness_assessment=rule_fairness,
            contract_value=contract_value_str,
        )
