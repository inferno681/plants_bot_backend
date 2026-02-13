from datetime import date
from enum import StrEnum, auto

from beanie import PydanticObjectId
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field

from app.constants.general import DAYS_IN_MONTH, MONTHS_IN_YEAR
from app.models.base import BaseDocument


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
    """Current Period model."""
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

    def build_delta(self) -> relativedelta:
        """Build delta."""
        match self.type:
            case FertilizingType.days:
                return relativedelta(days=self.frequency)
            case FertilizingType.weeks:
                return relativedelta(weeks=self.frequency)
            case FertilizingType.months:
                return relativedelta(months=self.frequency)
            case _:
                return relativedelta()

    def as_period(self) -> tuple[date, date]:
        """Convert values to dates."""
        current_year = date.today().year
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

    warm_period: WateringPeriod | None = None
    cold_period: WateringPeriod | None = None
    fertilizing: FertilizingPeriod | None = None

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None

    def period_info(self, date: date) -> CurrentPeriod | None:
        """Handle period info."""
        if self.warm_period and self.cold_period:
            start, end = self.warm_period.as_period()
            if start <= date <= end:
                return CurrentPeriod(
                    period=self.warm_period,
                    next_period=self.cold_period,
                    start=start,
                    end=end,
                )
            else:
                start, end = self.cold_period.as_period()
                return CurrentPeriod(
                    period=self.cold_period,
                    next_period=self.warm_period,
                    start=start,
                    end=end,
                )

        return None

    class Settings(BaseDocument.Settings):
        """Settings for Plant model."""
        name = 'plants'
