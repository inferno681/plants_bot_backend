import asyncio
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.constants.plant import NO_FILENAME_MSG, PLANT_NOT_FOUND_MSG
from app.models import Plant
from app.schemes import (
    CursorPaginatedResponse,
    PlantReadScheme,
    PlantReadSchemeShort,
    PlantStatsScheme,
    PlantUpdateScheme,
)
from app.services import current_user_id_dependency, storage_service
from app.utils import (
    CursorPaginatorParams,
    OrderParams,
    PlantFilter,
    send_photo_to_telegram,
)


def ordering_params(
    order: Annotated[list[str] | None, Query(alias='order')] = None,
) -> OrderParams:
    return OrderParams(order=order)  # type: ignore[arg-type]


router = APIRouter()


@router.get('', response_model=CursorPaginatedResponse[PlantReadSchemeShort])
async def get_plants(
    filters: Annotated[PlantFilter, Depends()],
    paginator: Annotated[CursorPaginatorParams, Depends()],
    ordering: Annotated[OrderParams, Depends(ordering_params)],
    user_id: str = current_user_id_dependency,
):
    plants, has_more = await Plant.get_plants(
        user_id, filters, paginator, ordering
    )
    schemes = [PlantReadSchemeShort.model_validate(plant) for plant in plants]

    for scheme, url in zip(
        schemes,
        await asyncio.gather(
            *[
                storage_service.presigned_url_for_plant(plant)
                for plant in plants
            ]
        ),
    ):
        if isinstance(url, str):
            scheme.image_url = url

    return CursorPaginatedResponse(
        items=schemes,
        next_cursor=schemes[-1].id if schemes and has_more else None,
        has_more=has_more,
        limit=paginator.limit,
    )


@router.get('/stats', response_model=PlantStatsScheme)
async def get_plants_stats(
    user_id: str = current_user_id_dependency,
):
    return PlantStatsScheme.model_validate(await Plant.get_stats(user_id))


@router.post("/{plant_id}/image", response_model=PlantReadScheme)
async def update_plant_image(
    plant_id: str,
    image: Annotated[UploadFile, File(...)],
    user_id: str = current_user_id_dependency,
):
    plant = await Plant.get_plant_by_id(plant_id, user_id)
    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PLANT_NOT_FOUND_MSG
        )

    if not image.filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=NO_FILENAME_MSG
        )
    file_bytes = await image.read()
    file_id = await send_photo_to_telegram(
        file_bytes=file_bytes,
        filename=image.filename,
        content_type=image.content_type,
    )
    ext = Path(image.filename).suffix.lstrip('.')
    storage_key = f'{user_id}/{uuid4()}.{ext}'
    if plant.storage_key:
        await storage_service.delete_file(plant.storage_key or '')
    await storage_service.upload_file(storage_key, file_bytes)
    plant.storage_key = storage_key
    plant.image = file_id
    await plant.save()

    scheme = PlantReadScheme.model_validate(plant)
    url = await storage_service.presigned_url_for_plant(plant)
    if isinstance(url, str):
        scheme.image_url = url

    return scheme


@router.get('/{plant_id}', response_model=PlantReadScheme)
async def get_plant(
    plant_id: str,
    user_id: str = current_user_id_dependency,
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


@router.patch('/{plant_id}', response_model=PlantReadScheme)
async def update_plant(
    plant_id: str,
    plant_update: PlantUpdateScheme,
    user_id: str = current_user_id_dependency,
):
    plant = await Plant.get_plant_by_id(plant_id, user_id)
    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PLANT_NOT_FOUND_MSG
        )
    for key, new_value in plant_update.model_dump(exclude_unset=True).items():
        setattr(plant, key, new_value)
    await plant.save()
    scheme = PlantReadScheme.model_validate(plant)

    url = await storage_service.presigned_url_for_plant(plant)
    if isinstance(url, str):
        scheme.image_url = url

    return scheme
