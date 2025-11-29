from beanie.operators import RegEx
from pydantic import BaseModel


class PlantFilter(BaseModel):
    """Filter model for querying plants."""

    name: str | None = None

    def apply(self, model) -> list:
        """Generate filter expressions for the given model."""
        expressions = []

        if self.name:
            expressions.append(RegEx(model.name, self.name, options="i"))

        return expressions
