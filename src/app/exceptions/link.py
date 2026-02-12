from types import MappingProxyType
from typing import Any, Type

from fastapi import status

from app.constants import MSG, STATUS, TYPE


class LinkException(Exception):
    """Base link exception."""


class CodeAllocationError(LinkException):
    """Failed to issue unique linking code."""


class TelegramConnectError(LinkException):
    """Telegram account already connected."""


class InvalidCodeProvided(LinkException):
    """Invalid code for telegram link provided."""


class AlreadyLinkedError(LinkException):
    """Account already linked error."""


class BusyError(LinkException):
    """Redis lock error."""


LINK_ERROR_MAP: MappingProxyType[Type[LinkException], dict[str, Any]] = (
    MappingProxyType(
        {
            CodeAllocationError: {
                MSG: 'link.code_allocation_error',
                TYPE: 'code_allocation_error',
                STATUS: status.HTTP_503_SERVICE_UNAVAILABLE,
            },
            TelegramConnectError: {
                MSG: 'link.telegram_already_connected',
                TYPE: 'telegram_already_connected',
                STATUS: status.HTTP_409_CONFLICT,
            },
            InvalidCodeProvided: {
                MSG: 'link.invalid_code',
                TYPE: 'invalid_code',
                STATUS: status.HTTP_400_BAD_REQUEST,
            },
            AlreadyLinkedError: {
                MSG: 'link.already_linked',
                TYPE: 'already_linked',
                STATUS: status.HTTP_409_CONFLICT,
            },
            BusyError: {
                MSG: 'link.busy',
                TYPE: 'busy',
                STATUS: status.HTTP_423_LOCKED,
            },
        }
    )
)
