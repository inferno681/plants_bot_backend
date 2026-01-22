from fastapi import FastAPI, Request
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import DuplicateKeyError

from app.logs.auth import (
    TELEGRAM_AUTH_SERVICE_START_LOG,
    UNREGISTERED_USER_LOG,
    USER_DATA_UPDATED_LOG,
    USER_LOGIN_LOG,
)
from app.models import TelegramAccount, User
from app.schemes import ClientInfo, Tokens
from app.schemes.auth import TelegramAccountBase
from app.services.auth import BaseAuthService, LoginType
from app.services.init_data import ClientType, InitDataChecker
from app.services.token import TokenService


class TelegramAuthService(BaseAuthService):
    """Telegram Auth service."""

    def __init__(
        self, token_service: TokenService, init_data_checker: InitDataChecker
    ):
        """Class constructor."""
        super().__init__(token_service)
        self.init_data_checker = init_data_checker
        self.log.info(TELEGRAM_AUTH_SERVICE_START_LOG)

    async def login_telegram_user(
        self,
        init_data: str,
        client_info: ClientInfo,
        session: AsyncClientSession,
    ) -> Tokens:
        """Authenticate telegram user and return JWT tokens."""
        user_data = self.init_data_checker.verify_init_data(
            init_data, ClientType.user
        )
        user = await TelegramAccount.find_one(
            TelegramAccount.telegram_id == user_data['id']
        )
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, user_data['id'])
            account_data = TelegramAccountBase(**user_data)
            user = await self.registration_telegram_user(
                account_data=account_data, session=session
            )
        self.log.info(USER_LOGIN_LOG, str(user.user_id), LoginType.telegram)
        await self._update_account_if_changed(user, user_data, session)
        return await self.token_service.create_and_put_tokens(
            str(user.user_id), client_info
        )

    async def registration_telegram_user(
        self, account_data: TelegramAccountBase, session: AsyncClientSession
    ):
        """Telegram user registration."""
        user = User(language_code=account_data.language_code)
        await user.insert(session=session)

        try:
            telegram_account = TelegramAccount(
                user_id=user.id,
                **account_data.model_dump(
                    exclude={'language_code'}, exclude_unset=True
                ),
            )
            await telegram_account.insert(session=session)

        except DuplicateKeyError:
            tg_account = await TelegramAccount.find_one(
                TelegramAccount.telegram_id == account_data.telegram_id
            )
            return tg_account

        return telegram_account

    async def _update_account_if_changed(
        self,
        tg_account: TelegramAccount,
        user_data: dict,
        session: AsyncClientSession,
    ):
        fields = [
            'first_name',
            'last_name',
            'username',
            'is_premium',
        ]
        update_fields = {
            field: user_data.get(field)
            for field in fields
            if user_data.get(field) != getattr(tg_account, field)
        }

        if update_fields:
            await tg_account.set(update_fields, session=session)
            self.log.info(USER_DATA_UPDATED_LOG, tg_account.user_id)


def init_telegram_auth_service(
    app: FastAPI,
    token_service: TokenService,
    init_data_checker: InitDataChecker,
) -> None:
    """Create TelegramAuthService once and store on app.state."""
    app.state.telegram_auth_service = TelegramAuthService(
        token_service=token_service, init_data_checker=init_data_checker
    )


def get_telegram_auth_service(request: Request) -> TelegramAuthService:
    """FastAPI dependency for TelegramAuthService."""
    return request.app.state.telegram_auth_service
