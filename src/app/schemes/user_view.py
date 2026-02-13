from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.schemes.user import Language


class TelegramUserView(BaseModel):
    """Telegram User View scheme."""
    id: PydanticObjectId = Field(alias='_id')
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None
    language_code: str | None = None


class WebUserView(BaseModel):
    """Web User View scheme."""
    id: PydanticObjectId = Field(alias='_id')
    email: str
    language: Language | None = None
    hashed_password: str


class UserSchedulerViewScheme(BaseModel):
    """User Scheduler View scheme."""
    id: PydanticObjectId = Field(alias='_id')
    telegram_id: int | None = None
    email: str | None = None
    telegram_notifications_enabled: bool
    email_notifications_enabled: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
