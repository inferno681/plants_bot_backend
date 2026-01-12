from logging import getLogger

from fastapi import Depends

from app.log_messages import USER_SERVICE_START_LOG
from app.security import oauth2_dependency
from app.services.token import SID, SUB, token_service


class UserService:
    """User service."""

    def __init__(self):
        """User service initialization."""
        self.log = getLogger(__name__)
        self.log.info(USER_SERVICE_START_LOG)


user_service = UserService()


async def get_current_user_uid_sid(token: str = oauth2_dependency) -> tuple:
    """Get current user DI."""
    payload = await token_service.check_token(token)
    return payload[SUB], payload[SID]


async def get_current_user_id(token: str = oauth2_dependency) -> str:
    """Get current user DI."""
    return (await token_service.check_token(token))[SUB]


current_user_uid_sid_dependency = Depends(get_current_user_uid_sid)
current_user_id_dependency = Depends(get_current_user_id)
