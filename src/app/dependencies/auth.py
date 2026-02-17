from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status

from app.constants import AuthMessage
from app.schemes import RefreshRequestCookie, UserSession
from app.security import oauth2_dependency
from app.services import (
    LoginType,
    UserService,
    get_bot_auth_service,
    get_telegram_auth_service,
    get_user_service,
    get_web_auth_service,
)


async def get_current_user_id(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: str = oauth2_dependency,
) -> str:
    """Get current user id."""
    return (
        await user_service.check_user_by_type(
            token, {LoginType.web, LoginType.telegram}
        )
    ).uid


async def get_current_user_uid_sid(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: str = oauth2_dependency,
) -> UserSession:
    """Get current user uid sid."""
    return await user_service.check_user_by_type(
        token, {LoginType.web, LoginType.telegram}
    )


async def refresh_request(
    refresh_token: Annotated[str | None, Cookie(alias='refresh_token')] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias='csrf_token')] = None,
    csrf_header: Annotated[str | None, Header(alias='X-CSRF-Token')] = None,
) -> RefreshRequestCookie:
    """Refresh request."""
    if refresh_token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, AuthMessage.missed_refresh_token
        )
    if (
        csrf_cookie is None
        or csrf_header is None
        or csrf_cookie != csrf_header
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, AuthMessage.csrf_validation_failed
        )
    return RefreshRequestCookie(
        refresh_token=refresh_token,
        csrf=csrf_cookie,
    )


async def get_current_web_uid_sid(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: str = oauth2_dependency,
) -> UserSession:
    """Get current web user id."""
    return await user_service.check_user_by_type(token, {LoginType.web})


async def get_current_telegram_uid_sid(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: str = oauth2_dependency,
) -> UserSession:
    """Get current web user id."""
    return await user_service.check_user_by_type(token, {LoginType.telegram})


async def get_current_bot_uid_sid(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: str = oauth2_dependency,
) -> UserSession:
    """Get current bot id."""
    return await user_service.check_user_by_type(token, {LoginType.bot})


current_user_id_dep = Depends(get_current_user_id)
current_user_uid_sid_dep = Depends(get_current_user_uid_sid)

bot_auth_service_dep = Depends(get_bot_auth_service)
telegram_auth_service_dep = Depends(get_telegram_auth_service)
web_auth_service_dep = Depends(get_web_auth_service)

refresh_request_dep = Depends(refresh_request)

current_web_uid_sid_dep = Depends(get_current_web_uid_sid)
current_telegram_uid_sid_dep = Depends(get_current_telegram_uid_sid)
current_bot_uid_sid_dep = Depends(get_current_bot_uid_sid)
