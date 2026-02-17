from enum import StrEnum, auto


class UserStatus(StrEnum):
    """User statuses"""

    active = auto()
    merged = auto()
    deleted = auto()
