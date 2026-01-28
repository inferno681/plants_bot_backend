from beanie import PydanticObjectId
from fastapi import APIRouter

from app.dependencies import (
    current_user_id_dep,
    link_service_dep,
    web_auth_service_dep,
)
from app.schemes import TelegramLink
from app.services import LinkService, LoginType, WebAuthService

router = APIRouter()


@router.post('', response_model=TelegramLink)
async def get_telegram_link(
    user_id: str = current_user_id_dep,
    link_service: LinkService = link_service_dep,
):
    """Get user info endpoint."""
    return await link_service.create_telegram_link(user_id=user_id)


@router.delete('')
async def delete_telegram_link(
    user_id: str = current_user_id_dep,
    link_service: LinkService = link_service_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Delete telegram link endpoint."""
    message = await link_service.delete_telegram_link(
        user_id=PydanticObjectId(user_id)
    )
    await web_auth_service.token_service.delete_sessions_by_type(
        user_id, LoginType.telegram
    )
    return message
