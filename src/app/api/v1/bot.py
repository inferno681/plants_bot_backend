from fastapi import APIRouter
from pymongo.asynchronous.client_session import AsyncClientSession

from app.constants import LinkMessage
from app.dependencies import (
    get_bot_id_dep,
    link_service_dep,
    link_telegram_deps,
    plant_service_dep,
    session_dependency,
    telegram_auth_service_dep,
)
from app.schemes import (
    MessageScheme,
    PlantBotCreateScheme,
    PlantBotUpdateScheme,
    PlantReadScheme,
    TelegramAccountBase,
    TelegramLinkRequest,
    TelegramUser,
)
from app.services import (
    LinkService,
    PlantService,
    TelegramAuthService,
    WebAuthService,
)

router = APIRouter()


@router.post('/registration', response_model=TelegramUser)
async def user_registration_via_bot(
    account_data: TelegramAccountBase,
    telegram_auth_service: TelegramAuthService = telegram_auth_service_dep,
    session: AsyncClientSession = session_dependency,
    bot_id: str = get_bot_id_dep,
):
    """User registration via bot endpoint."""
    return await telegram_auth_service.registration_telegram_user(
        account_data=account_data, session=session
    )


@router.post('/add_plant', response_model=PlantReadScheme)
async def add_plant_via_bot(
    plant_data: PlantBotCreateScheme,
    plant_service: PlantService = plant_service_dep,
    bot_id: str = get_bot_id_dep,
):
    """Add plant via bot endpoint."""
    return await plant_service.add_plant(
        user_id=plant_data.user_id,
        plant_data=plant_data,
    )


@router.patch('/update_plant', response_model=PlantReadScheme)
async def update_plant_via_bot(
    plant_update: PlantBotUpdateScheme,
    plant_service: PlantService = plant_service_dep,
    bot_id: str = get_bot_id_dep,
):
    """Update plant via bot endpoint."""
    return await plant_service.update_plant(
        plant_id=plant_update.plant_id,
        user_id=plant_update.user_id,
        plant_update=plant_update,
    )


@router.patch('/link_telegram', response_model=MessageScheme)
async def link_telegram(
    link_request: TelegramLinkRequest,
    link_service: LinkService = link_service_dep,
    deps: tuple[PlantService, WebAuthService, AsyncClientSession] = (
        link_telegram_deps
    ),
    bot_id: str = get_bot_id_dep,
):
    """Link telegram account endpoint."""
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
    return {'message': LinkMessage.user_link}
