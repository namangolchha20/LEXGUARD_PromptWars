import asyncio
import contextlib
import logging
import signal

from lexguard_analyze_worker.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

_shutdown = asyncio.Event()


def _handle_signal() -> None:
    logger.info("Shutdown signal received")
    _shutdown.set()


async def run_worker() -> None:
    logger.info(
        "Analyze worker started (env=%s, concurrency=%d)",
        settings.app_env,
        settings.analyze_worker_concurrency,
    )
    await _shutdown.wait()
    logger.info("Analyze worker stopped")


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _handle_signal)

    try:
        loop.run_until_complete(run_worker())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
