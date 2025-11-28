from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.constants.auth import INVALID_INIT_DATA_FORMAT_MESSAGE


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
