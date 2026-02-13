from pydantic import BaseModel


class UserSession(BaseModel):
    """User Session scheme."""
    uid: str
    sid: str
