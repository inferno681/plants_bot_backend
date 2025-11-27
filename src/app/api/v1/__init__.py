from fastapi import APIRouter

from app.api.v1.plant import router as plant_router
from config import config

v1_router = APIRouter(prefix='/api/v1')
v1_router.include_router(
    plant_router,
    prefix='/plants',
    tags=[config.service.tag_metadata_plant['name']],
)
