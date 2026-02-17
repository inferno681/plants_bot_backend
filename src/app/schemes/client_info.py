from pydantic import BaseModel


class ClientInfo(BaseModel):
    """Client Info scheme."""

    ip: str
    user_agent: str
