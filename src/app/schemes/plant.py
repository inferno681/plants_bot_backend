from datetime import date

from pydantic import BaseModel

from app.models.plant import FertilizingPeriod, WateringPeriod


class PlantReadScheme(BaseModel):
    id: str
    name: str
    scientific_name: str | None = None
    description: str | None = None
    image: str | None = None

    warm_period: WateringPeriod | None = None
    cold_period: WateringPeriod | None = None
    fertilizing: FertilizingPeriod | None = None

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None
