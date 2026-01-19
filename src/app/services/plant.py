from logging import getLogger

from beanie import PydanticObjectId


from app.logs.plant import PLANT_SERVICE_START_LOG
from app.models import Plant

from app.schemes import PlantCreteScheme
from app.services.scheduler import scheduler


class PlantService:
    """Plant service."""

    def __init__(self):
        self.log = getLogger(__name__)
        self.log.info(PLANT_SERVICE_START_LOG)

    async def add_plant(self, user_id: str, plant_data: PlantCreteScheme):
        """Add plant."""

        plant = Plant(
            user_id=PydanticObjectId(user_id), **plant_data.model_dump()
        )
        if plant.warm_period and plant.cold_period:
            plant = scheduler.next_watering_date(
                plant, plant.last_watered_at if plant.last_watered_at else None
            )
        if plant.fertilizing:
            plant = scheduler.next_fertilizing_date(
                plant,
                plant.last_fertilized_at if plant.last_fertilized_at else None,
            )
        await plant.insert()
        return plant


plant_service = PlantService()
