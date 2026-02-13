from datetime import date
from typing import Literal

from beanie import PydanticObjectId
from pydantic import BaseModel


class PlantTask(BaseModel):
    """Plant Task scheme."""
    plant_id: PydanticObjectId
    name: str
    date: date
    type: Literal['watering', 'watering_with_fertilizing']


class PlantDashboardStats(BaseModel):
    """Plant Dashboard Stats scheme."""
    total: int
    attention: int
    watering_week: int
    tasks: list[PlantTask]
