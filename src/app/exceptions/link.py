class LinkException(Exception):
    """Base link exception."""


class CodeAllocationError(LinkException):
    """Failed to issue unique linking code."""


class TelegramConnectError(LinkException):
    """Telegram account already connected."""


class InvalidCodeProvided(LinkException):
    """Invalid code for telegram link provided."""


class SecondLinkAttempt(LinkException):
    """Telegram already linked."""


class AlreadyLinkedError(LinkException):
    """Account already linked error."""


class BusyError(LinkException):
    """Redis lock error."""
