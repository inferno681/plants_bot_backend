import asyncio
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from pathlib import Path

from app.exceptions.image import (
    FileTooLargeError,
    InvalidExtensionError,
    UnsupportedMimeError,
)
from app.logs.image import (
    FILE_TOO_LARGE_LOG,
    IMAGE_SERVICE_START_LOG,
    IMAGE_VALIDATOR_START_LOG,
    UNSUPPORTED_EXT_LOG,
    UNSUPPORTED_MIME_LOG,
)
from app.schemes import ImageConfig, ImageUpload
from app.services.image_backend import get_backend
from config import config

logger = getLogger(__name__)
image_pool = ThreadPoolExecutor(max_workers=8)


class ImageValidator:
    def __init__(self, cfg: ImageConfig):
        self.cfg = cfg
        self.allowed_mime = cfg.allowed_mime
        self.allowed_ext = cfg.allowed_ext
        self.log = logger
        self.log.info(IMAGE_VALIDATOR_START_LOG)

    def validate(self, filename, content_type, file_bytes):
        """Base image validation."""
        mime = content_type.split(';', 1)[0].strip().lower()
        if mime not in self.allowed_mime:
            self.log.info(UNSUPPORTED_MIME_LOG, mime)
            raise UnsupportedMimeError(mime)

        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_ext:
            self.log.info(UNSUPPORTED_EXT_LOG, ext)
            raise InvalidExtensionError(ext)

        if len(file_bytes) > self.cfg.max_size_bytes:
            self.log.info(FILE_TOO_LARGE_LOG, len(file_bytes))
            raise FileTooLargeError(len(file_bytes))


class ImageService:
    def __init__(self, cfg: ImageConfig):
        self.cfg = cfg
        self.backend = get_backend(cfg)
        self.validator = ImageValidator(cfg)
        self.image_pool = ThreadPoolExecutor(max_workers=cfg.max_workers)
        self.log = logger
        self.log.info(IMAGE_SERVICE_START_LOG)

    async def process(self, file_info: ImageUpload, as_webp: bool = False):
        """Image file processing."""
        self.validator.validate(
            file_info.filename, file_info.content_type, file_info.file_bytes
        )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.image_pool, self._process_sync, file_info, as_webp
        )

    def _process_sync(self, file_info, as_webp):
        """Image file processing."""
        img = self.backend.open(file_info.file_bytes)
        img = self.backend.orient(img)
        img = self.backend.strip(img)
        img = self.backend.resize(img)

        if as_webp:
            return self.backend.export_webp(img), '.webp'
        return self.backend.export_jpeg(img), '.jpg'


image_service = ImageService(ImageConfig(**config.image.model_dump()))
