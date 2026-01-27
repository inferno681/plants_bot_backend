from beanie import PydanticObjectId
from fastapi import APIRouter, status
from pymongo.asynchronous.client_session import AsyncClientSession

from app.dependencies import (
    current_user_id_dep,
    get_bot_id_dep,
    plant_service_dep,
    session_dependency,
    user_service_dep,
    web_auth_service_dep,
)
from app.schemes import TelegramLink, TelegramLinkRequest, WebUserInfo
from app.services import PlantService, UserService, WebAuthService

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


@router.patch('/link_telegram', status_code=status.HTTP_204_NO_CONTENT)
async def link_telegram(
    link_request: TelegramLinkRequest,
    plant_service: PlantService = plant_service_dep,
    user_service: UserService = user_service_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
    session: AsyncClientSession = session_dependency,
    bot_id: str = get_bot_id_dep,
):
    old_id, new_id = await user_service.link_telegram(
        code=link_request.code,
        telegram_id=link_request.telegram_id,
        session=session,
    )
    if old_id:
        await plant_service.plant_migration(
            old_user=old_id, new_user=new_id, session=session
        )
        await web_auth_service.logout_all_sessions(str(old_id))
    await user_service.clear_link_code(str(new_id), link_request.code)
