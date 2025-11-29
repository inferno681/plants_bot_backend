from typing import Generic, TypeVar

from pydantic import BaseModel, Field

model = TypeVar('model')


class CursorPaginatedResponse(BaseModel, Generic[model]):
    """Cursor-based paginated response model."""

    items: list[model]
    next_cursor: str | None = None
    has_more: bool = False
    limit: int = Field(..., ge=1, le=100)
