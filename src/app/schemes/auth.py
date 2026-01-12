from fastapi import HTTPException, status
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.constants.auth import (
    INVALID_INIT_DATA_FORMAT_MESSAGE,
    PASSWORD_CHANGE_SAME_AS_OLD,
)
from app.schemes.validator import PasswordStr


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


class InitData(BaseModel):
    init_data: str = Field(
        ..., description='Signed initData string from Telegram WebApp'
    )

    @field_validator('init_data')
    def validate_format(cls, init_data: str):
        if not init_data or '&' not in init_data or '=' not in init_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=INVALID_INIT_DATA_FORMAT_MESSAGE,
            )
        return init_data


class RefreshRequest(BaseModel):
    """Refresh token request scheme."""

    refresh_token: str


class WebAccountLogin(BaseModel):
    """Web account login scheme."""

    email: EmailStr
    password: PasswordStr


class WebAccountRegistration(WebAccountLogin):
    """Web account registration scheme."""

    language_code: str | None = None


class WebAccountPasswordChange(BaseModel):
    """Web account password change scheme."""

    old_password: PasswordStr
    new_password: PasswordStr

    @model_validator(mode='after')
    def check_diff(self):
        if self.old_password == self.new_password:
            raise ValueError(PASSWORD_CHANGE_SAME_AS_OLD)
        return self


class TelegramAccountBase(BaseModel):
    """Telegram account scheme."""

    telegram_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None
    language_code: str | None = None
