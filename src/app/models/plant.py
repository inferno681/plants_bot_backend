from datetime import date, timedelta
from enum import StrEnum, auto
from typing import Any, cast

from beanie import PydanticObjectId
from dateutil import relativedelta
from pydantic import BaseModel, Field

from app.constants.general import DAYS_IN_MONTH, MONTHS_IN_YEAR
from app.models.base import BaseDocument
from app.utils import (
    CursorPaginatorParams,
    OrderDirection,
    OrderItem,
    OrderParams,
    PlantFilter,
)


class Period(StrEnum):
    """Enum for periods."""

    warm = auto()
    cold = auto()


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

    start: MonthDay
    end: MonthDay
    schedule: WateringSchedule
    note: str | None = None

    def as_period(self) -> tuple[date, date]:
        """Convert values to dates."""
        current_year = date.today().year
        if self.start is None or self.end is None:
            raise ValueError()
        start = self.start.as_date(current_year)
        end = self.end.as_date(current_year)
        if start < end:
            return start, end
        if start < date.today():
            end += relativedelta(years=1)
        else:
            start -= relativedelta(years=1)
        return start, end


class CurrentPeriod(BaseModel):
    period_name: Period
    period: WateringPeriod
    next_period: WateringPeriod
    start: date
    end: date


class FertilizingType(StrEnum):
    """Fertilizing frequency types enum."""

    days = auto()
    weeks = auto()
    months = auto()


class FertilizingPeriod(BaseModel):
    """Fertilizing period model."""

    start: MonthDay
    end: MonthDay
    frequency: int
    type: FertilizingType = FertilizingType.days
    note: str | None = None

    def as_period(self) -> tuple[date, date]:
        """Convert values to dates."""
        current_year = date.today().year
        if self.start is None or self.end is None:
            raise ValueError()
        start = self.start.as_date(current_year)
        end = self.end.as_date(current_year)
        if start < end:
            return start, end
        if start < date.today():
            end += relativedelta(years=1)
        else:
            start -= relativedelta(years=1)
        return start, end


class Plant(BaseDocument):
    """Plant model."""

    user_id: PydanticObjectId
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

    @property
    def current_period(self) -> CurrentPeriod | None:
        today = date.today()

        if self.warm_period:
            start, end = self.warm_period.as_period()
            if start <= today <= end:
                return CurrentPeriod(
                    period_name=Period.warm,
                    period=self.warm_period,
                    next_period=self.cold_period,
                    start=start,
                    end=end,
                )

        if self.cold_period:
            start, end = self.cold_period.as_period()
            if start <= today <= end:
                return CurrentPeriod(
                    period_name=Period.cold,
                    period=self.cold_period,
                    next_period=self.warm_period,
                    start=start,
                    end=end,
                )

        return None

    @classmethod
    async def get_plants(
        cls,
        user_id: int,
        filters: PlantFilter,
        paginator: CursorPaginatorParams,
        ordering: OrderParams,
    ) -> tuple[list["Plant"], bool]:

        query = [cls.user_id == user_id]

        query.extend(filters.apply(cls))

        if paginator.cursor:
            pivot = await cls.find_one(
                cls.id == PydanticObjectId(paginator.cursor)
            )
            if pivot is None:
                return [], False

            cursor_filter = cls._build_cursor_filter(
                pivot=pivot,
                order_items=ordering.with_tie_breaker(),
            )

            query.append(cursor_filter)

        items = (
            await cls.find(*query)
            .sort(cast(Any, ordering.sort_tuples))
            .limit(paginator.limit + 1)
            .to_list()
        )

        has_more = len(items) > paginator.limit
        if has_more:
            items = items[: paginator.limit]

        return items, has_more

    @classmethod
    async def get_plant_by_id(
        cls, plant_id: str, user_id: int
    ) -> 'Plant | None':
        return await cls.find_one(
            Plant.id == PydanticObjectId(plant_id), Plant.user_id == user_id
        )

    @classmethod
    async def get_stats(cls, user_id: int) -> dict[str, Any]:
        """Aggregate basic dashboard stats."""
        plants = await cls.find(cls.user_id == user_id).to_list()

        total = len(plants)

        today = date.today()
        week_limit = today + timedelta(days=7)

        attention = 0
        watering_week = 0

        tasks: list[dict[str, Any]] = []

        for plant in plants:
            next_water: date | None = plant.next_watering_at
            next_fert: date | None = plant.next_fertilizing_at

            min_diff = min(
                Plant.days_until(next_water, today),
                Plant.days_until(next_fert, today),
            )
            if min_diff <= 0:
                attention += 1

            if next_water and today <= next_water <= week_limit:
                watering_week += 1

            if next_water:
                task_type = (
                    'watering_with_fertilizing'
                    if next_fert and next_fert == next_water
                    else 'watering'
                )
                tasks.append(
                    {
                        'plant_id': str(plant.id),
                        'name': plant.name,
                        'date': next_water,
                        'type': task_type,
                    }
                )

        tasks.sort(key=lambda task: task['date'])

        return {
            'total': total,
            'watering_week': watering_week,
            'attention': attention,
            'tasks': tasks[:10],
        }

    @staticmethod
    def days_until(value: date | None, today: date | None = None) -> int:
        """Return days between value and today (default: current date)."""
        if today is None:
            today = date.today()
        if value is None:
            return 10**9
        return (value - today).days

    @classmethod
    def _build_cursor_filter(
        cls,
        pivot: "Plant",
        order_items: list["OrderItem"],
        index: int = 0,
    ):
        """Build cursor-based filter for multi-field ordering."""
        item = order_items[index]

        field_expr = getattr(cls, item.field.value)
        pivot_value = getattr(pivot, item.field.value)

        comparator = (
            field_expr < pivot_value
            if item.direction == OrderDirection.DESC
            else field_expr > pivot_value
        )

        if index == len(order_items) - 1:
            return comparator

        equals = field_expr == pivot_value
        return comparator | (
            equals & cls._build_cursor_filter(pivot, order_items, index + 1)
        )

    class Settings(BaseDocument.Settings):
        name = 'plants'
