from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.db import db_helper
from app.schemes import InitData, RefreshRequest, Tokens
from app.security import oauth2_dependency
from app.services import auth_service

router = APIRouter()


@router.post('/login', response_model=Tokens)
async def login(init: InitData):
    """Login endpoint."""
    return await auth_service.login_telegram_user(init.init_data)


@router.post(
    '/web_registration',
)
async def register(session=Depends(db_helper.transaction)):
    """Registration endpoint."""
    return await auth_service.registration_web_user(
        email='123', password='123', session=session
    )


@router.post('/logout')
async def logout(token: str = oauth2_dependency):
    return {'message': await auth_service.logout_user(token)}


@router.post('/refresh', response_model=Tokens)
async def refresh_tokens(refresh_token: RefreshRequest):
    """Refresh tokens endpoint."""
    return await auth_service.refresh_user_tokens(refresh_token.refresh_token)


@router.post('/login_doc', response_model=Tokens)
async def doc_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Documentation user login endpoint."""
    return await auth_service.login_doc(form_data.password)
