from lexguard_benchmark.retrieval.retriever import IndustryBenchmark


def compute_deviation(
    contract_value: float | None,
    benchmark: IndustryBenchmark,
) -> float:
    """Return deviation score 0-100 (higher = further from industry norm)."""
    if benchmark.unit == "qualitative":
        return 0.0

    if benchmark.unit == "boolean":
        if contract_value and contract_value >= 1.0:
            return 85.0
        return 0.0

    if contract_value is None:
        return 30.0

    min_v = benchmark.typical_min
    max_v = benchmark.typical_max
    if min_v is None or max_v is None:
        return 25.0

    if min_v <= contract_value <= max_v:
        return 0.0

    if contract_value < min_v:
        gap = min_v - contract_value
        span = max(max_v - min_v, 1)
        return min(100.0, round((gap / span) * 60, 2))

    gap = contract_value - max_v
    span = max(max_v - min_v, 1)
    ratio = gap / span
    return min(100.0, round(30 + ratio * 70, 2))
