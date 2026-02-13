from logging import getLogger
from typing import Any, Callable, Coroutine, Type

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.constants import DETAIL, LOC, MSG, STATUS, TYPE
from app.exceptions.auth import AUTH_ERROR_MAP, AuthError
from app.exceptions.email import EMAIL_ERROR_MAP, EmailError
from app.exceptions.image import IMAGE_ERROR_MAP, ImageError
from app.exceptions.link import LINK_ERROR_MAP, LinkException
from app.exceptions.plant import PLANT_ERROR_MAP, InvalidPlantDataError
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


async def email_exception_handler(request: Request, exc: EmailError):
    """Email errors handler."""
    error_info = EMAIL_ERROR_MAP.get(
        type(exc),
        {
            MSG: 'email.error',
            TYPE: 'email_error',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
    )

    return JSONResponse(
        status_code=error_info[STATUS],
        content={
            DETAIL: [
                {
                    LOC: ['email'],
                    MSG: error_info[MSG],
                    TYPE: error_info[TYPE],
                }
            ]
        },
    )


async def link_exception_handler(request: Request, exc: LinkException):
    """Link errors handler."""
    error_info = LINK_ERROR_MAP.get(
        type(exc),
        {
            MSG: 'link.error',
            TYPE: 'link_error',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
    )

    return JSONResponse(
        status_code=error_info[STATUS],
        content={
            DETAIL: [
                {
                    LOC: ['link'],
                    MSG: error_info[MSG],
                    TYPE: error_info[TYPE],
                }
            ]
        },
    )


async def plant_exception_handler(
    request: Request, exc: InvalidPlantDataError
):
    """Plant data errors handler."""
    error_info = PLANT_ERROR_MAP.get(
        type(exc),
        {
            MSG: 'plant.error',
            TYPE: 'plant_error',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
    )

    return JSONResponse(
        status_code=error_info[STATUS],
        content={
            DETAIL: [
                {
                    LOC: ['plant'],
                    MSG: error_info[MSG],
                    TYPE: error_info[TYPE],
                }
            ]
        },
    )


async def pydantic_validation_error_handler(request, exc: ValidationError):
    """Pydantic validation error handler."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            DETAIL: [
                {
                    LOC: ['model'],
                    MSG: exc.errors(),
                    TYPE: 'validation_error',
                }
            ]
        },
    )


ExceptionHandler = Callable[[Request, Any], Coroutine[Any, Any, Response]]
exception_handlers: dict[int | Type[Exception], ExceptionHandler] = {
    TokenError: token_exception_handler,
    AuthError: auth_exception_handler,
    ImageError: image_exception_handler,
    EmailError: email_exception_handler,
    LinkException: link_exception_handler,
    InvalidPlantDataError: plant_exception_handler,
    ValidationError: pydantic_validation_error_handler,
    Exception: exception_handler,
}
