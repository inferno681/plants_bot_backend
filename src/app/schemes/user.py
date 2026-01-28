from enum import StrEnum, auto

from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr


class Language(StrEnum):
    """Supported languages."""

    en = auto()
    ru = auto()


class WebAccountUpdate(BaseModel):
    """Web account update scheme."""

    language_code: Language | None = None


class TelegramUser(BaseModel):
    """Telegram user scheme."""

    user_id: PydanticObjectId

    telegram_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None


class WebUser(BaseModel):
    """Web user scheme."""

    user_id: PydanticObjectId
    email: EmailStr


class WebUserInfo(BaseModel):
    """Web user info scheme."""

    public_username: str | None = None
    email: EmailStr | None = None
    email_verified: bool = False
    telegram_id: int | None = None
    telegram_linked: bool = False
