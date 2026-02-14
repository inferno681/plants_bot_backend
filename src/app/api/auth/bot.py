from fastapi import APIRouter
from pymongo.asynchronous.client_session import AsyncClientSession

from app.dependencies import (
    bot_auth_service_dep,
    current_bot_uid_sid_dep,
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
from app.services import BotAuthService, TelegramAuthService
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
    init_data: InitData,
    client_info: ClientInfo = client_info_dependency,
    bot_auth_service: BotAuthService = bot_auth_service_dep,
):
    """Login endpoint."""
    return await bot_auth_service.bot_login(init_data.init_data, client_info)


@router.post('/logout')
async def logout(
    session_info: UserSession = current_bot_uid_sid_dep,
    bot_auth_service: BotAuthService = bot_auth_service_dep,
):
    """Logout endpoint."""
    return {
        'message': await bot_auth_service.logout(
            session_info.uid, session_info.sid
        )
    }


@router.post('/refresh', response_model=Tokens)
async def refresh(
    refresh_token: RefreshRequest,
    client_info: ClientInfo = client_info_dependency,
    bot_auth_service: BotAuthService = bot_auth_service_dep,
):
    """Token refresh endpoint."""
    return await bot_auth_service.refresh_user_tokens(
        refresh_token.refresh_token, client_info
    )
