import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.asynchronous.client_session import AsyncClientSession

from app.constants.auth import CSRF_LENGTH, LAX_LITERAL
from app.dependencies import (
    current_web_uid_sid_dep,
    refresh_request_dep,
    session_dependency,
    web_auth_service_dep,
)
from app.schemes import (
    ClientInfo,
    RefreshRequestCookie,
    UserSession,
    WebAccountLogin,
    WebAccountRegistration,
    WebTokens,
    WebUser,
)
from app.services import WebAuthService
from app.utils import client_info_dependency
from config import config

router = APIRouter()


@router.post('/login_doc', response_model=WebTokens)
async def doc_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    client_info: ClientInfo = client_info_dependency,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Documentation user login endpoint."""
    tokens = await web_auth_service.login(
        WebAccountLogin.model_validate(
            {'email': form_data.username, 'password': form_data.password}
        ),
        client_info,
    )
    return WebTokens(access_token=tokens.access_token)


@router.post('/registration', response_model=WebUser)
async def web_registration(
    user_data: WebAccountRegistration,
    session: AsyncClientSession = session_dependency,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Web user registration."""
    return await web_auth_service.registration_web_user(user_data, session)


@router.post('/login', response_model=WebTokens)
async def login(
    login_data: WebAccountLogin,
    response: Response,
    client_info: ClientInfo = client_info_dependency,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Web user login."""
    tokens = await web_auth_service.login(login_data, client_info)

    response.set_cookie(
        key='refresh_token',
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.auth.refresh_token_ttl,
    )
    response.set_cookie(
        key='csrf_token',
        value=secrets.token_urlsafe(CSRF_LENGTH),
        httponly=False,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.auth.refresh_token_ttl,
    )

    return WebTokens(access_token=tokens.access_token)


@router.post('/logout')
async def logout(
    response: Response,
    session_info: UserSession = current_web_uid_sid_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Current session logout."""
    message = await web_auth_service.logout_user(
        session_info.uid, session_info.sid
    )
    response.delete_cookie('refresh_token')
    response.delete_cookie('csrf_token')

    return {'message': message}


@router.post('/logout_others')
async def logout_other(
    session_info: UserSession = current_web_uid_sid_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Other session logout."""
    return {
        'message': await web_auth_service.logout_others_sessions(
            session_info.uid, session_info.sid
        )
    }


@router.post('/logout_all')
async def logout_all(
    session_info: UserSession = current_web_uid_sid_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """All session logout."""
    return {
        'message': await web_auth_service.logout_all_sessions(session_info.uid)
    }


@router.post('/refresh', response_model=WebTokens)
async def refresh_tokens(
    response: Response,
    refresh_request: RefreshRequestCookie = refresh_request_dep,
    client_info: ClientInfo = client_info_dependency,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Refresh tokens endpoint."""
    tokens = await web_auth_service.refresh_user_tokens(
        refresh_request.refresh_token, client_info
    )
    response.set_cookie(
        key='refresh_token',
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.auth.refresh_token_ttl,
    )
    response.set_cookie(
        key='csrf_token',
        value=secrets.token_urlsafe(CSRF_LENGTH),
        httponly=False,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.auth.refresh_token_ttl,
    )
    return WebTokens(access_token=tokens.access_token)
