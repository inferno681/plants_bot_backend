from enum import StrEnum, auto


class NotificationStatus(StrEnum):
    """Notification statuses."""

    queued = auto()
    processing = auto()
    sent = auto()
    retry_wait = auto()
    dead = auto()
    canceled = auto()


class DeliveryChannel(StrEnum):
    """Delivery Channel model."""

    telegram = auto()
    email = auto()
    web = auto()
