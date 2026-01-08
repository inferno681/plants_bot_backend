import hashlib
import hmac
import json
import logging
from importlib.resources import files
from pymongo.errors import DuplicateKeyError
import time
import urllib
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from fastapi import HTTPException, status
from redis.asyncio.client import Redis
from pwdlib import PasswordHash

from app.constants import auth
from app.exception import UserAlreadyExistsError
from app.log_messages import (
    AUTH_SERVICE_START_LOG,
    TOKEN_SERVICE_START_LOG,
    UNREGISTERED_USER_LOG,
    USER_LOGIN_LOG,
    USER_LOGOUT_LOG,
    USER_LOGOUT_OTHERS_LOG,
)
from app.models import User, WebAccount, TelegramAccount
from app.redis_service import redis
from app.schemes import Tokens
from redis.exceptions import NoScriptError
from config import config

DOC_USER = 459335857


class TokenService:
    """Token service."""

    def __init__(self, redis: Redis):
        """Class constructor."""
        self.redis = redis
        self.log = logging.getLogger(__name__)
        self.refresh_lua_sha: str | None = None
        self.refresh_lua = (
            files('app.redis_service.scripts')
            .joinpath('token_refresh.lua')
            .read_text()
        )
        self.log.info(TOKEN_SERVICE_START_LOG)

    async def load_lua_scripts(self) -> None:
        self.refresh_lua_sha = await self.redis.script_load(self.refresh_lua)
        self.log.info("Refresh Lua script loaded: %s", self.refresh_lua_sha)

    def generate_jwt_token(
        self, user_id: int, sid: str, is_access_token: bool = True
    ) -> str:
        """Generate JWT tokens."""
        if is_access_token:
            exp = self._get_expiration_time(config.service.access_token_ttl)
            secret = config.secrets.verification_token_secret
        else:
            exp = self._get_expiration_time(config.service.refresh_token_ttl)
            secret = config.secrets.reset_token_secret
        payload = {
            'sub': user_id,
            'exp': exp,
            'sid': sid,
        }
        return jwt.encode(
            payload,
            secret.get_secret_value(),
            algorithm='HS256',
        )

    async def create_and_put_tokens(
        self, user_id: int, ip: str, user_agent: str
    ) -> Tokens:
        """Create JWT access and refresh tokens and store them in Redis."""
        sid = str(uuid4())
        access_token = self.generate_jwt_token(user_id, sid)
        refresh_token = self.generate_jwt_token(user_id, sid, False)
        await self.store_sid_in_redis(user_id, sid, ip, user_agent)
        return Tokens(access_token=access_token, refresh_token=refresh_token)

    async def store_sid_in_redis(
        self, user_id: int, sid: str, ip: str, user_agent: str
    ) -> None:
        """Store access and refresh sid in Redis."""
        sessions_key = f'user_sessions:{user_id}'

        async with self.redis.pipeline() as pipe:

            pipe.hsetex(
                f'session:{sid}',
                ex=config.service.refresh_token_ttl,
                mapping={
                    'uid': user_id,
                    'ip': ip or 'uknown',
                    'user_agent': user_agent or 'uknown',
                    'created_at': int(time.time()),
                },
            )
            pipe.zadd(
                sessions_key,
                {sid: int(time.time())},
            )

            await pipe.execute()

    async def check_token(
        self, token: str, is_access_token: bool = True
    ) -> dict:
        """Token validation."""
        try:
            payload = self.decode_jwt_token(token, is_access_token)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            )
        sid = payload.get('sid')
        user_id = payload.get('sub')

        if not sid or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth.INVALID_TOKEN_MESSAGE,
            )

        stored_uid = await self.redis.hget(f'session:{sid}', 'uid')
        if not stored_uid or int(stored_uid) != int(user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth.INVALID_TOKEN_MESSAGE,
            )
        return payload

    def decode_jwt_token(
        self, token: str, is_access_token: bool = True
    ) -> dict:
        """Decode JWT token."""
        if is_access_token:
            secret = config.secrets.verification_token_secret
        else:
            secret = config.secrets.reset_token_secret
        try:
            return jwt.decode(
                token,
                secret.get_secret_value(),
                algorithms=['HS256'],
            )
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError(auth.EXPIRED_TOKEN_MESSAGE)
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError(auth.INVALID_TOKEN_MESSAGE)

    async def delete_sid(self, sid: str, user_id: int) -> None:
        """Delete sid from Redis."""
        async with self.redis.pipeline() as pipe:
            pipe.delete(f'session:{sid}')
            pipe.zrem(f'user_sessions:{user_id}', sid)
            await pipe.execute()
        self.log.info(USER_LOGOUT_LOG, user_id)

    async def delete_sids(self, user_id: int, current_sid: str) -> None:
        """Delete other sids from Redis."""
        sids = await self.redis.zrange(f'user_sessions:{user_id}', 0, -1)
        async with redis.pipeline() as pipe:
            for sid in sids:
                if sid != current_sid:
                    pipe.delete(f'session:{sid}')
                    pipe.zrem(f'user_sessions:{user_id}', sid)
            await pipe.execute()
        self.log.info(USER_LOGOUT_OTHERS_LOG, user_id)

    async def refresh_tokens(
        self,
        token: str,
        ip: str,
        user_agent: str,
    ) -> Tokens:
        payload = await self.check_token(token, is_access_token=False)

        old_sid = payload["sid"]
        user_id = str(payload["sub"])
        new_sid = str(uuid4())
        now = int(time.time())

        try:
            await self.redis.evalsha(
                self.refresh_lua_sha,
                keys=[
                    f"session:{old_sid}",
                    f"user_sessions:{user_id}",
                ],
                args=[
                    old_sid,
                    new_sid,
                    user_id,
                    config.service.refresh_token_ttl,
                    now,
                    ip or "unknown",
                    user_agent or "unknown",
                ],
            )
        except NoScriptError:
            self.refresh_lua_sha = await self.redis.script_load(
                self.refresh_lua
            )
            await self.redis.evalsha(
                self.refresh_lua_sha,
                keys=[
                    f"session:{old_sid}",
                    f"user_sessions:{user_id}",
                ],
                args=[
                    old_sid,
                    new_sid,
                    user_id,
                    config.service.refresh_token_ttl,
                    now,
                    ip or "unknown",
                    user_agent or "unknown",
                ],
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth.INVALID_TOKEN_MESSAGE,
            )

        access_token = self.generate_jwt_token(user_id, new_sid)
        refresh_token = self.generate_jwt_token(user_id, new_sid, False)

        return Tokens(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @staticmethod
    def _get_expiration_time(delta: int) -> int:
        """Generate expiration timestamp for access token."""
        return int(
            (datetime.now(timezone.utc) + timedelta(seconds=delta)).timestamp()
        )


class AuthService:
    """Auth service."""

    def __init__(self, redis: Redis):
        """Class constructor."""
        self.token_service = TokenService(redis)
        self.log = logging.getLogger(__name__)
        self.password_hasher = PasswordHash.recommended()
        self.log.info(AUTH_SERVICE_START_LOG)

    def verify_telegram_init_data(self, init_data: str) -> int:
        parsed = self._parse_init_data(init_data)
        user_id = self._check_init_data(parsed)

        calculated_hash = hmac.new(
            hmac.new(
                key=b'WebAppData',
                msg=config.secrets.bot_token.get_secret_value().encode(),
                digestmod=hashlib.sha256,
            ).digest(),
            '\n'.join(
                f'{key}={value}'
                for key, value in sorted(
                    (key, value)
                    for key, value in parsed.items()
                    if key != 'hash'
                )
            ).encode(),
            hashlib.sha256,
        ).hexdigest()

        if calculated_hash != parsed['hash']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth.INVALID_SIGNATURE_MESSAGE,
            )

        return user_id

    async def login_telegram_user(self, init_data: str) -> Tokens:
        """Authenticate telegram user and return JWT tokens."""
        user_id = self.verify_telegram_init_data(init_data)
        user = await User.find_one(User.user_id == user_id)
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=auth.UNREGISTERED_USER_MESSAGE,
            )
        self.log.info(USER_LOGIN_LOG, user_id)
        return await self.token_service.create_and_put_tokens(user_id)

    async def refresh_user_tokens(self, refresh_token: str) -> Tokens:
        """Refresh user tokens."""
        return await self.token_service.refresh_tokens(refresh_token)

    async def login_doc(self, password: str) -> Tokens:
        """Login for documentation access."""
        if password != '123':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid documentation password',
            )
        user = await User.find_one(User.user_id == DOC_USER)
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, DOC_USER)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=auth.UNREGISTERED_USER_MESSAGE,
            )
        self.log.info(USER_LOGIN_LOG, DOC_USER)
        return await self.token_service.create_and_put_tokens(DOC_USER)

    async def logout_user(self, sid: str, user_id: int) -> str:
        """User logout."""
        await self.token_service.delete_sid(sid, user_id)
        return auth.LOGOUT_MESSAGE

    async def logout_others_sessions(
        self, current_sid: str, user_id: int
    ) -> str:
        """Logout other user sessions."""
        await self.token_service.delete_sids(user_id, current_sid)
        return auth.LOGOUT_OTHERS_MESSAGE

    async def registration_web_user(self, email: str, password: str, session):
        """User registration."""
        user = User()
        await user.insert(session=session)

        try:
            web_account = WebAccount(
                user_id=user.id,
                email=email,
                hashed_password=self.password_hasher.hash(password),
            )
            await web_account.insert(session=session)

        except DuplicateKeyError:
            raise UserAlreadyExistsError()

        return user

    async def registration_telegram_user(
        self,
    ):
        """Telegram user registration."""
        pass

    def _parse_init_data(self, init_data: str) -> dict:
        try:
            parsed_raw = urllib.parse.parse_qs(init_data, strict_parsing=True)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=auth.INVALID_INIT_DATA_FORMAT_MESSAGE,
            )
        return {key: value[0] for key, value in parsed_raw.items()}

    def _check_init_data(self, parsed: dict) -> int:
        errors = []

        missing = [
            field
            for field in auth.REQUIRED_INIT_DATA_FIELDS
            if field not in parsed
        ]
        if missing:
            errors.append(
                auth.MISSED_FIELDS_MSG.format(fields=', '.join(missing))
            )

        auth_date = None
        try:
            auth_date = int(parsed.get('auth_date', 0))
        except ValueError:
            errors.append(auth.INVALID_AUTH_DATE_MESSAGE)

        if auth_date is not None:
            if int(time.time()) - auth_date > config.service.init_data_max_age:
                errors.append(auth.INIT_DATA_EXPIRED_MESSAGE)
        try:
            user_data = json.loads(parsed.get('user', '{}'))
        except Exception:
            errors.append(auth.INVALID_INIT_DATA_USER_DATA_MSG)
        if not user_data:
            errors.append(auth.NO_USER_DATA_MSG)
        user_id = user_data.get('id')
        if not user_id:
            errors.append(auth.USER_ID_MISSED_INIT_DATA_MSG)

        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=errors,
            )

        return user_id


auth_service = AuthService(redis)
