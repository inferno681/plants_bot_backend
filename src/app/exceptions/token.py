from types import MappingProxyType
from typing import Any, Type

from fastapi import status

from app.constants import MSG, STATUS, TYPE


class TokenError(Exception):
    """Base token error."""


class TokenExpiredError(TokenError):
    """Token has expired."""


class TokenInvalidError(TokenError):
    """Token is invalid or malformed."""


class TokenReplayError(TokenError):
    """Refresh token replay detected."""


class TokenInvalidOwnerError(TokenError):
    """Token owner mismatch."""


class TokenRevokedError(TokenError):
    """Token has been revoked."""


class TokenIntegrityError(TokenError):
    """Token has security problem."""


TOKEN_MAP: MappingProxyType[Type[TokenError], dict[str, Any]] = (
    MappingProxyType(
        {
            TokenExpiredError: {
                MSG: 'token.expired',
                TYPE: 'expired',
                STATUS: status.HTTP_401_UNAUTHORIZED,
            },
            TokenInvalidError: {
                MSG: 'token.invalid',
                TYPE: 'invalid',
                STATUS: status.HTTP_401_UNAUTHORIZED,
            },
            TokenReplayError: {
                MSG: 'token.replay',
                TYPE: 'replay',
                STATUS: status.HTTP_401_UNAUTHORIZED,
            },
            TokenInvalidOwnerError: {
                MSG: 'token.owner_mismatch',
                TYPE: 'owner',
                STATUS: status.HTTP_403_FORBIDDEN,
            },
            TokenRevokedError: {
                MSG: 'token.revoked',
                TYPE: 'revoked',
                STATUS: status.HTTP_401_UNAUTHORIZED,
            },
            TokenIntegrityError: {
                MSG: 'token.integrity',
                TYPE: 'integrity',
                STATUS: status.HTTP_400_BAD_REQUEST,
            },
        }
    )
)
