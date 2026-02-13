from fastapi import FastAPI, Request
from pwdlib import PasswordHash
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import DuplicateKeyError

from app.constants.auth import DOC_USER
from app.exceptions.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.logs.auth import (
    INACTIVE_USER_LOGIN_ATTEMPT_LOG,
    INVALID_DOC_PASSWORD_LOG,
    INVALID_WEB_PASSWORD_LOG,
    SAME_EMAIL_REGISTRATION_LOG,
    UNREGISTERED_USER_LOG,
    USER_LOGIN_LOG,
    WEB_AUTH_SERVICE_START_LOG,
)
from app.models import User, UserStatus
from app.schemes import ClientInfo, Tokens, WebUserView
from app.schemes.auth import WebAccountLogin, WebAccountRegistration
from app.services.auth import BaseAuthService
from app.services.token import LoginType, TokenService


class WebAuthService(BaseAuthService):
    """Telegram Auth service."""

    def __init__(self, token_service: TokenService, doc_pass: str):
        """Class constructor."""
        super().__init__(token_service)
        self.password_hasher = PasswordHash.recommended()
        self.doc_pass = doc_pass
        self.log.info(WEB_AUTH_SERVICE_START_LOG)

    async def registration_web_user(
        self, account_data: WebAccountRegistration, session: AsyncClientSession
    ) -> User:
        """User registration."""

        try:
            user = User(
                email=account_data.email,
                hashed_password=self.password_hasher.hash(
                    account_data.password
                ),
            )
            await user.insert(session=session)

        except DuplicateKeyError:
            self.log.info(SAME_EMAIL_REGISTRATION_LOG, account_data.email)
            raise UserAlreadyExistsError()

        return user

    async def login(
        self, login_data: WebAccountLogin, client_info: ClientInfo
    ) -> Tokens:
        """User login."""
        user = await User.find_one(
            User.email == login_data.email, projection_model=WebUserView
        )
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, login_data.email)
            raise InvalidCredentialsError()
        if user.status != UserStatus.active:
            self.log.warning(INACTIVE_USER_LOGIN_ATTEMPT_LOG, user.id)
            raise UserNotFoundError()
        if self.password_hasher.verify(
            login_data.password, user.hashed_password
        ):
            self.log.info(USER_LOGIN_LOG, str(user.id), LoginType.web)
            return await self.token_service.create_and_put_tokens(
                str(user.id), client_info, LoginType.web
            )
        self.log.warning(INVALID_WEB_PASSWORD_LOG, login_data.email)
        raise InvalidCredentialsError()

    async def login_doc(
        self, password: str, client_info: ClientInfo
    ) -> Tokens:
        """Login for documentation access."""
        if password != self.doc_pass:
            self.log.warning(
                INVALID_DOC_PASSWORD_LOG, client_info.ip, client_info.ua
            )
            raise InvalidCredentialsError()
        user = await User.find_one(User.id == DOC_USER)
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, DOC_USER)
            raise UserNotFoundError()
        if user.status != UserStatus.active:
            self.log.warning(INACTIVE_USER_LOGIN_ATTEMPT_LOG, user.id)
            raise UserNotFoundError()
        self.log.info(USER_LOGIN_LOG, DOC_USER, LoginType.doc)
        return await self.token_service.create_and_put_tokens(
            str(DOC_USER), client_info, LoginType.doc
        )


def init_web_auth_service(
    app: FastAPI, token_service: TokenService, doc_pass: str
) -> None:
    """Create WebAuthService once and store on app.state."""
    app.state.web_auth_service = WebAuthService(
        token_service=token_service, doc_pass=doc_pass
    )


def get_web_auth_service(request: Request) -> WebAuthService:
    """FastAPI dependency for WebAuthService."""
    return request.app.state.web_auth_service
