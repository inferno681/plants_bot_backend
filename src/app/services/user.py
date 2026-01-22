from logging import getLogger

from fastapi import FastAPI, Request

from app.constants.auth import SID, SUB
from app.log_messages import USER_SERVICE_START_LOG
from app.schemes import UserSession
from app.services.token import TokenService


class UserService:
    """User service."""

    def __init__(self, token_service: TokenService):
        """User service initialization."""
        self.token_service = token_service
        self.log = getLogger(__name__)
        self.log.info(USER_SERVICE_START_LOG)

    async def get_current_user_uid_sid(self, token: str) -> UserSession:
        """Get current user DI."""
        payload = await self.token_service.check_token(token)
        return UserSession(uid=payload[SUB], sid=payload[SID])

    async def get_current_user_id(self, token: str) -> str:
        """Get current user DI."""
        return (await self.token_service.check_token(token))[SUB]


def init_user_service(
    app: FastAPI,
    token_service: TokenService,
) -> None:
    """Create UserService once and store on app.state."""
    app.state.user_service = UserService(token_service=token_service)


def get_user_service(request: Request) -> UserService:
    """FastAPI dependency for UserService."""
    return request.app.state.user_service
