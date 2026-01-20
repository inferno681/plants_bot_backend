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
