from pydantic import BaseModel


class TokenServiceConfig(BaseModel):
    """Token Service Config scheme."""
    access_secret: str
    refresh_secret: str
    access_ttl: int
    refresh_ttl: int
    algorithm: str = 'HS256'
    max_sessions: int


class Tokens(BaseModel):
    """Tokens scheme."""
    access_token: str
    refresh_token: str


class WebTokens(BaseModel):
    """Web Tokens scheme."""
    access_token: str


class RefreshRequest(BaseModel):
    """Refresh token request scheme."""

    refresh_token: str


class RefreshRequestCookie(BaseModel):
    """Refresh Request Cookie scheme."""
    refresh_token: str
    csrf: str
