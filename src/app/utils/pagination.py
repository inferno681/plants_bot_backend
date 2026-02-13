from beanie import PydanticObjectId
from pydantic import BaseModel, Field, field_validator


class CursorPaginatorParams(BaseModel):
    """Query params for cursor-based pagination."""

    cursor: str | None = None
    limit: int = Field(10, ge=1, le=100)

    @field_validator('cursor', mode='after')
    def validate_cursor(cls, cursor):
        """Validate cursor."""
        if cursor:
            return PydanticObjectId(cursor)
        return cursor
