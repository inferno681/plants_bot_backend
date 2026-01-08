from typing import Annotated

from beanie import Document, Indexed, PydanticObjectId
from app.models.mixin import TimestampMixin


class TelegramAccount(TimestampMixin, Document):
    """Telegram auth/account data."""

    user_id: Annotated[PydanticObjectId, Indexed()]

    telegram_id: Annotated[int, Indexed(unique=True)]
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None

    class Settings:
        name = 'telegram_accounts'
        use_state_management = True
