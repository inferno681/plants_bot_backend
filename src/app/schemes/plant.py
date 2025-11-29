from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from app.models.plant import FertilizingPeriod, WateringPeriod


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
