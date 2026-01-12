from beanie import Document

from app.models.mixin import TimestampMixin


class Bot(TimestampMixin, Document):
    """Bot model."""

    name: str
    description: str | None = None
    is_active: bool = False

    class Settings:
        name = 'bots'
        use_state_management = True
