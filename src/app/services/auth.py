from enum import StrEnum, auto
from logging import getLogger

from app.constants.auth import (
    LOGOUT_ALL_MESSAGE,
    LOGOUT_MESSAGE,
    LOGOUT_OTHERS_MESSAGE,
)
from app.schemes import ClientInfo, Tokens
from app.services.token import TokenService


class LoginType(StrEnum):
    doc = auto()
    telegram = auto()
    web = auto()
    bot = auto()


class BaseAuthService:
    """Base Auth service."""

    def __init__(self, token_service: TokenService):
        """Class constructor."""
        self.token_service = token_service
        self.log = getLogger(__name__)

    async def refresh_user_tokens(
        self, refresh_token: str, client_info: ClientInfo
    ) -> Tokens:
        """Refresh user tokens."""
        return await self.token_service.refresh_tokens(
            refresh_token, client_info
        )

    async def logout_user(self, user_id: str, sid: str) -> str:
        """User logout."""
        await self.token_service.delete_sessions(user_id=user_id, sid=sid)
        return LOGOUT_MESSAGE

    async def logout_others_sessions(
        self, user_id: str, current_sid: str
    ) -> str:
        """Logout other user sessions."""
        await self.token_service.delete_sessions(
            user_id=user_id, current_sid=current_sid
        )
        return LOGOUT_OTHERS_MESSAGE

    async def logout_all_sessions(self, user_id: str) -> str:
        """Logout all user sessions."""
        await self.token_service.delete_sessions(user_id=user_id)
        return LOGOUT_ALL_MESSAGE
