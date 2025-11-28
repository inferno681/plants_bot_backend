from fastapi import APIRouter

from app.schemes import InitData, Tokens, RefreshRequest
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


@router.post('/refresh', response_model=Tokens)
async def refresh_tokens(refresh_token: RefreshRequest):
    """Refresh tokens endpoint."""
    return await auth_service.refresh_user_tokens(refresh_token.refresh_token)
