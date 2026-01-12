from enum import StrEnum, auto
from logging import getLogger

from app.constants.auth import (
    DOC_USER,
    INVALID_DOC_PASSWORD_MESSAGE,
    LOGOUT_ALL_MESSAGE,
    LOGOUT_MESSAGE,
    LOGOUT_OTHERS_MESSAGE,
    UNREGISTERED_USER_MESSAGE,
)
from app.exception import InvalidCredentialsError, UserNotFoundError
from app.logs.auth import UNREGISTERED_USER_LOG, USER_LOGIN_LOG
from app.models import User
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

    async def login_doc(
        self, password: str, client_info: ClientInfo
    ) -> Tokens:
        """Login for documentation access."""
        if password != '123':
            raise InvalidCredentialsError(INVALID_DOC_PASSWORD_MESSAGE)
        user = await User.find_one(User.id == DOC_USER)
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, DOC_USER)
            raise UserNotFoundError(UNREGISTERED_USER_MESSAGE)
        self.log.info(USER_LOGIN_LOG, DOC_USER, LoginType.doc)
        return await self.token_service.create_and_put_tokens(
            str(DOC_USER), client_info
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
