from datetime import date
from typing import Literal

from pydantic import BaseModel


class PlantTask(BaseModel):
    plant_id: str
    name: str
    date: date
    type: Literal['watering', 'watering_with_fertilizing']


class PlantDashboardStats(BaseModel):
    total: int
    attention: int
    watering_week: int
    tasks: list[PlantTask]
