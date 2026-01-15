from fastapi import APIRouter

from app.api.v1.healthz import router as healthz_router
from app.api.v1.plant import router as plant_router
from config import config

v1_router = APIRouter(prefix='/api/v1')
v1_router.include_router(
    plant_router,
    prefix='/plants',
    tags=[config.service.tag_metadata_plant['name']],
)
v1_router.include_router(
    healthz_router,
    prefix='healthz',
    tags=[config.service.tag_metadata_health['name']],
)
