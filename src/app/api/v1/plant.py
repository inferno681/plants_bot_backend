from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.schemes import (
    CursorPaginatedResponse,
    ImageUpload,
    PlantDashboardStats,
    PlantReadScheme,
    PlantReadSchemeShort,
    PlantUpdateScheme,
)
from app.schemes.plant import PlantCreteScheme
from app.services import (
    current_user_id_dependency,
    plant_mapper,
    plant_service,
)
from app.utils import CursorPaginatorParams, OrderParams, PlantFilter


def ordering_params(
    order: Annotated[list[str] | None, Query(alias='order')] = None,
) -> OrderParams:
    return OrderParams.model_validate({'order': order})


router = APIRouter()


@router.post('', response_model=PlantReadScheme)
async def add_plant(
    plant_data: PlantCreteScheme, user_id: str = current_user_id_dependency
):
    return await plant_service.add_plant(
        user_id=user_id, plant_data=plant_data
    )


@router.get('', response_model=CursorPaginatedResponse[PlantReadSchemeShort])
async def get_plants(
    filters: Annotated[PlantFilter, Depends()],
    paginator: Annotated[CursorPaginatorParams, Depends()],
    ordering: Annotated[OrderParams, Depends(ordering_params)],
    user_id: str = current_user_id_dependency,
):
    plants, has_more = await plant_service.get_plants(
        user_id, filters, paginator, ordering
    )
    schemes = await plant_mapper.to_short_many(plants)

    return CursorPaginatedResponse(
        items=schemes,
        next_cursor=schemes[-1].id if schemes and has_more else None,
        has_more=has_more,
        limit=paginator.limit,
    )


@router.get('/stats', response_model=PlantDashboardStats)
async def get_plants_stats(
    user_id: str = current_user_id_dependency,
):
    return await plant_service.get_stats(user_id)


@router.post('/{plant_id}/image', response_model=PlantReadScheme)
async def update_plant_image(
    plant_id: str,
    image: Annotated[UploadFile, File(...)],
    user_id: str = current_user_id_dependency,
):
    file_info = ImageUpload(
        file_bytes=await image.read(),
        filename=image.filename or 'upload.jpg',
        content_type=image.content_type or 'image/jpeg',
    )
    return await plant_service.update_plant_image(plant_id, user_id, file_info)


@router.get('/{plant_id}', response_model=PlantReadScheme)
async def get_plant(
    plant_id: str,
    user_id: str = current_user_id_dependency,
):
    plant = await plant_service.get_plant_by_id(plant_id, user_id)

    return await plant_mapper.to_full(plant)


@router.patch('/{plant_id}', response_model=PlantReadScheme)
async def update_plant(
    plant_id: str,
    plant_update: PlantUpdateScheme,
    user_id: str = current_user_id_dependency,
):
    plant = await plant_service.update_plant(plant_id, user_id, plant_update)

    return await plant_mapper.to_full(plant)
