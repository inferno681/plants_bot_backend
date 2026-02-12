import secrets
from datetime import datetime, timezone
from logging import getLogger

from beanie import PydanticObjectId
from fastapi import FastAPI, Request
from redis.asyncio import Redis

from app.constants.email import (
    CONFIRM_TOKEN_PREFIX,
    CONFIRM_USER_PREFIX,
    CONFIRMATION_EMAIL_LINK,
    EMAIL_CONFIRMATION_TTL,
    TOKEN_LENGTH,
)
from app.exceptions.auth import UserNotFoundError
from app.exceptions.email import (
    EmailAlreadyConfirmedError,
    EmailNotSetError,
    InvalidTokenError,
    TokenAlreadyUsedError,
)
from app.logs.email import (
    CONFIRM_EMAIL_LOG,
    CONFIRMATION_EMAIL_BAD_REQUEST_LOG,
    CONFIRMATION_EMAIL_REQUEST_LOG,
    EMAIL_SERVICE_START_LOG,
)
from app.models import EmailConfirmation, User
from app.schemes import ClientInfo
from app.tasks import send_confirmation_email


class EmailService:
    """Email service."""

    def __init__(self, redis: Redis):
        """Email service initialization."""
        self.redis = redis
        self.log = getLogger(__name__)
        self.log.info(EMAIL_SERVICE_START_LOG)

    async def send_confirmation_email(
        self, user_id: PydanticObjectId, client_info: ClientInfo
    ) -> None:
        """Send confirmation email to user."""
        user = await User.find_one(User.id == user_id)
        if not user:
            raise UserNotFoundError()
        if not user.email:
            self.log.warning(
                CONFIRMATION_EMAIL_BAD_REQUEST_LOG,
                str(user_id),
            )
            raise EmailNotSetError()
        if user.email_verified_at:
            raise EmailAlreadyConfirmedError()
        token = secrets.token_urlsafe(TOKEN_LENGTH)
        email_confirmation = EmailConfirmation(
            user_id=user_id,
            email=user.email,
            token=token,
            ip=client_info.ip,
            user_agent=client_info.ua,
        )
        await email_confirmation.insert()
        old_token = await self.redis.get(f'{CONFIRM_USER_PREFIX}{user_id}')

        pipe = self.redis.pipeline()

        if old_token:
            pipe.delete(f'{CONFIRM_TOKEN_PREFIX}{old_token}')

        pipe.set(
            f'{CONFIRM_TOKEN_PREFIX}{token}',
            str(user_id),
            ex=EMAIL_CONFIRMATION_TTL,
        )

        pipe.set(
            f'{CONFIRM_USER_PREFIX}{user_id}',
            token,
            ex=EMAIL_CONFIRMATION_TTL,
        )

        await pipe.execute()

        self.log.info(
            CONFIRMATION_EMAIL_REQUEST_LOG,
            str(user_id),
        )
        await send_confirmation_email.kiq(
            to_email=user.email,
            confirmation_link=CONFIRMATION_EMAIL_LINK.format(token=token),
            language=user.language,
        )

    async def confirm_email(self, token: str, client_info: ClientInfo) -> None:
        """Confirm user's email using token."""
        user_id, email_confirmation = await self._validate_confirmation(token)

        user = await User.find_one(User.id == user_id)
        if not user:
            raise UserNotFoundError()
        if user.email_verified_at:
            raise EmailAlreadyConfirmedError()
        user.email_verified_at = datetime.now(timezone.utc)
        await user.save_changes()

        email_confirmation.is_used = True
        email_confirmation.confirmed_ip = client_info.ip
        email_confirmation.confirmed_user_agent = client_info.ua
        await email_confirmation.save_changes()

        pipe = self.redis.pipeline()
        pipe.unlink(f'{CONFIRM_TOKEN_PREFIX}{token}')
        pipe.unlink(f'{CONFIRM_USER_PREFIX}{user_id}')
        await pipe.execute()
        self.log.info(CONFIRM_EMAIL_LOG, str(user_id))

    async def _validate_confirmation(
        self, token: str
    ) -> tuple[PydanticObjectId, EmailConfirmation]:

        user_id = await self.redis.get(f'{CONFIRM_TOKEN_PREFIX}{token}')
        if not user_id:
            raise InvalidTokenError()

        user_id = PydanticObjectId(user_id)

        email_confirmation = await EmailConfirmation.find_one(
            EmailConfirmation.token == token,
            EmailConfirmation.user_id == user_id,
        )
        if not email_confirmation:
            raise InvalidTokenError()

        if email_confirmation.is_used:
            raise TokenAlreadyUsedError()

        return user_id, email_confirmation


def init_email_service(
    app: FastAPI,
    redis: Redis,
) -> None:
    """Create EmailService once and store on app.state."""
    app.state.email_service = EmailService(
        redis=redis,
    )


def get_email_service(request: Request) -> EmailService:
    """FastAPI dependency for UserService."""
    return request.app.state.email_service
