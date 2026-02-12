from types import MappingProxyType
from typing import Any, Type

from fastapi import status

from app.constants import MSG, STATUS, TYPE


class EmailError(Exception):
    """Base class for email-related exceptions."""


class EmailNotSetError(EmailError):
    """Raised when a user does not have an email set."""


class InvalidTokenError(EmailError):
    """Raised when an invalid token is provided."""


class TokenAlreadyUsedError(EmailError):
    """Raised when a token has already been used."""


class EmailAlreadyConfirmedError(EmailError):
    """Raised when an email already confirmed."""


class EmailNotConfirmedError(EmailError):
    """Raise when an email not confirmed."""


EMAIL_ERROR_MAP: MappingProxyType[Type[EmailError], dict[str, Any]] = (
    MappingProxyType(
        {
            EmailNotSetError: {
                MSG: 'email.not_set',
                TYPE: 'email_not_set',
                STATUS: status.HTTP_400_BAD_REQUEST,
            },
            InvalidTokenError: {
                MSG: 'email.invalid_token',
                TYPE: 'invalid_token',
                STATUS: status.HTTP_400_BAD_REQUEST,
            },
            TokenAlreadyUsedError: {
                MSG: 'email.token_already_used',
                TYPE: 'token_already_used',
                STATUS: status.HTTP_409_CONFLICT,
            },
            EmailAlreadyConfirmedError: {
                MSG: 'email.already_confirmed',
                TYPE: 'email_already_confirmed',
                STATUS: status.HTTP_409_CONFLICT,
            },
            EmailNotConfirmedError: {
                MSG: 'email.not_confirmed',
                TYPE: 'email_not_confirmed',
                STATUS: status.HTTP_403_FORBIDDEN,
            },
        }
    )
)
