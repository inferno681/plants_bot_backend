from app.services.auth_bot import bot_auth_service
from app.services.auth_telegram import telegram_auth_service
from app.services.auth_web import web_auth_service
from app.services.storage import storage_service
from app.services.user import (
    current_user_id_dependency,
    current_user_uid_sid_dependency,
    user_service,
)

__all__ = [
    'web_auth_service',
    'user_service',
    'storage_service',
    'telegram_auth_service',
    'current_user_uid_sid_dependency',
    'current_user_id_dependency',
    'bot_auth_service',
]
