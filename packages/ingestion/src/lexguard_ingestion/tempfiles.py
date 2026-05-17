import asyncio
import logging
import shutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import aiofiles

logger = logging.getLogger(__name__)


@asynccontextmanager
async def temp_upload(
    temp_dir: Path,
    filename: str,
    content: bytes,
) -> AsyncIterator[Path]:
    """Write upload to a temp file and guarantee cleanup on exit."""
    await asyncio.to_thread(temp_dir.mkdir, parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower()
    temp_path = temp_dir / f"{uuid4().hex}{suffix}"

    try:
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)
        yield temp_path
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
            logger.debug("Cleaned up temp file %s", temp_path)


def cleanup_temp_dir(temp_dir: Path) -> None:
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info("Cleaned up temp directory %s", temp_dir)
