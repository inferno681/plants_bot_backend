from fastapi import APIRouter

from app.schemes import (
    ClientInfo,
    InitData,
    RefreshRequest,
    Tokens,
    UserSession,
)
from app.services import bot_auth_service, current_user_uid_sid_dependency
from app.utils import client_info_dependency

router = APIRouter()


@router.post('/login', response_model=Tokens)
async def login(
    init_data: InitData, client_info: ClientInfo = client_info_dependency
):
    """Login endpoint."""
    return await bot_auth_service.bot_login(init_data.init_data, client_info)


@router.post('/logout')
async def logout(session_info: UserSession = current_user_uid_sid_dependency):
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
):
    """Token refresh endpoint."""
    return await bot_auth_service.refresh_user_tokens(
        refresh_token.refresh_token, client_info
    )
