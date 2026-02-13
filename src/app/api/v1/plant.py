from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.dependencies import (
    current_user_id_dep,
    plant_mapper_dep,
    plant_query_dep,
    plant_service_dep,
)
from app.schemes import (
    CursorPaginatedResponse,
    ImageUpload,
    PlantCreteScheme,
    PlantDashboardStats,
    PlantQuery,
    PlantReadScheme,
    PlantReadSchemeShort,
    PlantUpdateScheme,
)
from app.services import PlantReadMapper, PlantService

router = APIRouter()


@router.post('', response_model=PlantReadScheme)
async def add_plant(
    plant_data: PlantCreteScheme,
    user_id: str = current_user_id_dep,
    plant_service: PlantService = plant_service_dep,
):
    """Add plant endpoint."""
    return await plant_service.add_plant(
        user_id=user_id, plant_data=plant_data
    )


@router.get('', response_model=CursorPaginatedResponse[PlantReadSchemeShort])
async def get_plants(
    query: PlantQuery = plant_query_dep,
    plant_service: PlantService = plant_service_dep,
    plant_mapper: PlantReadMapper = plant_mapper_dep,
    user_id: str = current_user_id_dep,
):
    """Get user plants endpoint."""
    plants, has_more = await plant_service.get_plants(
        user_id, query.filters, query.paginator, query.ordering
    )
    schemes = await plant_mapper.to_short_many(plants)

    return CursorPaginatedResponse(
        items=schemes,
        next_cursor=schemes[-1].id if schemes and has_more else None,
        has_more=has_more,
        limit=query.paginator.limit,
    )


@router.get('/stats', response_model=PlantDashboardStats)
async def get_plants_stats(
    user_id: str = current_user_id_dep,
    plant_service: PlantService = plant_service_dep,
):
    """Get plants dashboard stats endpoint."""
    return await plant_service.get_stats(user_id)


@router.post('/{plant_id}/image', response_model=PlantReadScheme)
async def update_plant_image(
    plant_id: str,
    image: Annotated[UploadFile, File(...)],
    user_id: str = current_user_id_dep,
    plant_service: PlantService = plant_service_dep,
):
    """Update plant image endpoint."""
    file_info = ImageUpload(
        file_bytes=await image.read(),
        filename=image.filename or 'upload.jpg',
        content_type=image.content_type or 'image/jpeg',
    )
    return await plant_service.update_plant_image(plant_id, user_id, file_info)


@router.get('/{plant_id}', response_model=PlantReadScheme)
async def get_plant(
    plant_id: str,
    user_id: str = current_user_id_dep,
    plant_service: PlantService = plant_service_dep,
    plant_mapper: PlantReadMapper = plant_mapper_dep,
):
    """Get plant by id endpoint."""
    plant = await plant_service.get_plant_by_id(plant_id, user_id)

    return await plant_mapper.to_full(plant)


@router.patch('/{plant_id}', response_model=PlantReadScheme)
async def update_plant(
    plant_id: str,
    plant_update: PlantUpdateScheme,
    user_id: str = current_user_id_dep,
    plant_service: PlantService = plant_service_dep,
    plant_mapper: PlantReadMapper = plant_mapper_dep,
):
    """Update plant endpoint."""
    plant = await plant_service.update_plant(plant_id, user_id, plant_update)

    return await plant_mapper.to_full(plant)
