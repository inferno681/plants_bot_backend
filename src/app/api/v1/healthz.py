from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.constants import STATUS
from app.dependencies import healthz_service_dep
from app.services import HealthService

router = APIRouter()


@router.get('/healthz', response_model=dict)
async def healthz(health_service: HealthService = healthz_service_dep):
    """Health check endpoint."""
    return health_service.health_check()


@router.get('/readyz', response_model=dict)
async def readyz(health_service: HealthService = healthz_service_dep):
    readiness = await health_service.ready_check()
    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if readiness.get(STATUS) == 'ready'
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content=readiness,
    )
