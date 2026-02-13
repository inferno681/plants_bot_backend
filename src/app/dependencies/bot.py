from typing import Annotated

from fastapi import Depends

from app.security import oauth2_dependency
from app.services import BotService, get_bot_service


async def get_bot_id(
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    token: str = oauth2_dependency,
) -> str:
    """Get bot id."""
    return await bot_service.check_bot_permission(token)


get_bot_id_dep = Depends(get_bot_id)
