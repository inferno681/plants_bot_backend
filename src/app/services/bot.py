from logging import getLogger

from fastapi import FastAPI, Request

from app.constants.auth import SUB, TYPE
from app.exceptions.auth import UserPermissionError
from app.logs.bot import BOT_SERVICE_START_LOG
from app.services.token import TokenService


class BotService:
    """Bot service."""

    def __init__(
        self,
        token_service: TokenService,
    ):
        """Bot service initialization."""
        self.token_service = token_service
        self.log = getLogger(__name__)
        self.log.info(BOT_SERVICE_START_LOG)

    async def check_bot_permission(self, token: str) -> str:
        """Get current bot id."""
        payload = await self.token_service.check_token(token)
        if payload[TYPE] != 'bot':
            raise UserPermissionError()
        return payload[SUB]


def init_bot_service(
    app: FastAPI,
    token_service: TokenService,
) -> None:
    """Create BotService once and store on app.state."""
    app.state.bot_service = BotService(
        token_service=token_service,
    )


def get_bot_service(request: Request) -> BotService:
    """FastAPI dependency for BotService."""
    return request.app.state.bot_service
