import time
from datetime import datetime, timezone
from enum import StrEnum, auto
from functools import lru_cache
from logging import getLogger
from types import SimpleNamespace
from uuid import uuid4

import jwt
from redis.asyncio.client import Redis

from app.constants import auth
from app.constants.general import SCRIPTS_DIR
from app.exceptions.token import (
    TokenExpiredError,
    TokenIntegrityError,
    TokenInvalidError,
    TokenInvalidOwnerError,
    TokenReplayError,
    TokenRevokedError,
)
from app.logs import token as token_logs
from app.schemes import ClientInfo, Tokens

logger = getLogger(__name__)


class LoginType(StrEnum):
    """Login Type model."""

    doc = auto()
    telegram = auto()
    web = auto()
    bot = auto()

    @classmethod
    @lru_cache
    def user_types(cls):
        """Handle user types."""
        return frozenset((cls.web, cls.telegram))


class TokenProvider:
    """Token provider interface."""

    def __init__(
        self,
        access_secret: str,
        refresh_secret: str,
        access_ttl: int,
        refresh_ttl: int,
        algorithm: str = 'HS256',
    ):
        """Service constructor."""
        self.access_secret = access_secret
        self.refresh_secret = refresh_secret
        self.access_ttl = access_ttl
        self.refresh_ttl = refresh_ttl
        self.algorithm = algorithm
        self.log = logger
        self.log.info(token_logs.TOKEN_PROVIDER_START_LOG)

    def issue_access(
        self, user_id: str, sid: str, user_type: LoginType
    ) -> str:
        """Issue access token."""
        now = int(datetime.now(timezone.utc).timestamp())
        return jwt.encode(
            {
                auth.SUB: user_id,
                auth.EXP: now + self.access_ttl,
                auth.SID: sid,
                auth.IAT: now,
                auth.TYPE: user_type,
            },
            self.access_secret,
            algorithm=self.algorithm,
        )

    def issue_refresh(
        self, user_id: str, sid: str, user_type: LoginType
    ) -> str:
        """Issue refresh token."""
        now = int(datetime.now(timezone.utc).timestamp())
        return jwt.encode(
            {
                auth.SUB: user_id,
                auth.EXP: now + self.refresh_ttl,
                auth.SID: sid,
                auth.IAT: now,
                auth.TYPE: user_type,
            },
            self.refresh_secret,
            algorithm=self.algorithm,
        )

    def decode_access(self, token: str) -> dict:
        """Decode access token."""
        try:
            return jwt.decode(
                token,
                self.access_secret,
                algorithms=[self.algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError as exc:
            self.log.warning(
                token_logs.INVALID_ACCESS_TOKEN_LOG, type(exc).__name__
            )
            raise TokenInvalidError()

    def decode_refresh(self, token: str) -> dict:
        """Decode refresh token."""
        try:
            return jwt.decode(
                token,
                self.refresh_secret,
                algorithms=[self.algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError as exc:
            self.log.warning(
                token_logs.INVALID_REFRESH_TOKEN_LOG, type(exc).__name__
            )
            raise TokenInvalidError()


class SessionStore:
    """Session store interface."""

    def __init__(self, redis: Redis, refresh_ttl: int, max_session: int):
        """Class constructor."""
        self.redis = redis
        self.refresh_ttl = refresh_ttl
        self.log = logger
        self.lua = SimpleNamespace()
        self.load_lua_scripts(
            refresh_filename='token_refresh.lua',
            session_create_filename='session_create.lua',
            delete_sessions_filename='delete_sessions_by_type.lua',
        )
        self.max_sessions = max_session
        self.log.info(token_logs.SESSION_STORE_START_LOG)

    def load_lua_scripts(
        self,
        refresh_filename: str,
        session_create_filename: str,
        delete_sessions_filename: str,
    ) -> None:
        """Load Lua scripts into Redis."""
        self.lua.refresh_script = self.redis.register_script(
            SCRIPTS_DIR.joinpath(refresh_filename).read_text()
        )
        self.log.info(
            token_logs.TOKEN_REFRESH_SCRIPT_LOADED_LOG,
            self.lua.refresh_script.sha,
        )
        self.lua.session_create_script = self.redis.register_script(
            SCRIPTS_DIR.joinpath(session_create_filename).read_text()
        )
        self.log.info(
            token_logs.SESSION_CREATE_SCRIPT_LOADED_LOG,
            self.lua.session_create_script.sha,
        )
        self.lua.delete_sessions_script = self.redis.register_script(
            SCRIPTS_DIR.joinpath(delete_sessions_filename).read_text()
        )
        self.log.info(
            token_logs.DELETE_SESSIONS_SCRIPT_LOADED_LOG,
            self.lua.delete_sessions_script.sha,
        )

    async def create_session(
        self,
        user_id: str,
        sid: str,
        client_info: ClientInfo,
        user_type: LoginType,
    ) -> None:
        """Store access and refresh sid in Redis."""
        dropped = await self.lua.session_create_script(
            keys=[f'{auth.USER_SESSIONS_PREFIX}{user_id}'],
            args=[
                (
                    self.max_sessions
                    if user_type in LoginType.user_types()
                    else 1
                ),
                self.refresh_ttl,
                int(time.time()),
                sid,
                client_info.ip,
                client_info.user_agent,
                user_id,
                user_type,
            ],
        )
        removed = dropped[0] if dropped else []
        if removed:
            for session in removed:
                self.log.info(
                    token_logs.SESSIONS_EVICTED_LOG,
                    user_id,
                    session['sid'],
                    session['ip'],
                    session['user_agent'],
                    session['created_at'],
                    session['ttl'],
                    session['type'],
                )

    async def check_sid(
        self,
        user_id: str,
        sid: str,
        user_type: LoginType,
        is_access_token: bool = True,
    ) -> None:
        """Check sid in storage."""

        stored_uid, stored_type, rotated = await self.redis.hmget(
            f'{auth.SESSION_PREFIX}{sid}', ['uid', 'type', 'rotated']
        )
        self._validate_base(stored_uid, stored_type, user_id, user_type)
        is_rotated = rotated and rotated == '1'
        if not is_rotated:
            return

        if is_access_token:
            raise TokenRevokedError()
        raise TokenReplayError()

    async def delete_sessions(
        self,
        user_id: str,
        sid: str | None = None,
        current_sid: str | None = None,
    ) -> None:
        """Delete sessions from Redis."""
        key = f'{auth.USER_SESSIONS_PREFIX}{user_id}'

        if sid:
            raw_sids = [sid]
            session_keys = [f'{auth.SESSION_PREFIX}{sid}']
            log_text = token_logs.SESSION_DELETED_LOG
        else:
            raw_sids, session_keys = await self._collect_bulk_sids(
                key, current_sid
            )
            log_text = (
                token_logs.SESSION_DELETED_OTHERS_LOG
                if current_sid
                else token_logs.ALL_SESSION_DELETED_LOG
            )

        if not raw_sids:
            return

        async with self.redis.pipeline() as pipe:
            pipe.unlink(*session_keys)
            pipe.zrem(key, *raw_sids)
            await pipe.execute()
        self.log.info(log_text, user_id)

    async def refresh_sessions(
        self,
        user_id: str,
        sid: str,
        client_info: ClientInfo,
        user_type: LoginType,
    ) -> str:
        """Refresh sids in storage."""

        new_sid = str(uuid4())

        try:
            script_result = await self.lua.refresh_script(
                keys=[
                    f"{auth.SESSION_PREFIX}{sid}",
                    f"{auth.USER_SESSIONS_PREFIX}{user_id}",
                ],
                args=[
                    sid,
                    new_sid,
                    user_id,
                    self.refresh_ttl,
                    int(time.time()),
                    client_info.ip,
                    client_info.user_agent,
                    user_type,
                ],
            )
        except Exception as exc:
            self.log.warning(
                token_logs.REFRESH_REJECTED_LOG,
                user_id,
                type(exc).__name__,
            )
            raise TokenInvalidError()
        if isinstance(script_result, dict) and 'err' in script_result:
            if script_result['err'] == 'REPLAY':
                self.log.error(
                    token_logs.REFRESH_REPLAY_DETECTED_LOG,
                    user_id,
                    client_info.ip,
                    client_info.user_agent,
                    user_type,
                )
                raise TokenReplayError()
            else:
                self.log.error(
                    token_logs.REFRESH_UNKNOWN_ERROR_LOG,
                    script_result['err'],
                )
                raise TokenInvalidError()

        return new_sid

    async def delete_sessions_by_type(
        self,
        user_id: str,
        user_type: LoginType,
    ) -> int:
        """Delete all sessions of a specific type for a user."""
        deleted_count = await self.lua.delete_sessions_script(
            keys=[f'{auth.USER_SESSIONS_PREFIX}{user_id}'],
            args=[
                auth.SESSION_PREFIX,
                user_type,
            ],
        )

        if deleted_count > 0:
            self.log.info(
                token_logs.SESSIONS_DELETED_BY_TYPE_LOG,
                deleted_count,
                user_id,
                user_type,
            )

        return deleted_count

    def _validate_base(
        self,
        stored_uid: str | None,
        stored_type: str | None,
        user_id: str,
        expected_type: str,
    ) -> None:
        """Base token check."""
        if not stored_uid or not stored_type:
            self.log.warning(token_logs.TOKEN_MISSED_UID_TYPE_LOG, user_id)
            raise TokenInvalidError()

        if stored_uid != user_id:
            self.log.warning(
                token_logs.TOKEN_OWNER_MISMATCH_LOG, user_id, stored_uid
            )
            raise TokenInvalidOwnerError()

        if stored_type != expected_type:
            self.log.warning(
                token_logs.TOKEN_TYPE_MISMATCH_LOG, expected_type, stored_type
            )
            raise TokenIntegrityError()

    async def _collect_bulk_sids(
        self,
        key: str,
        current_sid: str | None,
    ) -> tuple[list[str], list[str]]:
        """Collect sids and session keys for bulk deletion."""
        all_sids = await self.redis.zrange(key, 0, -1)

        sids = []
        keys = []

        for sid in all_sids:
            if sid != current_sid:
                sids.append(sid)
                keys.append(f'{auth.SESSION_PREFIX}{sid}')

        return sids, keys


class TokenService:
    """Token service."""

    def __init__(self, provider: TokenProvider, store: SessionStore):
        """Class constructor."""
        self.provider = provider
        self.store = store
        self.log = logger
        self.log.info(token_logs.TOKEN_SERVICE_START_LOG)

    async def create_and_put_tokens(
        self, user_id: str, client_info: ClientInfo, user_type: LoginType
    ) -> Tokens:
        """Create JWT access and refresh tokens and store them in Redis."""
        sid = str(uuid4())
        access_token = self.provider.issue_access(user_id, sid, user_type)
        refresh_token = self.provider.issue_refresh(user_id, sid, user_type)
        await self.store.create_session(user_id, sid, client_info, user_type)
        return Tokens(access_token=access_token, refresh_token=refresh_token)

    async def check_token(
        self, token: str, is_access_token: bool = True
    ) -> dict:
        """Token validation."""
        payload = (
            self.provider.decode_access(token)
            if is_access_token
            else self.provider.decode_refresh(token)
        )
        await self.store.check_sid(
            payload[auth.SUB],
            payload[auth.SID],
            payload[auth.TYPE],
            is_access_token,
        )
        return payload

    async def refresh_tokens(
        self, token: str, client_info: ClientInfo
    ) -> Tokens:
        """Refresh user tokens."""
        payload = await self.check_token(token, is_access_token=False)
        user_id = payload[auth.SUB]
        old_sid = payload[auth.SID]
        user_type = payload[auth.TYPE]
        new_sid = await self.store.refresh_sessions(
            user_id, old_sid, client_info, user_type
        )
        self.log.info(
            token_logs.TOKEN_REFRESHED_LOG,
            user_id,
        )
        return Tokens(
            access_token=self.provider.issue_access(
                user_id, new_sid, user_type
            ),
            refresh_token=self.provider.issue_refresh(
                user_id, new_sid, user_type
            ),
        )

    async def delete_sessions(
        self,
        user_id: str,
        sid: str | None = None,
        current_sid: str | None = None,
    ) -> None:
        """Delete sessions."""
        return await self.store.delete_sessions(user_id, sid, current_sid)

    async def delete_sessions_by_type(
        self,
        user_id: str,
        user_type: LoginType,
    ) -> int:
        """Delete all sessions of a specific type for a user."""
        return await self.store.delete_sessions_by_type(user_id, user_type)
