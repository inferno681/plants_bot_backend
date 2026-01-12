from pydantic import BaseModel


class ClientInfo(BaseModel):
    ip: str
    ua: str
