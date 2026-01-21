import asyncio

from app.models import Plant
from app.schemes import PlantReadScheme, PlantReadSchemeShort
from app.services.storage import storage_service


class PlantReadMapper:

    @staticmethod
    async def to_full(plant: Plant) -> PlantReadScheme:
        scheme = PlantReadScheme.model_validate(plant)
        scheme.image_url = await storage_service.presigned_url_for_plant(plant)
        return scheme

    @staticmethod
    async def to_short(plant: Plant) -> PlantReadSchemeShort:

        return PlantReadSchemeShort(
            id=str(plant.id),
            name=plant.name,
            next_watering_at=plant.next_watering_at,
            image_url=await storage_service.presigned_url_for_plant(plant),
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
                image_url=url,
            )
            for plant, url in zip(plants, urls)
        ]


plant_mapper = PlantReadMapper()
