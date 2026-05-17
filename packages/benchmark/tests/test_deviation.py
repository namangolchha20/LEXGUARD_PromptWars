from lexguard_benchmark.analysis.deviation import compute_deviation
from lexguard_benchmark.retrieval.retriever import IndustryBenchmark


def test_notice_period_180_days_is_high_deviation() -> None:
    benchmark = IndustryBenchmark(
        id="term_notice_period",
        clause_types=["termination"],
        metric="notice_period_days",
        label="Termination notice period",
        typical_min=30,
        typical_max=60,
        unit="days",
        description="Notice period",
        keywords=["notice"],
    )
    deviation = compute_deviation(180.0, benchmark)
    assert deviation > 50


def test_within_range_zero_deviation() -> None:
    benchmark = IndustryBenchmark(
        id="term_notice_period",
        clause_types=["termination"],
        metric="notice_period_days",
        label="Termination notice period",
        typical_min=30,
        typical_max=60,
        unit="days",
        description="Notice period",
        keywords=["notice"],
    )
    assert compute_deviation(45.0, benchmark) == 0.0
