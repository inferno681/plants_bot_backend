from pydantic import BaseModel


class MessageScheme(BaseModel):
    """Message scheme."""
    message: str
