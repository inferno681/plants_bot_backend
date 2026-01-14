from types import MappingProxyType
from typing import Any, Type

from fastapi import status

from app.constants import MSG, STATUS, TYPE


class AuthError(Exception):
    """Base auth error."""


class UserNotFoundError(AuthError):
    """User not found error."""


class UserAlreadyExistsError(AuthError):
    """User already exist."""


class InvalidCredentialsError(AuthError):
    """Invalid credentials error."""


class InvalidInitDataError(AuthError):
    """Invalid init data."""


class InvalidSignatureError(AuthError):
    """Invalid signature."""


class InvalidPasswordError(AuthError):
    """Invalid password provided."""


AUTH_ERROR_MAP: MappingProxyType[Type[AuthError], dict[str, Any]] = (
    MappingProxyType(
        {
            UserNotFoundError: {
                MSG: 'auth.user_not_found',
                TYPE: 'user_not_found',
                STATUS: status.HTTP_404_NOT_FOUND,
            },
            UserAlreadyExistsError: {
                MSG: 'auth.user_already_exists',
                TYPE: 'user_already_exists',
                STATUS: status.HTTP_409_CONFLICT,
            },
            InvalidCredentialsError: {
                MSG: 'auth.invalid_credentials',
                TYPE: 'invalid_credentials',
                STATUS: status.HTTP_401_UNAUTHORIZED,
            },
            InvalidPasswordError: {
                MSG: 'auth.invalid_password',
                TYPE: 'invalid_password',
                STATUS: status.HTTP_401_UNAUTHORIZED,
            },
            InvalidInitDataError: {
                MSG: 'auth.invalid_init_data',
                TYPE: 'invalid_init_data',
                STATUS: status.HTTP_400_BAD_REQUEST,
            },
            InvalidSignatureError: {
                MSG: 'auth.invalid_signature',
                TYPE: 'invalid_signature',
                STATUS: status.HTTP_401_UNAUTHORIZED,
            },
        }
    )
)
