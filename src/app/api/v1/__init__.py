from fastapi import APIRouter

from app.api.v1.bot import router as bot_router
from app.api.v1.healthz import router as healthz_router
from app.api.v1.link import router as link_router
from app.api.v1.plant import router as plant_router
from app.api.v1.user import router as user_router
from config import config

v1_router = APIRouter(prefix='/api/v1')
v1_router.include_router(
    bot_router,
    prefix='/bot',
    tags=[config.service.tag_metadata_bot['name']],
)
v1_router.include_router(
    plant_router,
    prefix='/plants',
    tags=[config.service.tag_metadata_plant['name']],
)
v1_router.include_router(
    healthz_router,
    tags=[config.service.tag_metadata_health['name']],
)
v1_router.include_router(
    user_router,
    prefix='/users',
    tags=[config.service.tag_metadata_user['name']],
)
v1_router.include_router(
    link_router,
    prefix='/link',
    tags=[config.service.tag_metadata_link['name']],
)
