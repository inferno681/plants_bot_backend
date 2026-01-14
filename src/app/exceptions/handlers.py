from logging import getLogger

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.constants import DETAIL, LOC, MSG, STATUS, TYPE
from app.exceptions.auth import AUTH_ERROR_MAP, AuthError
from app.exceptions.token import TOKEN_MAP, TokenError

logger = getLogger(__name__)


async def token_exception_handler(request: Request, exc: TokenError):
    """Token errors handler."""
    error_info = TOKEN_MAP.get(
        type(exc),
        {
            MSG: 'token.error',
            TYPE: 'token_error',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
    )

    return JSONResponse(
        status_code=error_info[STATUS],
        content={
            DETAIL: [
                {
                    LOC: ['token'],
                    MSG: error_info[MSG],
                    TYPE: error_info[TYPE],
                }
            ]
        },
    )


async def auth_exception_handler(request: Request, exc: AuthError):
    """Auth errors handler."""
    error_info = AUTH_ERROR_MAP.get(
        type(exc),
        {
            MSG: 'auth.error',
            TYPE: 'auth_error',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
    )

    return JSONResponse(
        status_code=error_info[STATUS],
        content={
            DETAIL: [
                {
                    LOC: ['auth'],
                    MSG: error_info[MSG],
                    TYPE: error_info[TYPE],
                }
            ]
        },
    )


async def exception_handler(request: Request, exc: Exception):
    """Generic exceptions handler (HTTP 500)."""
    logger.exception('Unhandled server error', exc_info=exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            DETAIL: [
                {
                    LOC: ['server'],
                    MSG: 'internal.server.error',
                    TYPE: 'internal_error',
                }
            ]
        },
    )


exception_handlers = {
    TokenError: token_exception_handler,
    AuthError: auth_exception_handler,
    Exception: exception_handler,
}
