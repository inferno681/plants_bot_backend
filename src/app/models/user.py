from datetime import datetime

from beanie import Document


class User(Document):
    """User model."""

    user_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    full_name: str
    language_code: str | None = None
    is_premium: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Settings:
        name = 'users'
