from datetime import datetime
from enum import StrEnum, auto
from beanie import PydanticObjectId
from pydantic import model_validator, EmailStr
from pymongo import ASCENDING, IndexModel

from app.exceptions.auth import (
    MissingPasswordError,
    NoContactsError,
    OrphanContactFieldsError,
)
from app.models.base import BaseDocument
from app.schemes.user import Language


class UserStatus(StrEnum):
    """User statuses"""

    active = auto()
    merged = auto()
    deleted = auto()


class User(BaseDocument):
    """Core user model."""

    public_username: str | None = None
    language_code: Language | None = None
    status: UserStatus = UserStatus.active
    merged_into: PydanticObjectId | None = None
    merged_at: datetime | None = None

    email: EmailStr | None = None
    hashed_password: str | None = None
    email_verified_at: datetime | None = None

    telegram_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None

    telegram_notifications_enabled: bool = False
    email_notifications_enabled: bool = False

    class Settings(BaseDocument.Settings):
        name = 'users'
        indexes = [
            IndexModel(
                [('public_username', ASCENDING)],
                unique=True,
                partialFilterExpression={
                    'public_username': {'$type': 'string'}
                },
            ),
            IndexModel(
                [('email', ASCENDING)],
                unique=True,
                partialFilterExpression={'email': {'$type': 'string'}},
            ),
            IndexModel(
                [('telegram_id', ASCENDING)],
                unique=True,
                partialFilterExpression={'telegram_id': {'$type': 'number'}},
            ),
        ]

    @model_validator(mode='after')
    def ensure_contact(self) -> 'User':
        """Ensure that user has at least one contact method."""
        if self.email is None and self.telegram_id is None:
            raise NoContactsError()

        email_fields = (self.hashed_password, self.email_verified_at)
        orphan_email = self.email is None and any(
            field is not None for field in email_fields
        )
        if self.email is not None and not self.hashed_password:
            raise MissingPasswordError()

        tg_fields = (
            self.first_name,
            self.last_name,
            self.username,
            self.is_premium,
        )
        orphan_tg = self.telegram_id is None and any(
            field is not None for field in tg_fields
        )
        if orphan_email or orphan_tg:
            raise OrphanContactFieldsError()
        return self
