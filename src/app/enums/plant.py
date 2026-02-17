from enum import StrEnum, auto


class FrequencyType(StrEnum):
    """Frequency type enum."""

    weekly = auto()
    biweekly = auto()
    monthly = auto()


class FertilizingType(StrEnum):
    """Fertilizing frequency types enum."""

    days = auto()
    weeks = auto()
    months = auto()
