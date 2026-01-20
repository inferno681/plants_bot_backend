from logging import getLogger
from typing import Any, Callable, Coroutine, Type

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.constants import DETAIL, LOC, MSG, STATUS, TYPE
from app.exceptions.auth import AUTH_ERROR_MAP, AuthError
from app.exceptions.image import IMAGE_ERROR_MAP, ImageError
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


async def image_exception_handler(request: Request, exc: ImageError):
    """Image errors handler."""
    error_info = IMAGE_ERROR_MAP.get(
        type(exc),
        {
            MSG: 'image.error',
            TYPE: 'image_error',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
    )

    return JSONResponse(
        status_code=error_info[STATUS],
        content={
            DETAIL: [
                {
                    LOC: ['image'],
                    MSG: error_info[MSG],
                    TYPE: error_info[TYPE],
                }
            ]
        },
    )


ExceptionHandler = Callable[[Request, Any], Coroutine[Any, Any, Response]]
exception_handlers: dict[int | Type[Exception], ExceptionHandler] = {
    TokenError: token_exception_handler,
    AuthError: auth_exception_handler,
    ImageError: image_exception_handler,
    Exception: exception_handler,
}
