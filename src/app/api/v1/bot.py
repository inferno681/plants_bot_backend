from fastapi import APIRouter, status
from pymongo.asynchronous.client_session import AsyncClientSession

from app.dependencies import (
    get_bot_id_dep,
    link_service_dep,
    link_telegram_deps,
)
from app.schemes import TelegramLinkRequest
from app.services import LinkService, PlantService, WebAuthService

router = APIRouter()


@router.patch('/link_telegram', status_code=status.HTTP_204_NO_CONTENT)
async def link_telegram(
    link_request: TelegramLinkRequest,
    link_service: LinkService = link_service_dep,
    deps: tuple[PlantService, WebAuthService, AsyncClientSession] = (
        link_telegram_deps
    ),
    bot_id: str = get_bot_id_dep,
):
    plant_service, web_auth_service, session = deps
    old_id, new_id = await link_service.link_telegram(
        code=link_request.code,
        telegram_id=link_request.telegram_id,
        session=session,
    )
    if old_id:
        await plant_service.plant_migration(
            old_user=old_id, new_user=new_id, session=session
        )
        await web_auth_service.logout_all_sessions(str(old_id))
    await link_service.clear_link_code(str(new_id), link_request.code)
