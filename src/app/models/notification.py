from datetime import datetime
from typing import Annotated

from beanie import Indexed, PydanticObjectId
from pydantic import model_validator

from app.enums import DeliveryChannel, NotificationStatus
from app.models.base import BaseDocument


class Notification(BaseDocument):
    """Notification model."""

    user_id: PydanticObjectId
    plant_id: PydanticObjectId
    telegram_message_id: int | None = None
    plant_name: str
    image: str | None = None

    channel: DeliveryChannel
    destination: str | int | None = None

    scheduled_for: datetime
    dedup_key: Annotated[str | None, Indexed(unique=True)]

    status: NotificationStatus = NotificationStatus.queued
    attempts: int = 0
    last_attempt_at: datetime | None = None
    enqueued_at: datetime | None = None

    def to_queue_dict(self) -> dict[str, str]:
        """Convert to queue dict."""
        return {
            'key': self.dedup_key or '',
            'user_id': str(self.user_id),
            'plant_id': str(self.plant_id),
            'name': self.plant_name,
            'image': self.image or '',
            'destination': str(self.destination) if self.destination else '',
        }

    @model_validator(mode='after')
    def set_dedup(self):
        """Set dedup."""
        if not self.dedup_key:
            self.dedup_key = ':'.join(
                str(self.user_id),
                str(self.plant_id),
                str(self.channel),
                self.scheduled_for.isoformat(),
            )
        return self

    class Settings(BaseDocument.Settings):
        """Settings for Notification model."""

        name = 'notifications'
