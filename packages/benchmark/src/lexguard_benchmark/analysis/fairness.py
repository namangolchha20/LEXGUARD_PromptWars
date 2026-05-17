from lexguard_shared.schemas.benchmark import FairnessLevel

from lexguard_benchmark.retrieval.retriever import IndustryBenchmark


def assess_fairness(
    contract_value: float | None,
    benchmark: IndustryBenchmark,
    deviation_score: float,
    clause_text: str,
) -> FairnessLevel:
    if benchmark.unit == "qualitative":
        return _qualitative_fairness(benchmark, clause_text, deviation_score)

    if benchmark.unit == "boolean":
        if contract_value and contract_value >= 1.0:
            return FairnessLevel.UNFAVORABLE
        return FairnessLevel.NEUTRAL

    if deviation_score < 15:
        return FairnessLevel.NEUTRAL
    if deviation_score < 35:
        return FairnessLevel.NEUTRAL

    if contract_value is None:
        return FairnessLevel.UNFAVORABLE if deviation_score > 40 else FairnessLevel.NEUTRAL

    min_v = benchmark.typical_min
    max_v = benchmark.typical_max
    if min_v is None or max_v is None:
        return FairnessLevel.NEUTRAL

    if contract_value > max_v:
        return FairnessLevel.UNFAVORABLE
    if contract_value < min_v:
        return FairnessLevel.FAVORABLE

    return FairnessLevel.NEUTRAL


def _qualitative_fairness(
    benchmark: IndustryBenchmark,
    text: str,
    deviation_score: float,
) -> FairnessLevel:
    text_lower = text.lower()
    unfair_hits = sum(1 for t in benchmark.qualitative_unfair if t.lower() in text_lower)
    fair_hits = sum(1 for t in benchmark.qualitative_fair if t.lower() in text_lower)

    if unfair_hits > fair_hits:
        return FairnessLevel.UNFAVORABLE
    if fair_hits > 0 and unfair_hits == 0:
        return FairnessLevel.FAVORABLE
    if deviation_score > 40:
        return FairnessLevel.UNFAVORABLE
    return FairnessLevel.NEUTRAL
