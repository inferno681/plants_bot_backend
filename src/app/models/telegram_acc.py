from typing import Annotated

from beanie import Indexed, PydanticObjectId

from app.models.base import BaseDocument


class TelegramAccount(BaseDocument):
    """Telegram auth/account data."""

    user_id: Annotated[PydanticObjectId, Indexed()]

    telegram_id: Annotated[int, Indexed(unique=True)]
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None

    class Settings(BaseDocument.Settings):
        name = 'telegram_accounts'
