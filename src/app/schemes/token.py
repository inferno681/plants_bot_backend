from pydantic import BaseModel


class TokenServiceConfig(BaseModel):
    access_secret: str
    refresh_secret: str
    access_ttl: int
    refresh_ttl: int
    algorithm: str = 'HS256'
    max_sessions: int


class Tokens(BaseModel):
    access_token: str
    refresh_token: str


class WebTokens(BaseModel):
    access_token: str


class RefreshRequest(BaseModel):
    """Refresh token request scheme."""

    refresh_token: str


class RefreshRequestCookie(BaseModel):
    refresh_token: str
    csrf: str
