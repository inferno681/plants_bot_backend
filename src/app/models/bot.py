from app.models.base import BaseDocument


class Bot(BaseDocument):
    """Bot model."""

    name: str
    description: str | None = None
    is_active: bool = False

    class Settings(BaseDocument.Settings):
        """Settings for Bot model."""
        name = 'bots'
