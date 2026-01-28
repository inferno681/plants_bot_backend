from pydantic import BaseModel


class TelegramLink(BaseModel):
    """Telegram linking scheme."""

    code: str
    qr: str
    link: str
    expires_at: int


class TelegramLinkRequest(BaseModel):
    """Link request scheme."""

    code: str
    telegram_id: int
