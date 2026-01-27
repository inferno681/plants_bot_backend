class UserException(Exception):
    """Base user exception."""


class CodeAllocationError(UserException):
    """Failed to issue unique linking code."""


class TelegramConnectError(UserException):
    """Telegram account already connected."""


class InvalidCodeProvided(UserException):
    """Invalid code for telegram link provided."""


class SecondLinkAttempt(UserException):
    """Telegram already linked."""


class BusyError(UserException):
    """Redis lock error."""
