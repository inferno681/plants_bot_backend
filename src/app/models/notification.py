from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated

from beanie import Indexed, PydanticObjectId
from pydantic import model_validator

from app.models.base import BaseDocument


class NotificationStatus(StrEnum):
    """Notification statuses."""

    queued = auto()
    processing = auto()
    sent = auto()
    retry_wait = auto()
    dead = auto()
    canceled = auto()


class DeliveryChannel(StrEnum):
    telegram = auto()
    email = auto()
    web = auto()


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

    @model_validator(mode='after')
    def set_dedup(self):
        if not self.dedup_key:
            self.dedup_key = ':'.join(
                str(self.user_id),
                str(self.plant_id),
                str(self.channel),
                self.scheduled_for.isoformat(),
            )
        return self

    class Settings(BaseDocument.Settings):
        name = 'notifications'
