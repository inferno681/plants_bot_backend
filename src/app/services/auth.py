from logging import getLogger

from bson import ObjectId

from app.constants import auth
from app.exception import InvalidCredentialsError, UserNotFoundError
from app.log_messages import UNREGISTERED_USER_LOG, USER_LOGIN_LOG
from app.models import User
from app.schemes import Tokens
from app.services.token import TokenService

DOC_USER = ObjectId('68fdd756d174872a92b7e87d')


class BaseAuthService:
    """Base Auth service."""

    def __init__(self, token_service: TokenService):
        """Class constructor."""
        self.token_service = token_service
        self.log = getLogger(__name__)

    async def refresh_user_tokens(
        self, refresh_token: str, ip: str, ua: str
    ) -> Tokens:
        """Refresh user tokens."""
        return await self.token_service.refresh_tokens(refresh_token, ip, ua)

    async def login_doc(self, password: str, ip: str, ua: str) -> Tokens:
        """Login for documentation access."""
        if password != '123':
            raise InvalidCredentialsError(
                auth.INVALID_DOC_PASSWORD_MESSAGE,
            )
        user = await User.find_one(User.id == DOC_USER)
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, DOC_USER)
            raise UserNotFoundError(auth.UNREGISTERED_USER_MESSAGE)
        self.log.info(USER_LOGIN_LOG, DOC_USER)
        return await self.token_service.create_and_put_tokens(DOC_USER, ip, ua)

    async def logout_user(self, user_id: str, sid: str) -> str:
        """User logout."""
        await self.token_service.delete_sessions(user_id=user_id, sid=sid)
        return auth.LOGOUT_MESSAGE

    async def logout_others_sessions(
        self, user_id: str, current_sid: str
    ) -> str:
        """Logout other user sessions."""
        await self.token_service.delete_sessions(
            user_id=user_id, current_sid=current_sid
        )
        return auth.LOGOUT_OTHERS_MESSAGE

    async def logout_all_sessions(self, user_id: str) -> str:
        """Logout all user sessions."""
        await self.token_service.delete_sessions(user_id=user_id)
        return auth.LOGOUT_ALL_MESSAGE
