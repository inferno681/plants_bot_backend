from beanie import PydanticObjectId
from fastapi import APIRouter

from app.dependencies import (
    current_user_id_dep,
    user_service_dep,
    web_auth_service_dep,
)
from app.schemes import TelegramLink, WebUserInfo
from app.services import UserService, WebAuthService


router = APIRouter()


@router.get('/me', response_model=WebUserInfo)
async def get_web_user_info(
    user_id: str = current_user_id_dep,
    user_service: UserService = user_service_dep,
):
    """Get user info endpoint."""
    return await user_service.get_web_user_info(
        user_id=PydanticObjectId(user_id)
    )


@router.post('/telegram_link', response_model=TelegramLink)
async def get_telegram_link(
    user_id: str = current_user_id_dep,
    user_service: UserService = user_service_dep,
):
    """Get user info endpoint."""
    return await user_service.create_telegram_link(user_id=user_id)


@router.delete('/me')
async def delete_user(
    user_id: str = current_user_id_dep,
    user_service: UserService = user_service_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Delete user endpoint."""
    message = await user_service.delete_user(user_id=PydanticObjectId(user_id))
    await web_auth_service.logout_all_sessions(user_id)
    return message


@router.delete('/me/telegram_link')
async def delete_telegram_link(
    user_id: str = current_user_id_dep,
    user_service: UserService = user_service_dep,
):
    """Delete telegram link endpoint."""
    return await user_service.delete_telegram_link(
        user_id=PydanticObjectId(user_id)
    )
