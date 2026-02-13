from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status

from app.constants.auth import (
    CSRF_VALIDATION_FAILED_MSG,
    MISSING_REFRESH_TOKEN,
)
from app.schemes import RefreshRequestCookie, UserSession
from app.security import oauth2_dependency
from app.services import (
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
    return await user_service.get_current_user_id(token)


async def get_current_user_uid_sid(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: str = oauth2_dependency,
) -> UserSession:
    """Get current user uid sid."""
    return await user_service.get_current_user_uid_sid(token)


async def refresh_request(
    refresh_token: Annotated[str | None, Cookie(alias='refresh_token')] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias='csrf_token')] = None,
    csrf_header: Annotated[str | None, Header(alias='X-CSRF-Token')] = None,
) -> RefreshRequestCookie:
    """Refresh request."""
    if refresh_token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, MISSING_REFRESH_TOKEN
        )
    if (
        csrf_cookie is None
        or csrf_header is None
        or csrf_cookie != csrf_header
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, CSRF_VALIDATION_FAILED_MSG
        )
    return RefreshRequestCookie(
        refresh_token=refresh_token,
        csrf=csrf_cookie,
    )


current_user_id_dep = Depends(get_current_user_id)
current_user_uid_sid_dep = Depends(get_current_user_uid_sid)

bot_auth_service_dep = Depends(get_bot_auth_service)
telegram_auth_service_dep = Depends(get_telegram_auth_service)
web_auth_service_dep = Depends(get_web_auth_service)

refresh_request_dep = Depends(refresh_request)
