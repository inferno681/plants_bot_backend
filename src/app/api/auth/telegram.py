from fastapi import APIRouter
from pymongo.asynchronous.client_session import AsyncClientSession

from app.dependencies import (
    current_user_id_dep,
    current_user_uid_sid_dep,
    session_dependency,
    telegram_auth_service_dep,
)
from app.schemes import (
    ClientInfo,
    InitData,
    RefreshRequest,
    TelegramAccountBase,
    TelegramUser,
    Tokens,
    UserSession,
)
from app.services import TelegramAuthService
from app.utils import client_info_dependency

router = APIRouter()


@router.post('/registration', response_model=TelegramUser)
async def telegram_user_registration(
    user_data: TelegramAccountBase,
    session: AsyncClientSession = session_dependency,
    telegram_auth_service: TelegramAuthService = telegram_auth_service_dep,
):
    """Telegram user registration (Bot action)"""
    return await telegram_auth_service.registration_telegram_user(
        user_data, session
    )


@router.post('/login', response_model=Tokens)
async def login(
    init: InitData,
    client_info: ClientInfo = client_info_dependency,
    session: AsyncClientSession = session_dependency,
    telegram_auth_service: TelegramAuthService = telegram_auth_service_dep,
):
    """Login endpoint."""
    return await telegram_auth_service.login_telegram_user(
        init.init_data, client_info, session
    )


@router.post('/logout')
async def logout(
    session_info: UserSession = current_user_uid_sid_dep,
    telegram_auth_service: TelegramAuthService = telegram_auth_service_dep,
):
    """Current session logout."""
    return {
        'message': await telegram_auth_service.logout_user(
            session_info.uid, session_info.sid
        )
    }


@router.post('/logout_others')
async def logout_other(
    session_info: UserSession = current_user_uid_sid_dep,
    telegram_auth_service: TelegramAuthService = telegram_auth_service_dep,
):
    """Other session logout."""
    return {
        'message': await telegram_auth_service.logout_others_sessions(
            session_info.uid, session_info.sid
        )
    }


@router.post('/logout_all')
async def logout_all(
    user_id: str = current_user_id_dep,
    telegram_auth_service: TelegramAuthService = telegram_auth_service_dep,
):
    """All session logout."""
    return {
        'message': await telegram_auth_service.logout_all_sessions(user_id)
    }


@router.post('/refresh', response_model=Tokens)
async def refresh_tokens(
    refresh_token: RefreshRequest,
    client_info: ClientInfo = client_info_dependency,
    telegram_auth_service: TelegramAuthService = telegram_auth_service_dep,
):
    """Refresh tokens endpoint."""
    return await telegram_auth_service.refresh_user_tokens(
        refresh_token.refresh_token, client_info
    )
