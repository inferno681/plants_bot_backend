from datetime import date, timedelta
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    field_validator,
    model_validator,
)

from app.exceptions.plant import PeriodCrossingError
from app.models.plant import FertilizingPeriod, WateringPeriod


class PlantStatsScheme(BaseModel):
    total: int
    watering_week: int
    attention: int
    tasks: list['PlantTaskScheme']


class PlantReadSchemeShort(BaseModel):

    id: str
    name: str
    image_url: str | None = None

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('id', mode='before')
    @classmethod
    def cast_id(cls, id):
        return str(id)

    @computed_field
    def status(self) -> str:
        today = date.today()
        if self.next_watering_at:
            if self.next_watering_at < today:
                return 'needs_watering'
            elif self.next_watering_at == today + timedelta(days=1):
                return 'watering_tomorrow'
            else:
                return 'healthy'
        return 'healthy'


class PlantTaskScheme(BaseModel):
    plant_id: str
    name: str
    date: date
    type: Literal['watering', 'watering_with_fertilizing']


class PlantReadScheme(PlantReadSchemeShort):

    id: str
    name: str
    scientific_name: str | None = None
    description: str | None = None
    image: str | None = None
    image_url: str | None = None

    warm_period: WateringPeriod | None = None
    cold_period: WateringPeriod | None = None
    fertilizing: FertilizingPeriod | None = None

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None

    model_config = ConfigDict(from_attributes=True)


class PlantUpdateScheme(BaseModel):

    name: str | None = None
    scientific_name: str | None = None
    description: str | None = None

    warm_period: WateringPeriod | None = None
    cold_period: WateringPeriod | None = None
    fertilizing: FertilizingPeriod | None = None


class PlantCreteScheme(BaseModel):
    """Create plant scheme."""

    name: str
    scientific_name: str | None = None
    description: str | None = None
    image: str | None = None
    image_url: str | None = None

    warm_period: WateringPeriod | None = None
    cold_period: WateringPeriod | None = None
    fertilizing: FertilizingPeriod | None = None

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None

    @model_validator(mode='after')
    def check_periods_do_not_overlap(self):
        if not self.warm_period or not self.cold_period:
            return self

        warm_start, warm_end = self.warm_period.as_period()
        cold_start, cold_end = self.cold_period.as_period()

        if warm_start <= cold_end and cold_start <= warm_end:
            raise PeriodCrossingError()

        return self
