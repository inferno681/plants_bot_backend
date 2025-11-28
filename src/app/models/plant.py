from datetime import date, datetime
from enum import StrEnum, auto

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

from app.constants.general import DAYS_IN_MONTH, MONTHS_IN_YEAR


class MonthDay(BaseModel):
    """Class for date data."""

    day: int = Field(ge=1, le=DAYS_IN_MONTH)
    month: int = Field(ge=1, le=MONTHS_IN_YEAR)

    def as_date(self, year: int) -> date:
        """As date method."""
        return date(year, self.month, self.day)


class FrequencyType(StrEnum):
    """Frequency type enum."""

    weekly = auto()
    biweekly = auto()
    monthly = auto()


class WateringSchedule(BaseModel):
    """Model for watering schedule."""

    type: FrequencyType = FrequencyType.weekly
    weekday: set[int] | int | None = None
    monthday: int | None = None
    note: str | None = None


class WateringPeriod(BaseModel):
    """Model for watering periods."""

    start: MonthDay | None = None
    end: MonthDay | None = None
    schedule: WateringSchedule | None = None
    note: str | None = None


class FertilizingType(StrEnum):
    """Fertilizing frequency types enum."""

    days = auto()
    weeks = auto()
    months = auto()


class FertilizingPeriod(BaseModel):
    """Fertilizing period model."""

    start: MonthDay | None = None
    end: MonthDay | None = None
    frequency: int | None = None
    type: FertilizingType = FertilizingType.days
    note: str | None = None


class Plant(Document):
    """Plant model."""

    user_id: int
    name: str
    scientific_name: str | None = None
    description: str | None = None
    image: str | None = None
    storage_key: str | None = None

    warm_period: WateringPeriod | None = Field(default_factory=WateringPeriod)
    cold_period: WateringPeriod | None = Field(default_factory=WateringPeriod)
    fertilizing: FertilizingPeriod | None = Field(
        default_factory=FertilizingPeriod
    )

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    async def get_plants(cls, user_id: int) -> list['Plant']:
        return await cls.find(cls.user_id == user_id).sort('+_id').to_list()

    @classmethod
    async def get_plant_by_id(
        cls, plant_id: str, user_id: int
    ) -> 'Plant | None':
        return await cls.find_one(
            Plant.id == PydanticObjectId(plant_id), Plant.user_id == user_id
        )

    class Settings:
        name = 'plants'
