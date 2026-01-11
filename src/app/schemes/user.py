from pydantic import BaseModel


class WebAccountUpdate(BaseModel):
    """Web account update scheme."""

    language_code: str | None = None
