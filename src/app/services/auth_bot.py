from logging import getLogger

from app.constants.auth import LOGOUT_MESSAGE
from app.exceptions.auth import UserNotFoundError
from app.logs.auth import (
    BOT_AUTH_SERVICE_START_LOG,
    UNREGISTERED_BOT_LOG,
    USER_LOGIN_LOG,
)
from app.models import Bot
from app.schemes import ClientInfo, Tokens
from app.services.auth import LoginType
from app.services.init_data import (
    ClientType,
    InitDataChecker,
    init_data_checker,
)
from app.services.token import TokenService, token_service


class BotAuthService:
    """Telegram Auth service."""

    def __init__(
        self, token_service: TokenService, init_data_checker: InitDataChecker
    ):
        """Class constructor."""
        self.token_service = token_service
        self.init_data_checker = init_data_checker
        self.log = getLogger(__name__)
        self.log.info(BOT_AUTH_SERVICE_START_LOG)

    async def bot_login(self, bot_data: str, client_info: ClientInfo):
        """Bot login."""
        payload = self.init_data_checker.verify_init_data(
            bot_data, ClientType.bot
        )
        bot = await Bot.find_one(Bot.id == payload['id'])
        if not bot:
            self.log.info(UNREGISTERED_BOT_LOG, payload['id'])
            raise UserNotFoundError()
        self.log.info(USER_LOGIN_LOG, payload['id'], LoginType.bot)
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


bot_auth_service = BotAuthService(
    token_service=token_service,
    init_data_checker=init_data_checker,
)
