from fastapi import APIRouter

from app.models import Plant
from app.schemes import PlantReadScheme
from app.services import user_service

router = APIRouter()


@router.get('', response_model=list[PlantReadScheme])
async def get_plants(
    user_id: int = user_service.current_user_id_dependency,
):
    return await Plant.get_plants(user_id)
