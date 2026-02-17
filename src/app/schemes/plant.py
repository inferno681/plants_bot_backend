from datetime import date, timedelta

from beanie import PydanticObjectId
from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    field_validator,
    model_validator,
)

from app.exceptions.plant import OnePeriodMissingError, PeriodCrossingError
from app.models.plant import FertilizingPeriod, WateringPeriod


class PlantReadSchemeShort(BaseModel):
    """Plant short scheme."""

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
        """Cast id."""
        return str(id)

    @computed_field
    def status(self) -> str:
        """Handle status."""
        today = date.today()
        if self.next_watering_at:
            if self.next_watering_at < today:
                return 'needs_watering'
            elif self.next_watering_at == today + timedelta(days=1):
                return 'watering_tomorrow'
        return 'healthy'


class PlantReadScheme(PlantReadSchemeShort):
    """Plant Read scheme."""

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


class BasePlantCUScheme(BaseModel):
    """Base plant create, update scheme."""

    scientific_name: str | None = None
    description: str | None = None

    warm_period: WateringPeriod | None = None
    cold_period: WateringPeriod | None = None
    fertilizing: FertilizingPeriod | None = None

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None

    @model_validator(mode='after')
    def check_periods_do_not_overlap(self):
        """Check periods do not overlap."""
        fields_set = self.model_fields_set
        has_warm = 'warm_period' in fields_set
        has_cold = 'cold_period' in fields_set
        if not has_warm and not has_cold:
            return self
        if has_warm != has_cold:
            raise OnePeriodMissingError()
        if self.warm_period is None and self.cold_period is None:
            setattr(self, 'next_watering_at', None)
            return self
        warm_period = self.warm_period.as_period()
        cold_period = self.cold_period.as_period()

        if (
            warm_period[0] <= cold_period[1]
            and cold_period[0] <= warm_period[1]
        ):
            raise PeriodCrossingError()

        return self

    @model_validator(mode='after')
    def reset_fertilizing_next_date(self):
        """Reset fertilizing next date."""
        if 'fertilizing' in self.model_fields_set and self.fertilizing is None:
            setattr(self, 'next_fertilizing_at', None)
        return self

    @property
    def should_recalc_watering(self) -> bool:
        """Should recalc watering."""
        fields_set = self.model_fields_set
        if not (
            {'warm_period', 'cold_period', 'last_watered_at'} & fields_set
        ):
            return False
        if (
            'next_watering_at' in fields_set
            and self.next_watering_at
            and self.next_watering_at > date.today()
        ):
            return False
        return True

    @property
    def should_recalc_fertilizing(self) -> bool:
        """Should recalc fertilizing."""
        fields_set = self.model_fields_set
        if not ({'fertilizing', 'last_fertilized_at'} & fields_set):
            return False
        if (
            'next_fertilizing_at' in fields_set
            and self.next_fertilizing_at
            and self.next_fertilizing_at > date.today()
        ):
            return False
        return True


class PlantCreteScheme(BasePlantCUScheme):
    """Create plant scheme."""

    name: str


class PlantUpdateScheme(BasePlantCUScheme):
    """Plant Update scheme."""

    name: str | None = None


class PlantBotCreateScheme(PlantCreteScheme):
    """Plant Bot Create scheme."""

    image: str | None = None
    user_id: str


class PlantBotUpdateScheme(PlantUpdateScheme):
    """Plant Bot Update scheme."""

    image: str | None = None
    user_id: str
    plant_id: str


class PlantSchedulerViewScheme(BaseModel):
    """Plant Scheduler View scheme."""

    id: PydanticObjectId
    user_id: PydanticObjectId
    name: str
    image: str | None = None

    model_config = ConfigDict(from_attributes=True)
