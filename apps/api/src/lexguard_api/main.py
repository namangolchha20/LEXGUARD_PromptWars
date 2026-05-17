import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lexguard_api import __version__
from lexguard_api.config import settings
from lexguard_api.dependencies import get_job_queue
from lexguard_api.middleware.private_network import PrivateNetworkAccessMiddleware
from lexguard_api.routes import (
    benchmarks,
    clauses,
    consequences,
    documents,
    health,
    orchestrator,
    orchestrator_ws,
    risk,
    websocket,
)

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s API (env=%s)", settings.app_name, settings.app_env)
    queue = get_job_queue()
    await queue.start()
    yield
    await queue.stop()
    logger.info("Shutting down %s API", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title="LEXGUARD API",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(PrivateNetworkAccessMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(websocket.router, tags=["websocket"])
    app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
    app.include_router(clauses.router, prefix="/api/v1", tags=["clauses"])
    app.include_router(risk.router, prefix="/api/v1", tags=["risk"])
    app.include_router(consequences.router, prefix="/api/v1", tags=["consequences"])
    app.include_router(benchmarks.router, prefix="/api/v1", tags=["benchmarks"])
    app.include_router(orchestrator.router, prefix="/api/v1", tags=["orchestrator"])
    app.include_router(orchestrator_ws.router, tags=["orchestrator"])

    return app


app = create_app()


def run() -> None:
    uvicorn.run(
        "lexguard_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    run()
