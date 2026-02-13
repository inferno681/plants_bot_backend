from fastapi import Depends
from pymongo.asynchronous.client_session import AsyncClientSession

from app.dependencies.auth import web_auth_service_dep
from app.dependencies.db import session_dependency
from app.dependencies.plant import plant_service_dep
from app.services import PlantService, WebAuthService, get_user_service

user_service_dep = Depends(get_user_service)


async def get_link_telegram_deps(
    plant_service: PlantService = plant_service_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
    session: AsyncClientSession = session_dependency,
) -> tuple[PlantService, WebAuthService, AsyncClientSession]:
    """Get link telegram deps."""
    return plant_service, web_auth_service, session


link_telegram_deps = Depends(get_link_telegram_deps)
