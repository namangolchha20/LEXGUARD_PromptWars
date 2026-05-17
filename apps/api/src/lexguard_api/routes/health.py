from fastapi import APIRouter
from lexguard_shared.schemas.health import HealthResponse

from lexguard_api import __version__

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(service="lexguard-api", version=__version__)
