from fastapi import APIRouter, Depends

from app.models import Plant
from app.schemes import PlantReadScheme
from app.services import user_service

router = APIRouter()


@router.get('', response_model=list[PlantReadScheme])
async def get_plants(
    user_id: int = Depends(user_service.get_current_user_id),
):
    return await Plant.get_plants(user_id)
