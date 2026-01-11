import hashlib
import hmac
import json
import logging
import time
import urllib

from fastapi import HTTPException, status
from pwdlib import PasswordHash
from pymongo.errors import DuplicateKeyError
from redis.asyncio.client import Redis

from app.constants import auth
from app.exception import UserAlreadyExistsError
from app.log_messages import (
    AUTH_SERVICE_START_LOG,
    TOKEN_SERVICE_START_LOG,
    UNREGISTERED_USER_LOG,
    USER_LOGIN_LOG,
    USER_LOGOUT_ALL_LOG,
    USER_LOGOUT_LOG,
    USER_LOGOUT_OTHERS_LOG,
)
from app.models import TelegramAccount, User, WebAccount
from app.redis_service import redis
from app.schemes import Tokens
from config import config

DOC_USER = 459335857


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
        await self.token_service.delete_sessions(user_id=user_id, sid=sid)
        return auth.LOGOUT_MESSAGE

    async def logout_others_sessions(
        self, current_sid: str, user_id: int
    ) -> str:
        """Logout other user sessions."""
        await self.token_service.delete_sessions(
            user_id=user_id, current_sid=current_sid
        )
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
