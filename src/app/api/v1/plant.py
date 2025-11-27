import asyncio
import os

from fastapi import APIRouter

from app.models import Plant
from app.schemes import PlantReadScheme
from app.services import storage_service, user_service

router = APIRouter()


@router.get('', response_model=list[PlantReadScheme])
async def get_plants(
    user_id: int = 459335857,
):
    plants = await Plant.get_plants(user_id)
    schemes = [PlantReadScheme.model_validate(plant) for plant in plants]

    tasks = []
    for plant, scheme in zip(plants, schemes):
        if plant.storage_key:

            ext = os.path.splitext(plant.storage_key)[1] or '.jpg'
            filename = f"{plant.name}{ext}"

            tasks.append(
                storage_service.generate_presigned_url(
                    storage_key=plant.storage_key,
                    filename=filename,
                )
            )
        else:
            tasks.append(None)

    urls = await asyncio.gather(
        *[task if task is not None else asyncio.sleep(0) for task in tasks]
    )

    for scheme, url in zip(schemes, urls):
        if isinstance(url, str):
            scheme.image_url = url

    return schemes
