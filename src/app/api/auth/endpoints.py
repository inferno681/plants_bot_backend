from fastapi import APIRouter

from app.schemes import InitData, Tokens
from app.security import oauth2_dependency
from app.services import auth_service

router = APIRouter()


@router.post('/login', response_model=Tokens)
async def login(init: InitData):
    """Login endpoint."""
    return await auth_service.login_user(init.init_data)


@router.post('/logout')
async def logout(token: str = oauth2_dependency):
    return {'message': await auth_service.logout_user(token)}
