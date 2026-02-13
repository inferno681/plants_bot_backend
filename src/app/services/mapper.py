import asyncio

from fastapi import FastAPI, Request

from app.models import Plant
from app.schemes import PlantReadScheme, PlantReadSchemeShort
from app.services.storage import S3StorageService


class PlantReadMapper:
    """Plant read mapper."""

    def __init__(self, storage: S3StorageService):
        """Mapper constructor."""
        self.storage = storage

    async def to_full(self, plant: Plant) -> PlantReadScheme:
        """To full scheme mapping."""
        scheme = PlantReadScheme.model_validate(plant)
        scheme.image_url = await self.storage.presigned_url_for_plant(plant)
        return scheme

    async def to_short(self, plant: Plant) -> PlantReadSchemeShort:
        """To short scheme mapping."""
        return PlantReadSchemeShort(
            id=str(plant.id),
            name=plant.name,
            next_watering_at=plant.next_watering_at,
            image_url=await self.storage.presigned_url_for_plant(plant),
        )

    async def to_short_many(
        self, plants: list[Plant]
    ) -> list[PlantReadSchemeShort]:
        """To short scheme list mapping."""
        urls = await asyncio.gather(
            *[self.storage.presigned_url_for_plant(plant) for plant in plants]
        )
        return [
            PlantReadSchemeShort(
                **plant.model_dump(),
                image_url=url,
            )
            for plant, url in zip(plants, urls)
        ]


def init_plant_mapper(
    app: FastAPI,
    storage: S3StorageService,
) -> None:
    """Create PlantReadMapper once and store on app.state."""
    app.state.plant_mapper = PlantReadMapper(storage=storage)


def get_plant_mapper(request: Request) -> PlantReadMapper:
    """FastAPI dependency for PlantReadMapper."""
    return request.app.state.plant_mapper
