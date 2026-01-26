class UserException(Exception):
    """Base user exception."""


class CodeAllocationError(UserException):
    """Failed to issue unique linking code."""
