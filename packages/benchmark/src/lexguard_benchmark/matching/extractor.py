import re

_DURATION_PATTERNS = [
    (re.compile(r"\(\s*(\d+)\s*\)\s*days?", re.I), lambda m: int(m.group(1))),
    (re.compile(r"(\d+)\s*\(\s*(\d+)\s*\)\s*days?", re.I), lambda m: int(m.group(2))),
    (re.compile(r"(\d+)\s*days?", re.I), lambda m: int(m.group(1))),
    (re.compile(r"(\d+)\s*months?", re.I), lambda m: int(m.group(1)) * 30),
    (re.compile(r"(\d+)\s*years?", re.I), lambda m: int(m.group(1)) * 365),
    (re.compile(r"(\d+)\s*weeks?", re.I), lambda m: int(m.group(1)) * 7),
]

_NET_PAYMENT = re.compile(r"net\s*(\d+)|payable\s+within\s+(\d+)\s*days", re.I)
_LIABILITY_CAP = re.compile(r"(\d+)\s*months?\s+of\s+fees", re.I)


def extract_numeric(text: str, metric: str, unit: str) -> float | None:
    text_lower = text.lower()

    if unit == "boolean":
        if metric == "uncapped_liability":
            triggers = ("unlimited", "uncapped", "without limitation", "consequential damages")
            return 1.0 if any(t in text_lower for t in triggers) else 0.0
        if metric == "mandatory_arbitration":
            triggers = ("binding arbitration", "class action waiver", "waive.*jury")
            return 1.0 if any(t in text_lower for t in triggers) else 0.0
        return None

    if unit == "qualitative":
        return None

    if metric == "payment_net_days":
        match = _NET_PAYMENT.search(text_lower)
        if match:
            return float(match.group(1) or match.group(2))
        return None

    if metric == "liability_cap_months":
        match = _LIABILITY_CAP.search(text_lower)
        if match:
            return float(match.group(1))
        return None

    if unit == "days":
        return _extract_days(text_lower)
    if unit == "months":
        days = _extract_days(text_lower)
        return days / 30 if days else None
    if unit == "years":
        days = _extract_days(text_lower)
        return days / 365 if days else None

    return _extract_days(text_lower)


def _extract_days(text: str) -> float | None:
    values: list[float] = []
    for pattern, converter in _DURATION_PATTERNS:
        for match in pattern.finditer(text):
            try:
                values.append(float(converter(match)))
            except (ValueError, IndexError):
                continue
    return max(values) if values else None


def format_range(benchmark) -> str:
    if benchmark.unit == "qualitative":
        fair = ", ".join(benchmark.qualitative_fair[:3]) or "narrow scope"
        return f"Typical: {fair}"
    if benchmark.unit == "boolean":
        return "Industry standard: limited or capped exposure"
    if benchmark.typical_min is not None and benchmark.typical_max is not None:
        return f"{benchmark.typical_min:g}–{benchmark.typical_max:g} {benchmark.unit}"
    return "Industry standard varies"
