from logging import getLogger

from fastapi import Depends

from app.log_messages import USER_SERVICE_START_LOG
from app.security import oauth2_scheme
from app.services.auth import auth_service


class UserService:
    """User service."""

    def __init__(self):
        """User service initialization."""
        self.log = getLogger(__name__)
        self.log.info(USER_SERVICE_START_LOG)

    async def get_current_user_id(
        self, token: str = Depends(oauth2_scheme)
    ) -> int:
        """Get current user method."""
        return await auth_service.token_service.check_token(token)


user_service = UserService()
