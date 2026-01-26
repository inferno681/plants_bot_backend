from datetime import datetime
from typing import Annotated

from beanie import Indexed, PydanticObjectId

from app.models.base import BaseDocument


class WebAccount(BaseDocument):
    """Web authentication account."""

    user_id: Annotated[PydanticObjectId, Indexed()]

    email: Annotated[str, Indexed(unique=True)]
    hashed_password: str
    email_verified_at: datetime | None = None

    class Settings(BaseDocument.Settings):
        name = 'web_accounts'
