from fastapi import APIRouter

from app.api.auth.bot import router as bot_router
from app.api.auth.telegram import router as telegram_router
from app.api.auth.web import router as web_router
from config import config

auth_router = APIRouter(prefix='/auth')

auth_router.include_router(
    web_router,
    prefix='/web',
    tags=[config.service.tag_metadata_auth_web['name']],
)
auth_router.include_router(
    telegram_router,
    prefix='/telegram',
    tags=[config.service.tag_metadata_auth_telegram['name']],
)
auth_router.include_router(
    bot_router,
    prefix='/bot',
    tags=[config.service.tag_metadata_auth_bot['name']],
)
