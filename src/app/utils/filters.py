from datetime import date, timedelta

from beanie.operators import And, Or, RegEx
from pydantic import BaseModel

from app.models import FrequencyType


class PlantFilter(BaseModel):
    """Filter model for querying plants."""

    name: str | None = None
    watering_type: FrequencyType | None = None
    watering_in: int | None = None

    def apply(self, model) -> list:
        """Generate filter expressions for the given model."""
        expressions: list = []

        if self.name:
            expressions.append(RegEx(model.name, self.name, options="i"))

        if self.watering_type:
            expressions.append(
                Or(
                    model.warm_period.schedule.type == self.watering_type,
                    model.cold_period.schedule.type == self.watering_type,
                )
            )
        if self.watering_in is not None:
            today = date.today()
            target = today + timedelta(days=self.watering_in)
            expressions.append(
                And(
                    model.next_watering_at >= today,
                    model.next_watering_at <= target,
                )
            )

        return expressions
