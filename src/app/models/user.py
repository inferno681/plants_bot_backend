from pymongo import ASCENDING, IndexModel

from app.models.base import BaseDocument


class User(BaseDocument):
    """Core user model."""

    public_username: str | None = None
    language_code: str | None = None

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
