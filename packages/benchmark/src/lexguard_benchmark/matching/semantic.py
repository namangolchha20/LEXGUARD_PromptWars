import re
from difflib import SequenceMatcher

from lexguard_benchmark.retrieval.retriever import IndustryBenchmark


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) > 2}


def semantic_similarity(clause_text: str, benchmark: IndustryBenchmark) -> float:
    """Lightweight semantic similarity via token overlap + sequence matching."""
    clause_tokens = tokenize(clause_text)
    bench_text = f"{benchmark.label} {benchmark.description} {' '.join(benchmark.keywords)}"
    bench_tokens = tokenize(bench_text)

    if not clause_tokens or not bench_tokens:
        return 0.0

    overlap = len(clause_tokens & bench_tokens) / len(clause_tokens | bench_tokens)
    sequence = SequenceMatcher(None, clause_text.lower()[:500], bench_text.lower()).ratio()
    keyword_hits = sum(1 for kw in benchmark.keywords if kw.lower() in clause_text.lower())
    keyword_score = min(keyword_hits / max(len(benchmark.keywords), 1), 1.0)

    return round(0.4 * overlap + 0.3 * sequence + 0.3 * keyword_score, 3)
