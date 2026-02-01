from datetime import datetime
from enum import StrEnum, auto

from beanie import PydanticObjectId
from pymongo import ASCENDING, IndexModel

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

    web_notifications_enabled: bool = False
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
            )
        ]
