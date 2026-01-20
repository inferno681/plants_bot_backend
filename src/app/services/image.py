from pathlib import Path

import pyvips

from app.exceptions.image import (
    FileTooLargeError,
    InvalidExtensionError,
    InvalidImageError,
    UnsupportedMimeError,
)
from app.schemes import ImageConfig, ImageUpload
from config import config


class ImageValidator:
    def __init__(self, cfg: ImageConfig):
        self.cfg = cfg
        self.allowed_mime = {mime.lower() for mime in cfg.allowed_mime}

    def validate(self, filename, content_type, file_bytes):
        self._mime(content_type)
        self._ext(filename)
        self._size(file_bytes)

    def _mime(self, content_type):
        mime = content_type.split(';', 1)[0].strip().lower()
        if mime not in self.allowed_mime:
            raise UnsupportedMimeError(mime)

    def _ext(self, filename):
        ext = Path(filename).suffix.lower()
        if ext not in self.cfg.allowed_ext:
            raise InvalidExtensionError(ext)

    def _size(self, file_bytes):
        if len(file_bytes) > self.cfg.max_size_bytes:
            raise FileTooLargeError(len(file_bytes))


class VipsProcessor:
    def __init__(self, cfg: ImageConfig):
        self.cfg = cfg

    def open_safe(self, file_bytes: bytes) -> pyvips.Image:
        try:
            img = pyvips.Image.new_from_buffer(file_bytes, '')
        except Exception:
            raise InvalidImageError()

        width, height = img.width, img.height

        if (
            width > self.cfg.max_input_width
            or height > self.cfg.max_input_height
        ):
            raise InvalidImageError(f'Image too large: {width}x{height}')
        pixels = width * height
        if pixels > self.cfg.max_input_pixels:
            raise InvalidImageError(f'Image too large: {pixels} pixels')

        return img

    @staticmethod
    def orient(img: pyvips.Image) -> pyvips.Image:
        try:
            return img.autorot()
        except Exception:
            return img

    @staticmethod
    def strip_meta(img: pyvips.Image) -> pyvips.Image:
        return img.copy(strip=True)

    def resize(self, img: pyvips.Image) -> pyvips.Image:
        return img.thumbnail_image(
            self.cfg.out_width, height=self.cfg.out_height, crop='centre'
        )

    def process(self, img: pyvips.Image) -> pyvips.Image:
        img = self.orient(img)
        img = self.strip_meta(img)
        img = self.resize(img)
        return img


class VipsExporter:
    def __init__(self, cfg: ImageConfig):
        self.cfg = cfg

    def export_jpeg(self, img: pyvips.Image) -> bytes:
        return img.write_to_buffer('.jpg', Q=self.cfg.jpeg_quality)

    def export_webp(self, img: pyvips.Image) -> bytes:
        return img.write_to_buffer('.webp', Q=self.cfg.webp_quality)


class ImageService:
    def __init__(self, cfg: ImageConfig):
        self.validator = ImageValidator(cfg)
        self.processor = VipsProcessor(cfg)
        self.exporter = VipsExporter(cfg)

    def process(
        self,
        file_info: ImageUpload,
        as_webp: bool = False,
    ):
        self.validator.validate(
            file_info.filename, file_info.content_type, file_info.file_bytes
        )
        img = self.processor.open_safe(file_info.file_bytes)
        img = self.processor.process(img)
        if as_webp:
            return self.exporter.export_webp(img), '.webp'
        else:
            return self.exporter.export_jpeg(img), '.jpg'


image_service = ImageService(ImageConfig(**config.image.model_dump()))
