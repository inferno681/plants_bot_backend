from types import MappingProxyType
from typing import Any, Type

from fastapi import status

from app.constants import MSG, STATUS, TYPE


class ImageError(Exception):
    """Base image processing error."""


class UnsupportedMimeError(ImageError):
    """The provided MIME type is not supported."""


class InvalidExtensionError(ImageError):
    """The file extension is not allowed."""


class FileTooLargeError(ImageError):
    """The file size exceeds the allowed maximum."""


class InvalidImageError(ImageError):
    """The file is not a valid or decodable image."""


IMAGE_ERROR_MAP: MappingProxyType[Type[ImageError], dict[str, Any]] = (
    MappingProxyType(
        {
            UnsupportedMimeError: {
                MSG: 'image.unsupported_mime',
                TYPE: 'unsupported_mime',
                STATUS: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            },
            InvalidExtensionError: {
                MSG: 'image.invalid_extension',
                TYPE: 'invalid_extension',
                STATUS: status.HTTP_400_BAD_REQUEST,
            },
            FileTooLargeError: {
                MSG: 'image.file_too_large',
                TYPE: 'file_too_large',
                STATUS: status.HTTP_413_CONTENT_TOO_LARGE,
            },
            InvalidImageError: {
                MSG: 'image.invalid_image',
                TYPE: 'invalid_image',
                STATUS: status.HTTP_422_UNPROCESSABLE_CONTENT,
            },
        }
    )
)
