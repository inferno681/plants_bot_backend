from beanie import PydanticObjectId
from pydantic import BaseModel


class BotBase(BaseModel):
    """Bot scheme."""

    id: PydanticObjectId
    name: str
    description: str | None = None
    is_active: bool = False
