import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


async def with_retry[T](
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable: Callable[[Exception], bool] | None = None,
) -> T:
    """Execute an async callable with exponential backoff retry."""
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc
            if attempt >= max_retries:
                break
            if retryable and not retryable(exc):
                break
            delay = base_delay * (2**attempt)
            logger.warning(
                "Retry %d/%d after %.1fs: %s",
                attempt + 1,
                max_retries,
                delay,
                exc,
            )
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
