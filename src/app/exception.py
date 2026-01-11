class UserAlreadyExistsError(Exception):
    """User with this email already exists."""


class InvalidTokenError(Exception):
    """The provided token is invalid or has expired."""
