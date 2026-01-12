class UserAlreadyExistsError(Exception):
    """User with this email already exists."""


class InvalidTokenError(Exception):
    """The provided token is invalid or has expired."""


class PermissionDeniedError(Exception):
    """The user does not have permission to perform this action."""


class InvalidCredentialsError(Exception):
    """The provided credentials are invalid."""


class UserNotFoundError(Exception):
    """The specified user was not found."""


class InvalidSignatureError(Exception):
    """The provided signature is invalid."""


class InvalidInitDataError(Exception):
    """The provided init_data is invalid."""


class InvalidPasswordError(Exception):
    """Invalid password provided."""
