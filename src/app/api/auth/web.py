from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.asynchronous.client_session import AsyncClientSession

from app.db import session_dependency
from app.schemes import (
    ClientInfo,
    RefreshRequest,
    Tokens,
    UserSession,
    WebAccountLogin,
    WebAccountRegistration,
    WebUser,
)
from app.services import (
    current_user_id_dependency,
    current_user_uid_sid_dependency,
    web_auth_service,
)
from app.utils import client_info_dependency

router = APIRouter()


@router.post('/login_doc', response_model=Tokens)
async def doc_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    client_info: ClientInfo = client_info_dependency,
):
    """Documentation user login endpoint."""
    return await web_auth_service.login_doc(form_data.password, client_info)


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
    return await web_auth_service.login(login_data, client_info)


@router.post('/logout')
async def logout(session_info: UserSession = current_user_uid_sid_dependency):
    """Current session logout."""
    return {
        'message': await web_auth_service.logout_user(
            session_info.uid, session_info.sid
        )
    }


@router.post('/logout_others')
async def logout_other(
    session_info: UserSession = current_user_uid_sid_dependency,
):
    """Other session logout."""
    return {
        'message': await web_auth_service.logout_others_sessions(
            session_info.uid, session_info.sid
        )
    }


@router.post('/logout_all')
async def logout_all(user_id: str = current_user_id_dependency):
    """All session logout."""
    return {'message': await web_auth_service.logout_all_sessions(user_id)}


@router.post('/refresh', response_model=Tokens)
async def refresh_tokens(
    refresh_token: RefreshRequest,
    client_info: ClientInfo = client_info_dependency,
):
    """Refresh tokens endpoint."""
    return await web_auth_service.refresh_user_tokens(
        refresh_token.refresh_token, client_info
    )
