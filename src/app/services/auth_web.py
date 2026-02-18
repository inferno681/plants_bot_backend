from fastapi import FastAPI, Request
from pwdlib import PasswordHash
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import DuplicateKeyError

from app.exceptions.auth import InvalidCredentialsError, UserAlreadyExistsError
from app.logs.auth import (
    FAILED_LOGIN_LOG,
    SAME_EMAIL_REGISTRATION_LOG,
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

    def __init__(
        self, token_service: TokenService, doc_pass: str, pepper: str
    ):
        """Class constructor."""
        super().__init__(token_service)
        self.password_hasher = PasswordHash.recommended()
        self.doc_pass = doc_pass
        self.pepper = pepper
        self.fake_hash = self.password_hasher.hash('fake_password')
        self.log.info(WEB_AUTH_SERVICE_START_LOG)

    async def registration_web_user(
        self, account_data: WebAccountRegistration, session: AsyncClientSession
    ) -> User:
        """User registration."""

        try:
            user = User(
                email=account_data.email,
                hashed_password=self.password_hasher.hash(
                    account_data.password + self.pepper
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
        password_hash = user.hashed_password if user else self.fake_hash
        try:
            valid = self.password_hasher.verify(
                login_data.password + self.pepper, password_hash
            )
        except Exception:
            valid = False
        if not valid or not user or user.status != UserStatus.active:
            self.log.info(
                FAILED_LOGIN_LOG, client_info.ip, client_info.user_agent
            )
            raise InvalidCredentialsError()
        self.log.info(USER_LOGIN_LOG, str(user.id), LoginType.web)
        return await self.token_service.create_and_put_tokens(
            str(user.id), client_info, LoginType.web
        )


def init_web_auth_service(
    app: FastAPI, token_service: TokenService, doc_pass: str, pepper: str
) -> None:
    """Create WebAuthService once and store on app.state."""
    app.state.web_auth_service = WebAuthService(
        token_service=token_service, doc_pass=doc_pass, pepper=pepper
    )


def get_web_auth_service(request: Request) -> WebAuthService:
    """FastAPI dependency for WebAuthService."""
    return request.app.state.web_auth_service
