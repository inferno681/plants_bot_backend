import asyncio

from fastapi import APIRouter, HTTPException, status

from app.constants.plant import PLANT_NOT_FOUND_MSG
from app.models import Plant
from app.schemes import PlantReadScheme, PlantReadSchemeShort
from app.services import storage_service, user_service

router = APIRouter()


@router.get('', response_model=list[PlantReadSchemeShort])
async def get_plants(
    user_id: int = user_service.current_user_id_dependency,
):
    plants = await Plant.get_plants(user_id)
    schemes = [PlantReadSchemeShort.model_validate(plant) for plant in plants]

    urls = await asyncio.gather(
        *[storage_service.presigned_url_for_plant(plant) for plant in plants]
    )

    for scheme, url in zip(schemes, urls):
        if isinstance(url, str):
            scheme.image_url = url

    return schemes


@router.get('/{plant_id}', response_model=PlantReadScheme)
async def get_plant(
    plant_id: str,
    user_id: int = user_service.current_user_id_dependency,
):
    plant = await Plant.get_plant_by_id(plant_id, user_id)
    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PLANT_NOT_FOUND_MSG
        )
    scheme = PlantReadScheme.model_validate(plant)

    url = await storage_service.presigned_url_for_plant(plant)
    if isinstance(url, str):
        scheme.image_url = url

    return scheme
