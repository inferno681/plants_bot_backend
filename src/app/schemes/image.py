from pydantic import BaseModel


class ImageConfig(BaseModel):
    """Image service config."""

    allowed_mime: set[str]
    allowed_ext: set[str]
    max_size_bytes: int

    out_width: int
    out_height: int
    jpeg_quality: int = 85
    webp_quality: int = 80

    max_input_width: int = 4096
    max_input_height: int = 4096
    max_input_pixels: int = 20_000_000


class ImageUpload(BaseModel):
    """Uploaded image scheme."""

    file_bytes: bytes
    filename: str
    content_type: str
