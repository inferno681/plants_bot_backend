from beanie import PydanticObjectId
from pydantic import BaseModel


class WebAccountUpdate(BaseModel):
    """Web account update scheme."""

    language_code: str | None = None


class TelegramUser(BaseModel):
    """Telegram user scheme."""

    user_id: PydanticObjectId

    telegram_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None
