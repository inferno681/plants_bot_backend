from beanie import Document
from pymongo import ASCENDING, IndexModel
from app.models.mixin import TimestampMixin


class User(TimestampMixin, Document):
    """Core user model."""

    public_username: str | None = None
    language_code: str | None = None

    class Settings:
        name = 'users'
        use_state_management = True
        indexes = [
            IndexModel(
                [('public_username', ASCENDING)],
                unique=True,
                partialFilterExpression={
                    'public_username': {'$type': 'string'}
                },
            )
        ]
