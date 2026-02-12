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
