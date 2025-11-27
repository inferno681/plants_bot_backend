import hashlib
import hmac
import json
import logging
import time
import urllib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from redis.asyncio.client import Redis

from app.constants import (
    EXPIRED_TOKEN_MESSAGE,
    INIT_DATA_EXPIRED_MESSAGE,
    INVALID_AUTH_DATE_MESSAGE,
    INVALID_INIT_DATA_FORMAT_MESSAGE,
    INVALID_INIT_DATA_USER_DATA_MSG,
    INIT_DATA_MAX_AGE_SECONDS,
    INVALID_SIGNATURE_MESSAGE,
    INVALID_TOKEN_MESSAGE,
    LOGOUT_MESSAGE,
    MISSING_FIELDS_INIT_DATA_MSG,
    REQUIRED_INIT_DATA_FIELDS,
    UNREGISTERED_USER_MESSAGE,
    USER_ID_MISSED_INIT_DATA_MSG,
)
from app.log_messages import (
    AUTH_SERVICE_START_LOG,
    TOKEN_SERVICE_START_LOG,
    UNREGISTERED_USER_LOG,
    USER_LOGIN_LOG,
    USER_LOGOUT_LOG,
)
from app.models import User
from app.schemes import Tokens
from config import config


class TokenService:
    """Token service."""

    def __init__(self, redis: Redis):
        """Class constructor."""
        self.redis = redis
        self.log = logging.getLogger(__name__)
        self.log.info(TOKEN_SERVICE_START_LOG)

    async def get_token_redis(
        self, user_id: int, is_access_token: bool = True
    ) -> str | None:
        """Get token from Redis."""
        if is_access_token:
            key_word = 'access_token'
        else:
            key_word = 'refresh_token'
        return await self.redis.get(f'{key_word}:{user_id}')

    async def store_token_in_redis(
        self, user_id: int, access_token: str, refresh_token: str
    ) -> None:
        """Store access and refresh tokens in Redis."""
        async with self.redis.pipeline() as pipe:
            pipe.setex(
                f'access_token:{user_id}',
                config.service.access_token_ttl,
                access_token,
            )
            pipe.setex(
                f'refresh_token:{user_id}',
                config.service.refresh_token_ttl,
                refresh_token,
            )
            await pipe.execute()

    async def create_and_put_tokens(self, user_id: int) -> Tokens:
        """Create JWT access and refresh tokens and store them in Redis."""
        access_token = self.generate_jwt_token(user_id)
        refresh_token = self.generate_jwt_token(user_id, False)
        await self.store_token_in_redis(user_id, access_token, refresh_token)
        return Tokens(access_token=access_token, refresh_token=refresh_token)

    async def check_token(
        self, token: str, is_access_token: bool = True
    ) -> int:
        """Validate access token."""
        try:
            user_id = self.decode_jwt_token(token, is_access_token)['id']
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            )
        if is_access_token:
            redis_token = await self.get_token_redis(user_id)
        else:
            redis_token = await self.get_token_redis(user_id, False)
        if user_id and token == redis_token:
            return user_id
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MESSAGE,
        )

    def generate_jwt_token(
        self, user_id: int, is_access_token: bool = True
    ) -> str:
        """Generate JWT access token."""
        if is_access_token:
            exp = self._get_expiration_time(config.service.access_token_ttl)
            secret = config.secrets.verification_token_secret
        else:
            exp = self._get_expiration_time(config.service.refresh_token_ttl)
            secret = config.secrets.reset_token_secret
        payload = {
            'id': user_id,
            'exp': exp,
        }
        return jwt.encode(
            payload,
            secret.get_secret_value(),
            algorithm='HS256',
        )

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
            raise jwt.ExpiredSignatureError(EXPIRED_TOKEN_MESSAGE)
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError(INVALID_TOKEN_MESSAGE)

    async def delete_tokens(self, token: str) -> None:
        """Delete tokens from Redis."""
        user_id = await self.check_token(token)
        await self.redis.delete(
            f'access_token:{user_id}', f'refresh_token:{user_id}'
        )
        self.log.info(USER_LOGOUT_LOG, user_id)

    async def refresh_tokens(self, token: str) -> Tokens:
        """Refresh tokens."""
        user_id = await self.check_token(token, False)
        return await self.create_and_put_tokens(user_id)

    @staticmethod
    def _get_expiration_time(delta: int) -> float:
        """Generate expiration timestamp for access token."""
        return (
            datetime.now(timezone.utc) + timedelta(seconds=delta)
        ).timestamp()


class AuthService:
    """Auth service."""

    def __init__(self, redis: Redis):
        """Class constructor."""
        self.token_service = TokenService(redis)
        self.log = logging.getLogger(__name__)
        self.log.info(AUTH_SERVICE_START_LOG)

    def _parse_init_data(self, init_data: str) -> dict:
        try:
            parsed_raw = urllib.parse.parse_qs(init_data, strict_parsing=True)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=INVALID_INIT_DATA_FORMAT_MESSAGE,
            )
        return {k: v[0] for k, v in parsed_raw.items()}

    def _check_init_data(self, parsed: dict) -> int:
        if not all(key in parsed for key in REQUIRED_INIT_DATA_FIELDS):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=MISSING_FIELDS_INIT_DATA_MSG,
            )
        try:
            auth_date = int(parsed['auth_date'])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=INVALID_AUTH_DATE_MESSAGE,
            )

        if int(time.time()) - auth_date > INIT_DATA_MAX_AGE_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INIT_DATA_EXPIRED_MESSAGE,
            )

        try:
            user_data = json.loads(parsed['user'])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=INVALID_INIT_DATA_USER_DATA_MSG,
            )

        if 'id' not in user_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=USER_ID_MISSED_INIT_DATA_MSG,
            )
        return user_data['id']

    def verify_telegram_init_data(self, init_data: str) -> int:
        parsed = self._parse_init_data(init_data)
        user_id = self._check_init_data(parsed)

        hash_from_telegram = parsed['hash']

        signing_data = parsed.copy()
        signing_data.pop('hash')

        data_check_string = '\n'.join(
            f"{k}={v}" for k, v in sorted(signing_data.items())
        )

        secret_key = hmac.new(
            key=b'WebAppData',
            msg=config.secrets.bot_token.get_secret_value().encode(),
            digestmod=hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if calculated_hash != hash_from_telegram:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_SIGNATURE_MESSAGE,
            )
        return user_id

    async def login_user(self, init_data: str) -> Tokens:
        """Authenticate user and return JWT access and refresh tokens."""
        user_id = self.verify_telegram_init_data(init_data)
        user = await User.find_one(User.user_id == user_id)
        if not user:
            self.log.info(UNREGISTERED_USER_LOG, user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=UNREGISTERED_USER_MESSAGE,
            )
        self.log.info(USER_LOGIN_LOG, user_id)
        return await self.token_service.create_and_put_tokens(user_id)

    async def logout_user(self, token: str) -> str:
        """User logout."""
        await self.token_service.delete_tokens(token)
        return LOGOUT_MESSAGE


redis = Redis.from_url(
    config.redis_url,
    db=config.redis.db,
    decode_responses=config.redis.decode_responses,
    password=config.secrets.redis_password.get_secret_value(),
)
auth_service = AuthService(redis)
