from pymongo import ASCENDING, IndexModel

from app.models.base import BaseDocument
from app.schemes.user import Language


class User(BaseDocument):
    """Core user model."""

    public_username: str | None = None
    language_code: Language | None = None

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
