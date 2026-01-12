from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.schemes import (
    ClientInfo,
    Tokens,
    WebUser,
    WebAccountRegistration,
    WebAccountLogin,
)
from app.services import web_auth_service
from app.db import session_dependency
from app.utils import client_info_dependency
from pymongo.asynchronous.client_session import AsyncClientSession

router = APIRouter()


@router.post('/login_doc', response_model=Tokens)
async def doc_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    client_info: ClientInfo = client_info_dependency,
):
    """Documentation user login endpoint."""
    return await web_auth_service.login_doc(
        form_data.password, client_info.ip, client_info.ua
    )


@router.post('/registration', response_model=WebUser)
async def web_registration(
    user_data: WebAccountRegistration,
    session: AsyncClientSession = session_dependency,
):
    """Web user registration."""
    return await web_auth_service.registration_web_user(user_data, session)


@router.post('/login', response_model=Tokens)
async def login(
    login_data: WebAccountLogin,
    client_info: ClientInfo = client_info_dependency,
):
    """Web user login."""
    return await web_auth_service.login(
        login_data, client_info.ip, client_info.ua
    )
