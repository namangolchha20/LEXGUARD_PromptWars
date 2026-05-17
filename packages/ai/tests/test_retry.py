import pytest
from lexguard_ai.exceptions import GeminiError
from lexguard_ai.retry import with_retry


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt() -> None:
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise GeminiError("503 unavailable")
        return "ok"

    result = await with_retry(flaky, max_retries=3, base_delay=0.01)
    assert result == "ok"
    assert attempts == 2


@pytest.mark.asyncio
async def test_retry_exhausts_and_raises() -> None:
    async def always_fail() -> str:
        raise GeminiError("500 error")

    with pytest.raises(GeminiError):
        await with_retry(always_fail, max_retries=2, base_delay=0.01)
