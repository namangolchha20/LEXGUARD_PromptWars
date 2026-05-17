import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from lexguard_shared.schemas.document import IngestionStatus

from lexguard_ingestion.config import IngestionSettings
from lexguard_ingestion.models import DocumentFormat
from lexguard_ingestion.pipeline import IngestionPipeline
from lexguard_ingestion.storage import DocumentStorage

logger = logging.getLogger(__name__)


@dataclass
class IngestionJob:
    document_id: str
    file_path: Path
    format: DocumentFormat


class IngestionJobQueue:
    """Async job queue with bounded concurrency for document processing."""

    def __init__(
        self,
        pipeline: IngestionPipeline,
        storage: DocumentStorage,
        settings: IngestionSettings,
    ) -> None:
        self._pipeline = pipeline
        self._storage = storage
        self._settings = settings
        self._queue: asyncio.Queue[IngestionJob | None] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        concurrency = self._settings.ingestion_worker_concurrency
        self._workers = [
            asyncio.create_task(self._worker(i), name=f"ingestion-worker-{i}")
            for i in range(concurrency)
        ]
        logger.info("Started %d ingestion workers", concurrency)

    async def stop(self) -> None:
        if not self._running:
            return
        for _ in self._workers:
            await self._queue.put(None)
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._running = False
        logger.info("Stopped ingestion workers")

    async def enqueue(self, job: IngestionJob) -> None:
        await self._storage.update_status(job.document_id, IngestionStatus.PENDING)
        await self._queue.put(job)
        logger.info("Enqueued ingestion job %s", job.document_id)

    async def _worker(self, worker_id: int) -> None:
        while True:
            job = await self._queue.get()
            try:
                if job is None:
                    break
                await self._process_job(job, worker_id)
            finally:
                self._queue.task_done()

    async def _process_job(self, job: IngestionJob, worker_id: int) -> None:
        logger.info("Worker %d processing document %s", worker_id, job.document_id)
        await self._storage.update_status(job.document_id, IngestionStatus.PROCESSING)

        try:
            result = await self._pipeline.process(
                document_id=job.document_id,
                file_path=job.file_path,
                doc_format=job.format,
            )
            await self._storage.save_result(result)
            await self._storage.update_status(
                job.document_id,
                IngestionStatus.COMPLETED,
                result=result,
            )
            logger.info("Completed ingestion for %s", job.document_id)
        except Exception as exc:
            logger.exception("Ingestion failed for %s", job.document_id)
            await self._storage.update_status(
                job.document_id,
                IngestionStatus.FAILED,
                error=str(exc),
            )
        finally:
            if job.file_path.exists():
                job.file_path.unlink(missing_ok=True)
