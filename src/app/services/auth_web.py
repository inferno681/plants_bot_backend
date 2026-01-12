from pwdlib import PasswordHash
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import DuplicateKeyError

from app.exception import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.logs.auth import (
    UNREGISTERED_USER_LOG,
    USER_LOGIN_LOG,
    WEB_AUTH_SERVICE_START_LOG,
)
from app.models import User, WebAccount
from app.schemes import ClientInfo, Tokens
from app.schemes.auth import WebAccountLogin, WebAccountRegistration
from app.services.auth import BaseAuthService, LoginType
from app.services.token import TokenService, token_service


class WebAuthService(BaseAuthService):
    """Telegram Auth service."""

    def __init__(self, token_service: TokenService):
        """Class constructor."""
        super().__init__(token_service)
        self.password_hasher = PasswordHash.recommended()
        self.log.info(WEB_AUTH_SERVICE_START_LOG)

    async def registration_web_user(
        self, account_data: WebAccountRegistration, session: AsyncClientSession
    ) -> User:
        """User registration."""
        user = User(language_code=account_data.language_code)
        await user.insert(session=session)

        try:
            web_account = WebAccount(
                user_id=user.id,
                email=account_data.email,
                hashed_password=self.password_hasher.hash(
                    account_data.password
                ),
            )
            await web_account.insert(session=session)

        except DuplicateKeyError:
            raise UserAlreadyExistsError()

        return web_account

    async def login(
        self, login_data: WebAccountLogin, client_info: ClientInfo
    ) -> Tokens:
        """User login."""
        user = await WebAccount.find_one(WebAccount.email == login_data.email)
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, login_data.email)
            raise UserNotFoundError()
        if self.password_hasher.verify(
            login_data.password, user.hashed_password
        ):
            self.log.info(USER_LOGIN_LOG, str(user.user_id), LoginType.web)
            return await self.token_service.create_and_put_tokens(
                str(user.user_id), client_info
            )
        raise InvalidPasswordError()


web_auth_service = WebAuthService(token_service=token_service)
