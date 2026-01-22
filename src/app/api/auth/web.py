import secrets
from typing import Annotated

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.asynchronous.client_session import AsyncClientSession

from app.constants.auth import (
    COOKIE_PATH,
    CSRF_LENGTH,
    CSRF_VALIDATION_FAILED_MSG,
    LAX_LITERAL,
    MISSING_REFRESH_TOKEN,
)
from app.db import session_dependency
from app.schemes import (
    ClientInfo,
    UserSession,
    WebAccountLogin,
    WebAccountRegistration,
    WebTokens,
    WebUser,
)
from app.services import (
    current_user_id_dependency,
    current_user_uid_sid_dependency,
    web_auth_service,
)
from app.utils import client_info_dependency
from config import config

router = APIRouter()


@router.post('/login_doc', response_model=WebTokens)
async def doc_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    client_info: ClientInfo = client_info_dependency,
):
    """Documentation user login endpoint."""
    tokens = await web_auth_service.login_doc(form_data.password, client_info)
    return WebTokens(access_token=tokens.access_token)


@router.post('/registration', response_model=WebUser)
async def web_registration(
    user_data: WebAccountRegistration,
    session: AsyncClientSession = session_dependency,
):
    """Web user registration."""
    return await web_auth_service.registration_web_user(user_data, session)


@router.post('/login', response_model=WebTokens)
async def login(
    login_data: WebAccountLogin,
    response: Response,
    client_info: ClientInfo = client_info_dependency,
):
    """Web user login."""
    tokens = await web_auth_service.login(login_data, client_info)

    response.set_cookie(
        key='refresh_token',
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.service.refresh_token_ttl,
        path=COOKIE_PATH,
    )
    response.set_cookie(
        key='csrf_token',
        value=secrets.token_urlsafe(CSRF_LENGTH),
        httponly=False,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.service.refresh_token_ttl,
        path=COOKIE_PATH,
    )

    return WebTokens(access_token=tokens.access_token)


@router.post('/logout')
async def logout(
    response: Response,
    session_info: UserSession = current_user_uid_sid_dependency,
):
    """Current session logout."""
    message = await web_auth_service.logout_user(
        session_info.uid, session_info.sid
    )
    response.delete_cookie('refresh_token', path=COOKIE_PATH)
    response.delete_cookie('csrf_token', path=COOKIE_PATH)

    return {'message': message}


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


@router.post('/refresh', response_model=WebTokens)
async def refresh_tokens(
    response: Response,
    csrf_cookie: Annotated[str | None, Cookie(alias='csrf_token')] = None,
    csrf_header: Annotated[str | None, Header(alias='X-CSRF-Token')] = None,
    refresh_token: Annotated[str | None, Cookie(alias='refresh_token')] = None,
    client_info: ClientInfo = client_info_dependency,
):
    """Refresh tokens endpoint."""
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MISSING_REFRESH_TOKEN,
        )
    if (
        csrf_cookie is None
        or csrf_header is None
        or csrf_cookie != csrf_header
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CSRF_VALIDATION_FAILED_MSG,
        )
    tokens = await web_auth_service.refresh_user_tokens(
        refresh_token, client_info
    )
    response.set_cookie(
        key='refresh_token',
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.service.refresh_token_ttl,
        path=COOKIE_PATH,
    )
    response.set_cookie(
        key='csrf_token',
        value=secrets.token_urlsafe(CSRF_LENGTH),
        httponly=False,
        secure=True,
        samesite=LAX_LITERAL,
        max_age=config.service.access_token_ttl,
        path=COOKIE_PATH,
    )
    return WebTokens(access_token=tokens.access_token)
