from io import BytesIO
from logging import getLogger
from typing import Protocol

from app.constants.image import (
    PILLOW_REQUEUED_MSG,
    UNKNOWN_IMAGE_BACKEND_MSG,
    VIPS_REQUEUED_MSG,
)
from app.exceptions.image import InvalidImageError
from app.logs.image import (
    IMAGE_EXIF_STRIP_ERROR_LOG,
    IMAGE_OPEN_ERROR_LOG,
    IMAGE_ORIENT_ERROR_LOG,
    PILLOW_BACKEND_START_LOG,
    VIPS_BACKEND_START_LOG,
)
from config.config import ImageSettings

logger = getLogger(__name__)


class IImageBackend(Protocol):
    """Image backend protocol."""
    def open(self, file_bytes: bytes):
        """Load image from raw bytes."""

    def orient(self, img):
        """Correct image orientation (EXIF-aware)."""

    def strip(self, img):
        """Remove metadata such as EXIF, IPTC, ICC, XMP."""

    def resize(self, img):
        """Resize the image to configured dimensions."""

    def export_jpeg(self, img) -> bytes:
        """Encode image as JPEG and return bytes."""

    def export_webp(self, img) -> bytes:
        """Encode image as WebP and return bytes."""


class PillowBackend(IImageBackend):
    """Pillow backend."""
    def __init__(self, cfg: ImageSettings):
        """Initialize PillowBackend."""
        try:
            from PIL import Image, ImageOps
        except ImportError:
            raise RuntimeError(PILLOW_REQUEUED_MSG)

        self.cfg = cfg
        self.Image = Image
        self.ImageOps = ImageOps
        self.log = logger
        self.log.info(PILLOW_BACKEND_START_LOG)

    def open(self, file_bytes: bytes):
        """Load image from raw bytes."""
        try:
            img = self.Image.open(BytesIO(file_bytes))
            img.load()
            return img
        except Exception as exc:
            self.log.info(IMAGE_OPEN_ERROR_LOG, str(exc))
            raise InvalidImageError()

    def orient(self, img):
        """Correct image orientation (EXIF-aware)."""
        return self.ImageOps.exif_transpose(img)

    def strip(self, img):
        """Remove metadata such as EXIF, IPTC, ICC, XMP."""
        try:
            img.getexif().clear()
        except Exception as exc:
            self.log.info(IMAGE_EXIF_STRIP_ERROR_LOG, str(exc))

        for field in ('exif', 'iptc', 'icc_profile', 'xmp'):
            img.info.pop(field, None)

        return img

    def resize(self, img):
        """Resize the image to configured dimensions."""
        img = img.copy()
        img.thumbnail(
            (self.cfg.out_width, self.cfg.out_height),
            self.Image.Resampling.LANCZOS,
        )
        return img

    def export_jpeg(self, img):
        """Encode image as JPEG and return bytes."""
        buf = BytesIO()
        img.save(
            buf, format='JPEG', quality=self.cfg.jpeg_quality, optimize=True
        )
        return buf.getvalue()

    def export_webp(self, img):
        """Encode image as WebP and return bytes."""
        buf = BytesIO()
        img.save(buf, format='WEBP', quality=self.cfg.webp_quality, method=6)
        return buf.getvalue()


class VipsBackend(IImageBackend):
    """Vips backend."""
    def __init__(self, cfg: ImageSettings):
        """Initialize VipsBackend."""
        try:
            import pyvips
        except ImportError:
            raise RuntimeError(VIPS_REQUEUED_MSG)

        self.cfg = cfg
        self.vips = pyvips
        self.log = logger
        self.log.info(VIPS_BACKEND_START_LOG)

    def open(self, file_bytes: bytes):
        """Load image from raw bytes."""
        try:
            return self.vips.Image.new_from_buffer(file_bytes, '')
        except Exception as exc:
            self.log.info(IMAGE_OPEN_ERROR_LOG, str(exc))
            raise InvalidImageError()

    def orient(self, img):
        """Correct image orientation (EXIF-aware)."""
        try:
            return img.autorot()
        except Exception as exc:
            self.log.info(IMAGE_ORIENT_ERROR_LOG, str(exc))
            return img

    def strip(self, img):
        """Remove metadata such as EXIF, IPTC, ICC, XMP."""
        for field in img.get_fields():
            lf = field.lower()
            if lf.startswith('exif-') or lf in (
                'exif-data',
                'xmp-data',
                'iptc-data',
                'icc-profile-data',
            ):
                try:
                    img.remove(field)
                except Exception as exc:
                    self.log.info(IMAGE_EXIF_STRIP_ERROR_LOG, str(exc))
        return img

    def resize(self, img):
        """Resize the image to configured dimensions."""
        return img.thumbnail_image(
            self.cfg.out_width, height=self.cfg.out_height, crop='centre'
        )

    def export_jpeg(self, img):
        """Encode image as JPEG and return bytes."""
        return img.write_to_buffer('.jpg', Q=self.cfg.jpeg_quality)

    def export_webp(self, img):
        """Encode image as WebP and return bytes."""
        return img.write_to_buffer('.webp', Q=self.cfg.webp_quality)


def get_backend(cfg: ImageSettings):
    """Get backend."""
    if cfg.backend == 'pillow':
        return PillowBackend(cfg)
    if cfg.backend == 'vips':
        return VipsBackend(cfg)
    raise ValueError(UNKNOWN_IMAGE_BACKEND_MSG.format(name=cfg.backend))
