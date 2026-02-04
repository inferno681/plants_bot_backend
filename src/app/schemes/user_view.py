from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict

from app.schemes.user import Language


class TelegramUserView(BaseModel):
    id: PydanticObjectId
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None
    language_code: str | None = None


class WebUserView(BaseModel):
    id: PydanticObjectId
    email: str
    language: Language | None
    hashed_password: str


class UserSchedulerViewScheme(BaseModel):
    id: PydanticObjectId
    telegram_id: int | None = None
    email: str | None = None
    telegram_notifications_enabled: bool
    email_notifications_enabled: bool

    model_config = ConfigDict(from_attributes=True)
