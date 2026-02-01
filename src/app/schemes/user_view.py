from beanie import PydanticObjectId
from pydantic import BaseModel

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
