from lexguard_benchmark.matching.extractor import extract_numeric


def test_extract_180_day_notice() -> None:
    text = "Either party may terminate with one hundred eighty (180) days written notice."
    value = extract_numeric(text, "notice_period_days", "days")
    assert value == 180.0


def test_extract_net_30_payment() -> None:
    text = "Invoices are payable net 30 days from receipt."
    value = extract_numeric(text, "payment_net_days", "days")
    assert value == 30.0
