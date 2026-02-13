from app.dependencies.auth import (
    bot_auth_service_dep,
    current_telegram_uid_sid_dep,
    current_user_id_dep,
    current_user_uid_sid_dep,
    current_web_uid_sid_dep,
    refresh_request_dep,
    telegram_auth_service_dep,
    web_auth_service_dep,
)
from app.dependencies.bot import get_bot_id_dep
from app.dependencies.db import session_dependency
from app.dependencies.email import email_service_dep
from app.dependencies.healthz import healthz_service_dep
from app.dependencies.link import link_service_dep
from app.dependencies.plant import (
    plant_mapper_dep,
    plant_query_dep,
    plant_service_dep,
)
from app.dependencies.user import link_telegram_deps, user_service_dep

__all__ = [
    'current_user_id_dep',
    'current_user_uid_sid_dep',
    'bot_auth_service_dep',
    'telegram_auth_service_dep',
    'web_auth_service_dep',
    'session_dependency',
    'refresh_request_dep',
    'healthz_service_dep',
    'plant_mapper_dep',
    'plant_service_dep',
    'plant_query_dep',
    'user_service_dep',
    'link_telegram_deps',
    'get_bot_id_dep',
    'link_service_dep',
    'email_service_dep',
    'current_web_uid_sid_dep',
    'current_telegram_uid_sid_dep',
]
