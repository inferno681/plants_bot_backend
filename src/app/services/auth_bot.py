import hashlib
import hmac
import time
import urllib
from logging import getLogger

from app.constants.auth import (
    INIT_DATA_EXPIRED_MESSAGE,
    INVALID_AUTH_DATE_MESSAGE,
    INVALID_INIT_DATA_FORMAT_MESSAGE,
    INVALID_SIGNATURE_MESSAGE,
    LOGOUT_MESSAGE,
    MISSED_FIELDS_MSG,
    REQUIRED_FIELDS_BOT_INIT_DATA,
)
from app.exception import (
    InvalidInitDataError,
    InvalidSignatureError,
    UserNotFoundError,
)
from app.logs.auth import (
    BOT_AUTH_SERVICE_START_LOG,
    UNREGISTERED_BOT_LOG,
    USER_LOGIN_LOG,
)
from app.models import Bot
from app.schemes import ClientInfo, Tokens
from app.services.auth import LoginType
from app.services.token import TokenService, token_service
from config import config


class BotAuthService:
    """Telegram Auth service."""

    def __init__(
        self, token_service: TokenService, init_data_max_age: int, secret: str
    ):
        """Class constructor."""
        self.token_service = token_service
        self.log = getLogger(__name__)
        self.init_data_max_age = init_data_max_age
        self.secret = secret
        self.log.info(BOT_AUTH_SERVICE_START_LOG)

    async def bot_login(self, bot_data, client_info: ClientInfo):
        """Bot login."""
        payload = self.verify_init_data(bot_data)
        bot = await Bot.find_one(Bot.id == payload['bot_id'])
        if not bot:
            self.log.info(UNREGISTERED_BOT_LOG, payload['bot_id'])
            raise UserNotFoundError()
        self.log.info(USER_LOGIN_LOG, payload['bot_id'], LoginType.bot)
        return await self.token_service.create_and_put_tokens(
            str(bot.id), client_info, 'bot'
        )

    async def logout(self, bot_id: str, sid: str) -> str:
        """User logout."""
        await self.token_service.delete_sessions(user_id=bot_id, sid=sid)
        return LOGOUT_MESSAGE

    async def refresh_user_tokens(
        self, refresh_token: str, client_info: ClientInfo
    ) -> Tokens:
        """Refresh user tokens."""
        return await self.token_service.refresh_tokens(
            refresh_token, client_info
        )

    def verify_init_data(self, init_data: str) -> dict:
        """Verify init data."""
        parsed = self._parse_init_data(init_data)
        self._check_init_data(parsed)
        self._verify_signature(parsed)
        return parsed

    def _parse_init_data(self, init_data: str) -> dict:
        """Parse init data."""
        try:
            parsed_raw = urllib.parse.parse_qs(init_data, strict_parsing=True)
        except Exception:
            raise InvalidInitDataError(INVALID_INIT_DATA_FORMAT_MESSAGE)

        return {key: field[0] for key, field in parsed_raw.items()}

    def _check_init_data(self, parsed: dict):
        """Validate required fields & auth_date."""
        errors: list[str] = []

        self._check_required_fields(parsed, errors)
        self._check_auth_date(parsed, errors)

        if errors:
            raise InvalidInitDataError(errors)

    def _check_required_fields(self, parsed: dict, errors: list[str]):
        """Check presence of required fields."""
        required = REQUIRED_FIELDS_BOT_INIT_DATA
        missing = [field for field in required if field not in parsed]

        if missing:
            errors.append(MISSED_FIELDS_MSG.format(fields=', '.join(missing)))

    def _check_auth_date(self, parsed: dict, errors: list[str]):
        """Check auth_date validity."""
        try:
            auth_date = int(parsed.get('auth_date', 0))
        except ValueError:
            errors.append(INVALID_AUTH_DATE_MESSAGE)
            return

        if int(time.time()) - auth_date > self.init_data_max_age:
            errors.append(INIT_DATA_EXPIRED_MESSAGE)

    def _verify_signature(self, parsed: dict):
        """Verify HMAC signature."""
        signature = parsed.pop('hash')

        inner = hmac.new(
            key=b'BotLogin',
            msg=self.secret.encode(),
            digestmod=hashlib.sha256,
        ).digest()

        expected = hmac.new(
            key=inner,
            msg='&'.join(
                f'{key}={parsed[key]}' for key in sorted(parsed)
            ).encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            raise InvalidSignatureError(INVALID_SIGNATURE_MESSAGE)


bot_auth_service = BotAuthService(
    token_service=token_service,
    init_data_max_age=config.service.bot_init_data_max_age,
    secret=config.secrets.bot_token.get_secret_value(),
)
