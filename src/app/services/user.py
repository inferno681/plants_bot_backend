import secrets
import time
from logging import getLogger

from beanie import PydanticObjectId
from fastapi import FastAPI, Request
from redis.asyncio import Redis

from app.constants.auth import SID, SUB
from app.constants.user import (
    BOT_LINK,
    CODE_LENGTH,
    LINK_CODE,
    LINK_USER,
    LINKING_CODE_SYMBOLS,
    QR_LINK,
)
from app.exceptions.auth import UserNotFoundError
from app.exceptions.user import CodeAllocationError
from app.log_messages import USER_SERVICE_START_LOG
from app.logs.user import ALLOCATION_ERROR_LOG
from app.models import User
from app.schemes import TelegramLink, UserSession, WebUserInfo
from app.services.pipeline import MongoPipelineBuilder
from app.services.token import TokenService


class UserService:
    """User service."""

    def __init__(
        self,
        token_service: TokenService,
        pipeline_builder: MongoPipelineBuilder,
        redis: Redis,
        link_ttl: int,
    ):
        """User service initialization."""
        self.token_service = token_service
        self.pipeline_builder = pipeline_builder
        self.redis = redis
        self.link_ttl = link_ttl
        self.log = getLogger(__name__)
        self.log.info(USER_SERVICE_START_LOG)

    async def get_current_user_uid_sid(self, token: str) -> UserSession:
        """Get current user DI."""
        payload = await self.token_service.check_token(token)
        return UserSession(uid=payload[SUB], sid=payload[SID])

    async def get_current_user_id(self, token: str) -> str:
        """Get current user DI."""
        return (await self.token_service.check_token(token))[SUB]

    async def get_web_user_info(
        self, user_id: PydanticObjectId
    ) -> WebUserInfo:
        """Get user info."""
        pipeline = self.pipeline_builder.build_user_info_pipeline(
            user_id=user_id
        )
        docs = await User.aggregate(pipeline).to_list()
        if not docs:
            raise UserNotFoundError()

        return WebUserInfo(**docs[0])

    async def create_telegram_link(self, user_id: str) -> TelegramLink:
        """Code generation for telegram linking."""
        existing = await self.redis.get(f'{LINK_USER}{user_id}')
        if existing:
            ttl = await self.redis.ttl(f'{LINK_USER}{user_id}')
            if ttl > 0:
                return TelegramLink(
                    code=existing,
                    qr=QR_LINK.format(code=existing),
                    link=BOT_LINK.format(code=existing),
                    expires_at=int(time.time()) + ttl,
                )

        for _ in range(5):
            code = self.generate_link_code()
            pipe = self.redis.pipeline()
            pipe.set(f'{LINK_CODE}{code}', user_id, ex=self.link_ttl, nx=True)
            pipe.set(f'{LINK_USER}{user_id}', code, ex=self.link_ttl)
            pipe_result = await pipe.execute()  # noqa: WPS476

            if pipe_result[0]:
                return TelegramLink(
                    code=code,
                    qr=QR_LINK.format(code=code),
                    link=BOT_LINK.format(code=code),
                    expires_at=int(time.time()) + self.link_ttl,
                )
        self.log.warning(ALLOCATION_ERROR_LOG, user_id)
        raise CodeAllocationError()

    @staticmethod
    def generate_link_code(length=CODE_LENGTH):
        return ''.join(
            secrets.choice(LINKING_CODE_SYMBOLS) for _ in range(length)
        )


def init_user_service(
    app: FastAPI,
    token_service: TokenService,
    pipeline_builder: MongoPipelineBuilder,
    redis: Redis,
    link_ttl: int,
) -> None:
    """Create UserService once and store on app.state."""
    app.state.user_service = UserService(
        token_service=token_service,
        pipeline_builder=pipeline_builder,
        redis=redis,
        link_ttl=link_ttl,
    )


def get_user_service(request: Request) -> UserService:
    """FastAPI dependency for UserService."""
    return request.app.state.user_service
