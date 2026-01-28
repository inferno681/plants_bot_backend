import secrets
import time
from datetime import datetime, timezone
from logging import getLogger

from beanie import PydanticObjectId
from beanie.operators import Set
from fastapi import FastAPI, Request
from pymongo.asynchronous.client_session import AsyncClientSession
from redis.asyncio import Redis

from app.constants.auth import SID, SUB
from app.constants.user import (
    BOT_LINK,
    CODE_LENGTH,
    LINK_CODE,
    LINK_USER,
    LINKING_CODE_SYMBOLS,
    QR_LINK,
    USER_DELETE_MSG,
    USER_UNLINK_MSG,
)
from app.exceptions.auth import UserNotFoundError
from app.exceptions.user import (
    BusyError,
    CodeAllocationError,
    InvalidCodeProvided,
    SecondLinkAttempt,
    TelegramConnectError,
)
from app.logs.user import (
    ALLOCATION_ERROR_LOG,
    INVALID_CODE_LOG,
    TELEGRAM_ALREADY_CONNECTED_LOG,
    USER_DELETE_LOG,
    USER_SERVICE_START_LOG,
)
from app.models import TelegramAccount, User, UserStatus, WebAccount
from app.schemes import TelegramLink, UserSession, WebUserInfo
from app.services import MongoPipelineBuilder, TokenService


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
        if await TelegramAccount.find_one(
            TelegramAccount.user_id == PydanticObjectId(user_id)
        ):
            self.log.info(TELEGRAM_ALREADY_CONNECTED_LOG, user_id)
            raise TelegramConnectError()
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
            pipe.set(f'{LINK_USER}{user_id}', code, ex=self.link_ttl, nx=True)
            pipe_result = await pipe.execute()  # noqa: WPS476

            if pipe_result[0] and pipe_result[1]:
                return TelegramLink(
                    code=code,
                    qr=QR_LINK.format(code=code),
                    link=BOT_LINK.format(code=code),
                    expires_at=int(time.time()) + self.link_ttl,
                )
        self.log.warning(ALLOCATION_ERROR_LOG, user_id)
        raise CodeAllocationError()

    async def link_telegram(
        self, code: str, telegram_id: int, session: AsyncClientSession
    ) -> tuple[PydanticObjectId | None, PydanticObjectId]:
        """Link telegram telegram to web account."""
        user_id = await self.redis.get(f'{LINK_CODE}{code}')
        if not user_id:
            self.log.info(INVALID_CODE_LOG, code, telegram_id)
            raise InvalidCodeProvided()
        lock_key = f'LOCK:TG:{telegram_id}'
        lock = await self.redis.set(lock_key, 1, nx=True, ex=5)
        if not lock:
            raise BusyError()
        user_id_obj = PydanticObjectId(user_id)

        try:
            old_user_id = await self._link_process(
                user_id_obj, session, telegram_id
            )
        except Exception:
            await self.redis.delete(lock_key)
            raise
        else:
            await self.redis.delete(lock_key)
        return old_user_id, user_id_obj

    async def clear_link_code(self, user_id: str, code: str) -> None:
        """Clear linking code after successful linking."""
        await self.redis.delete(f'{LINK_USER}{user_id}', f'{LINK_CODE}{code}')

    async def delete_telegram_link(self, user_id: PydanticObjectId):
        """Delete telegram link from user account."""
        user = await User.find_one(User.id == user_id)
        if not user:
            raise UserNotFoundError()
        await TelegramAccount.find(TelegramAccount.user_id == user_id).delete()
        return {'message': USER_UNLINK_MSG}

    async def delete_user(self, user_id: PydanticObjectId) -> dict:
        """Delete user and associated accounts."""
        user = await User.find_one(User.id == user_id)
        if not user:
            raise UserNotFoundError()
        await TelegramAccount.find(TelegramAccount.user_id == user_id).delete()
        await WebAccount.find(WebAccount.user_id == user_id).delete()
        user.status = UserStatus.deleted
        await user.save_changes()
        self.log.info(USER_DELETE_LOG, str(user_id))
        return {'message': USER_DELETE_MSG}

    @staticmethod
    def generate_link_code(length=CODE_LENGTH):
        return ''.join(
            secrets.choice(LINKING_CODE_SYMBOLS) for _ in range(length)
        )

    async def _link_process(
        self,
        user_id_obj: PydanticObjectId,
        session: AsyncClientSession,
        telegram_id: int,
    ) -> PydanticObjectId | None:
        """Linking process."""
        old_acc = await TelegramAccount.find_one(
            TelegramAccount.telegram_id == telegram_id, session=session
        )
        if old_acc:
            if old_acc.user_id == user_id_obj:
                raise SecondLinkAttempt()
            old_user_id = old_acc.user_id
            old_acc.user_id = user_id_obj
            await old_acc.save_changes(session=session)
            await WebAccount.find(
                WebAccount.user_id == old_user_id, session=session
            ).delete()
            now = datetime.now(timezone.utc)
            await User.find_one(
                User.id == old_user_id, session=session
            ).update(
                Set(
                    {
                        User.status: UserStatus.merged,
                        User.merged_into: user_id_obj,
                        User.merged_at: now,
                        User.updated_at: now,
                    }
                )
            )
        else:
            old_user_id = None
            new_acc = TelegramAccount(
                telegram_id=telegram_id, user_id=user_id_obj
            )
            await new_acc.insert(session=session)
        return old_user_id


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
