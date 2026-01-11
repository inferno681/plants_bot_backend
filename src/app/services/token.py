import time
from datetime import datetime, timezone
from importlib.resources import files
from logging import getLogger
from typing import Awaitable, cast
from uuid import uuid4

import jwt
from redis.asyncio.client import Redis
from redis.commands.core import AsyncScript

from app.constants import auth
from app.exception import InvalidTokenError
from app.logs import token as token_logs
from app.redis_service import redis
from app.schemes import Tokens
from config import config

SUB = 'sub'
EXP = 'exp'
SID = 'sid'
IAT = 'iat'

logger = getLogger(__name__)


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
        self.access_secret = access_secret
        self.refresh_secret = refresh_secret
        self.access_ttl = access_ttl
        self.refresh_ttl = refresh_ttl
        self.algorithm = algorithm
        self.log = logger
        self.log.info(token_logs.TOKEN_PROVIDER_START_LOG)

    def issue_access(self, user_id: str, sid: str) -> str:
        """Issue access token."""
        now = int(datetime.now(timezone.utc).timestamp())
        return jwt.encode(
            {
                SUB: user_id,
                EXP: now + self.access_ttl,
                SID: sid,
                IAT: now,
            },
            self.access_secret,
            algorithm=self.algorithm,
        )

    def issue_refresh(self, user_id: str, sid: str) -> str:
        """Issue refresh token."""
        now = int(datetime.now(timezone.utc).timestamp())
        return jwt.encode(
            {
                SUB: user_id,
                EXP: now + self.refresh_ttl,
                SID: sid,
                IAT: now,
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
            raise InvalidTokenError(auth.EXPIRED_TOKEN_MESSAGE)
        except jwt.InvalidTokenError as exc:
            self.log.warning(
                token_logs.INVALID_ACCESS_TOKEN_LOG, type(exc).__name__
            )
            raise InvalidTokenError(auth.INVALID_TOKEN_MESSAGE)

    def decode_refresh(self, token: str) -> dict:
        """Decode refresh token."""
        try:
            return jwt.decode(
                token,
                self.refresh_secret,
                algorithms=[self.algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError(auth.EXPIRED_TOKEN_MESSAGE)
        except jwt.InvalidTokenError as exc:
            self.log.warning(
                token_logs.INVALID_REFRESH_TOKEN_LOG, type(exc).__name__
            )
            raise InvalidTokenError(auth.INVALID_TOKEN_MESSAGE)


class SessionStore:
    """Session store interface."""

    def __init__(self, redis: Redis, refresh_ttl: int):
        """Class constructor."""
        self.redis = redis
        self.refresh_ttl = refresh_ttl
        self.log = logger
        self.refresh_script: AsyncScript
        self.session_create_script: AsyncScript
        self.load_lua_scripts(
            refresh_filename='token_refresh.lua',
            session_create_filename='session_create.lua',
        )
        self.max_sessions = config.service.max_sessions_per_user
        self.log.info(token_logs.SESSION_STORE_START_LOG)

    def load_lua_scripts(
        self, refresh_filename: str, session_create_filename: str
    ) -> None:
        """Load Lua scripts into Redis."""
        self.refresh_script = self._load_script(refresh_filename)
        self.log.info(
            token_logs.TOKEN_REFRESH_SCRIPT_LOADED_LOG, self.refresh_script.sha
        )
        self.session_create_script = self._load_script(session_create_filename)
        self.log.info(
            token_logs.SESSION_CREATE_SCRIPT_LOADED_LOG,
            self.session_create_script.sha,
        )

    async def create_session(
        self, user_id: str, sid: str, ip: str, user_agent: str
    ) -> None:
        """Store access and refresh sid in Redis."""
        dropped = await self.session_create_script(
            keys=[f'{auth.USER_SESSIONS_PREFIX}{user_id}'],
            args=[
                self.max_sessions,
                self.refresh_ttl,
                int(time.time()),
                sid,
                ip or auth.UNKNOWN_LITERAL,
                user_agent or auth.UNKNOWN_LITERAL,
                user_id,
            ],
        )

        if dropped:
            for session in dropped:
                self.log.info(
                    token_logs.SESSIONS_EVICTED_LOG,
                    user_id,
                    session['sid'],
                    session['ip'],
                    session['user_agent'],
                    session['created_at'],
                    session['ttl'],
                )

    async def check_sid(self, user_id: str, sid: str) -> bool:
        """Check sid in storage."""

        stored_uid = await cast(
            'Awaitable[str | None]',
            self.redis.hget(f'{auth.SESSION_PREFIX}{sid}', 'uid'),
        )
        if not stored_uid or str(stored_uid) != str(user_id):
            return False
        return True

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

        await self._delete_batch(key, raw_sids, session_keys)
        self.log.info(log_text, user_id)

    async def refresh_sessions(
        self,
        user_id: str,
        sid: str,
        ip: str,
        user_agent: str,
    ) -> str:
        """Refresh sids in storage."""

        new_sid = str(uuid4())

        try:
            script_result = await self.refresh_script(
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
                    ip or auth.UNKNOWN_LITERAL,
                    user_agent or auth.UNKNOWN_LITERAL,
                ],
            )
        except Exception as exc:
            self.log.warning(
                token_logs.REFRESH_REJECTED_LOG,
                user_id,
                type(exc).__name__,
            )
            raise InvalidTokenError(auth.INVALID_TOKEN_MESSAGE)
        if isinstance(script_result, dict) and 'err' in script_result:
            self._handle_refresh_error(
                script_result['err'], user_id, ip, user_agent
            )
        return new_sid

    def _load_script(self, filename: str) -> AsyncScript:
        return self.redis.register_script(
            files('app.redis_service.scripts').joinpath(filename).read_text()
        )

    def _handle_refresh_error(
        self, err: str, user_id: str, ip: str, user_agent: str
    ) -> None:
        if err == 'SESSION_NOT_FOUND':
            self.log.error(
                token_logs.REFRESH_REPLAY_DETECTED_LOG,
                user_id,
                ip,
                user_agent,
            )
        elif err == 'INVALID_OWNER':
            self.log.error(
                token_logs.REFRESH_INVALID_OWNER_LOG,
                user_id,
                ip,
                user_agent,
            )
        else:
            self.log.error(
                token_logs.REFRESH_UNKNOWN_ERROR_LOG,
                err,
            )
        raise InvalidTokenError(auth.INVALID_TOKEN_MESSAGE)

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

    async def _delete_batch(
        self,
        key: str,
        raw_sids: list[str],
        session_keys: list[str],
    ) -> None:
        """Delete batch of sessions."""
        async with self.redis.pipeline() as pipe:
            pipe.unlink(*session_keys)
            pipe.zrem(key, *raw_sids)
            await pipe.execute()


class TokenService:
    """Token service."""

    def __init__(self, provider: TokenProvider, store: SessionStore):
        """Class constructor."""
        self.provider = provider
        self.store = store
        self.log = logger
        self.log.info(token_logs.TOKEN_SERVICE_START_LOG)

    async def create_and_put_tokens(
        self, user_id: str, ip: str, user_agent: str
    ) -> Tokens:
        """Create JWT access and refresh tokens and store them in Redis."""
        sid = str(uuid4())
        access_token = self.provider.issue_access(user_id, sid)
        refresh_token = self.provider.issue_refresh(user_id, sid)
        await self.store.create_session(user_id, sid, ip, user_agent)
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
        if not await self.store.check_sid(payload[SUB], payload[SID]):
            raise InvalidTokenError(auth.INVALID_TOKEN_MESSAGE)

        return payload

    async def refresh_tokens(
        self,
        token: str,
        ip: str,
        user_agent: str,
    ) -> Tokens:
        """Refresh user tokens."""
        payload = await self.check_token(token, is_access_token=False)
        user_id = payload[SUB]
        old_sid = payload[SID]
        new_sid = await self.store.refresh_sessions(
            user_id, old_sid, ip, user_agent
        )
        self.log.info(
            token_logs.TOKEN_REFRESHED_LOG,
            user_id,
        )
        return Tokens(
            access_token=self.provider.issue_access(user_id, new_sid),
            refresh_token=self.provider.issue_refresh(user_id, new_sid),
        )

    async def delete_sessions(
        self,
        user_id: str,
        sid: str | None = None,
        current_sid: str | None = None,
    ) -> None:
        """Delete sessions."""
        return await self.store.delete_sessions(user_id, sid, current_sid)


token_service = TokenService(
    provider=TokenProvider(
        access_secret=config.secrets.access_token_secret.get_secret_value(),
        refresh_secret=config.secrets.refresh_token_secret.get_secret_value(),
        access_ttl=config.service.access_token_ttl,
        refresh_ttl=config.service.refresh_token_ttl,
    ),
    store=SessionStore(
        redis=redis,
        refresh_ttl=config.service.refresh_token_ttl,
    ),
)
