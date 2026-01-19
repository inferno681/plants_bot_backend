from datetime import date, datetime
from logging import getLogger

from beanie import PydanticObjectId
from dateutil import relativedelta
from dateutil.rrule import MONTHLY, WEEKLY, rrule

from app.constants.plant import WEEKDAY_MAP
from app.exceptions.plant import NoDaysSchedulerError, NoWateringPeriodError
from app.logs.plant import PLANT_SERVICE_START_LOG
from app.models import Plant
from app.models.plant import FertilizingType, FrequencyType, WateringSchedule
from app.schemes import PlantCreteScheme


class Scheduler:
    """Scheduler service."""

    def next_watering_date(
        self, plant: Plant, last_watered: date | None = None
    ) -> date:
        """Calculate next watering date."""
        last_watered_dt = datetime.combine(
            last_watered or date.today(), datetime.min.time()
        )
        current_period = plant.current_period

        if not current_period:
            raise NoWateringPeriodError()

        rule = self._build_rrule(
            current_period.period.schedule,
            last_watered_dt,
        )
        next_dt = rule.after(last_watered_dt)

        if next_dt.date() > current_period.end:
            next_rule = self._build_rrule(
                current_period.next_period.schedule,
                datetime.combine(current_period.end, datetime.min.time()),
            )
            next_dt = next_rule.after(
                datetime.combine(current_period.end, datetime.min.time())
            )

        plant.next_watering_at = next_dt.date()
        return plant.next_watering_at

    def next_fertilizing_date(
        self, plant: Plant, last_fertilized: date | None = None
    ) -> date:
        """Calculate new fertilizing date."""
        fert_start, fert_end = plant.fertilizing.as_period()

        frequency = plant.fertilizing.frequency

        if plant.fertilizing.type == FertilizingType.days:
            delta = relativedelta(days=frequency)
        elif plant.fertilizing.type == FertilizingType.weeks:
            delta = relativedelta(weeks=frequency)
        elif plant.fertilizing.type == FertilizingType.months:
            delta = relativedelta(months=frequency)

        fertilizing_date = (last_fertilized or date.today()) + delta

        if fertilizing_date > fert_end:
            plant.next_fertilizing_at = fert_start + relativedelta(years=1)
        else:
            plant.next_fertilizing_at = fertilizing_date

        return plant.next_fertilizing_at

    def sync_watering_and_fertilizing(self, plant: Plant):
        """Check synchronization for watering and fertilizing."""
        if plant.fertilizing and (
            plant.next_watering_at >= plant.next_fertilizing_at
        ):
            return True
        return False

    def _build_rrule(
        self, schedule: WateringSchedule, start_dt: datetime
    ) -> rrule:
        """Build schedule for watering."""
        interval = 2 if schedule.type == 'biweekly' else 1
        if schedule.type == FrequencyType.monthly:
            return rrule(
                freq=MONTHLY,
                bymonthday=schedule.monthday or start_dt.day,
                dtstart=start_dt,
            )
        else:
            weekday_value = schedule.weekday
            if isinstance(weekday_value, int):
                weekdays = [WEEKDAY_MAP[weekday_value]]
            elif isinstance(weekday_value, (set, list)):
                weekdays = [WEEKDAY_MAP[day] for day in weekday_value]
            else:
                raise NoDaysSchedulerError()

            return rrule(
                freq=WEEKLY,
                interval=interval,
                byweekday=weekdays,
                dtstart=start_dt,
            )


class PlantService:
    """Plant service."""

    def __init__(self):
        self.log = getLogger(__name__)
        self.log.info(PLANT_SERVICE_START_LOG)

    async def add_plant(self, user_id: str, plant: PlantCreteScheme):
        """Add plant."""
        plant: Plant = Plant(
            user_id=PydanticObjectId(user_id), **plant.model_dump()
        )
        await plant.insert()
        return plant
