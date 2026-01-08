from typing import Annotated
from beanie import Document, Indexed, PydanticObjectId
from app.models.mixin import TimestampMixin


class WebAccount(TimestampMixin, Document):
    """Web authentication account."""

    user_id: Annotated[PydanticObjectId, Indexed()]

    email: Annotated[str, Indexed(unique=True)]
    hashed_password: str

    class Settings:
        name = 'web_accounts'
        use_state_management = True
