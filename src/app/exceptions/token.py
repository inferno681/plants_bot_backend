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
