import hashlib
import hmac
import json
import time
import urllib

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import DuplicateKeyError

from app.constants import auth
from app.exceptions.auth import InvalidInitDataError, InvalidSignatureError
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
from app.services.token import TokenService, token_service
from config import config


class TelegramAuthService(BaseAuthService):
    """Telegram Auth service."""

    def __init__(self, token_service: TokenService):
        """Class constructor."""
        super().__init__(token_service)
        self.log.info(TELEGRAM_AUTH_SERVICE_START_LOG)

    def verify_telegram_init_data(self, init_data: str) -> dict:
        parsed = self._parse_init_data(init_data)
        user_data = self._check_init_data(parsed)

        calculated_hash = hmac.new(
            hmac.new(
                key=b'WebAppData',
                msg=config.secrets.bot_token.get_secret_value().encode(),
                digestmod=hashlib.sha256,
            ).digest(),
            '\n'.join(
                f'{key}={field}'
                for key, field in sorted(
                    (key, field)
                    for key, field in parsed.items()
                    if key != 'hash'
                )
            ).encode(),
            hashlib.sha256,
        ).hexdigest()

        if calculated_hash != parsed['hash']:
            raise InvalidSignatureError()

        return user_data

    async def login_telegram_user(
        self,
        init_data: str,
        client_info: ClientInfo,
        session: AsyncClientSession,
    ) -> Tokens:
        """Authenticate telegram user and return JWT tokens."""
        user_data = self.verify_telegram_init_data(init_data)
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

    def _parse_init_data(self, init_data: str) -> dict:
        """Parse init data."""
        try:
            parsed_raw = urllib.parse.parse_qs(init_data, strict_parsing=True)
        except Exception:
            raise InvalidInitDataError()
        return {key: field[0] for key, field in parsed_raw.items()}

    def _check_init_data(self, parsed: dict) -> dict:
        """Check init data."""
        errors: list = []

        self._check_required_fields(parsed, errors)
        user_data = self._check_user_data(parsed, errors)
        self._check_auth_date(parsed, errors)

        if errors:
            raise InvalidInitDataError(errors)

        return user_data

    def _check_required_fields(self, parsed: dict, errors: list):
        """Check required fields."""
        missing = [
            field
            for field in auth.REQUIRED_INIT_DATA_FIELDS
            if field not in parsed
        ]
        if missing:
            errors.append(
                auth.MISSED_FIELDS_MSG.format(fields=', '.join(missing))
            )

    def _check_auth_date(self, parsed: dict, errors: list):
        """Check auth date."""
        try:
            auth_date = int(parsed.get('auth_date', 0))
        except ValueError:
            errors.append(auth.INVALID_AUTH_DATE_MESSAGE)
            return

        if int(time.time()) - auth_date > config.service.init_data_max_age:
            errors.append(auth.INIT_DATA_EXPIRED_MESSAGE)

    def _check_user_data(self, parsed: dict, errors: list) -> dict:
        """Check user data."""
        try:
            user_data = json.loads(parsed.get('user', '{}'))
        except Exception:
            errors.append(auth.INVALID_INIT_DATA_USER_DATA_MSG)
            return {}

        if not user_data:
            errors.append(auth.NO_USER_DATA_MSG)
            return {}

        user_id = user_data.get('id')
        if not user_id:
            errors.append(auth.USER_ID_MISSED_INIT_DATA_MSG)
            return {}

        return user_data


telegram_auth_service = TelegramAuthService(token_service=token_service)
