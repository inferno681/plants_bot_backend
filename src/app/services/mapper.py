import asyncio

from app.models import Plant
from app.schemes import PlantReadSchemeShort
from app.services.storage import storage_service


class PlantReadMapper:

    @staticmethod
    async def to_short(plant: Plant) -> PlantReadSchemeShort:
        url = await storage_service.presigned_url_for_plant(plant)

        return PlantReadSchemeShort(
            id=str(plant.id),
            name=plant.name,
            next_watering_at=plant.next_watering_at,
            image_url=url if isinstance(url, str) else None,
        )

    @staticmethod
    async def to_short_many(plants: list[Plant]) -> list[PlantReadSchemeShort]:
        urls = await asyncio.gather(
            *[
                storage_service.presigned_url_for_plant(plant)
                for plant in plants
            ]
        )
        return [
            PlantReadSchemeShort(
                **plant.model_dump(),
                image_url=url if isinstance(url, str) else None,
            )
            for plant, url in zip(plants, urls)
        ]


plant_mapper = PlantReadMapper()
