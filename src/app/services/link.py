import secrets
import time
from logging import getLogger
from types import SimpleNamespace

from beanie import PydanticObjectId
from beanie.operators import Exists
from fastapi import FastAPI, Request
from pymongo.asynchronous.client_session import AsyncClientSession
from redis.asyncio import Redis

from app.constants.general import SCRIPTS_DIR
from app.constants.link import (
    BOT_LINK,
    CODE_LENGTH,
    LINK_CODE,
    LINK_USER,
    LINKING_CODE_SYMBOLS,
    MIN_TTL_SECONDS,
    QR_LINK,
    USER_UNLINK_MSG,
)
from app.exceptions.auth import UserNotFoundError
from app.exceptions.link import (
    AlreadyLinkedError,
    BusyError,
    CodeAllocationError,
    InvalidCodeProvided,
    TelegramConnectError,
)
from app.logs.link import (
    ALLOCATION_ERROR_LOG,
    INVALID_CODE_LOG,
    LINK_CODE_SCRIPT_LOADED_LOG,
    LINK_SERVICE_START_LOG,
    TELEGRAM_ALREADY_CONNECTED_LOG,
)
from app.models import User
from app.schemes import TelegramLink


class LinkService:
    """Link service."""

    def __init__(
        self,
        redis: Redis,
        link_ttl: int,
    ):
        """Link service initialization."""

        self.redis = redis
        self.link_ttl = link_ttl
        self.lua = SimpleNamespace()
        self.log = getLogger(__name__)
        self.load_lua_scripts(link_code_pair_filename='link_code_pair.lua')
        self.log.info(LINK_SERVICE_START_LOG)

    def load_lua_scripts(self, link_code_pair_filename: str) -> None:
        """Load Lua scripts into Redis."""
        self.lua.link_code_pair_script = self.redis.register_script(
            SCRIPTS_DIR.joinpath(link_code_pair_filename).read_text()
        )
        self.log.info(
            LINK_CODE_SCRIPT_LOADED_LOG, self.lua.link_code_pair_script.sha
        )

    async def create_telegram_link(self, user_id: str) -> TelegramLink:
        """Code generation for telegram linking."""
        if await User.find_one(
            User.id == PydanticObjectId(user_id), Exists(User.telegram_id)
        ):
            self.log.info(TELEGRAM_ALREADY_CONNECTED_LOG, user_id)
            raise TelegramConnectError()
        existing = await self.redis.get(f'{LINK_USER}{user_id}')
        if existing:
            ttl = await self.redis.ttl(f'{LINK_USER}{user_id}')
            if ttl > MIN_TTL_SECONDS:
                return TelegramLink(
                    code=existing,
                    qr=QR_LINK.format(code=existing),
                    link=BOT_LINK.format(code=existing),
                    expires_at=int(time.time()) + ttl,
                )
            else:
                await self.redis.unlink(
                    f'{LINK_USER}{user_id}', f'{LINK_CODE}{existing}'
                )
        for _ in range(5):
            code = self.generate_link_code()
            created = await self.lua.link_code_pair_script(  # noqa: WPS47
                keys=[f'{LINK_CODE}{code}', f'{LINK_USER}{user_id}'],
                args=[user_id, code, self.link_ttl],
            )

            if created:
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
        user.telegram_id = None
        user.first_name = None
        user.last_name = None
        user.username = None
        user.is_premium = None
        user.language_code = None
        await user.save_changes()
        return {'message': USER_UNLINK_MSG}

    @staticmethod
    def generate_link_code(length=CODE_LENGTH):
        return ''.join(
            secrets.choice(LINKING_CODE_SYMBOLS) for _ in range(length)
        )

    async def _link_process(
        self,
        user_id: PydanticObjectId,
        session: AsyncClientSession,
        telegram_id: int,
    ) -> PydanticObjectId | None:
        """Linking process."""
        user = await User.find_one(User.id == user_id, session=session)
        if not user:
            raise UserNotFoundError()
        if user.telegram_id:
            raise AlreadyLinkedError()
        else:
            user.telegram_id = telegram_id
            await user.save_changes(session=session)
        return user.id


def init_link_service(
    app: FastAPI,
    redis: Redis,
    link_ttl: int,
) -> None:
    """Create LinkService once and store on app.state."""
    app.state.link_service = LinkService(
        redis=redis,
        link_ttl=link_ttl,
    )


def get_link_service(request: Request) -> LinkService:
    """FastAPI dependency for LinkService."""
    return request.app.state.link_service
