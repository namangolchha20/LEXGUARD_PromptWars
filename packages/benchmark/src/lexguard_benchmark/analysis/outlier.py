def is_outlier(deviation_score: float, threshold: float = 50.0) -> bool:
    return deviation_score >= threshold
