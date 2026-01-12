from pydantic import BaseModel


class UserSession(BaseModel):
    uid: str
    sid: str
