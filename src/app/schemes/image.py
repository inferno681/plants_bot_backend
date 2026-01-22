from pydantic import BaseModel


class ImageUpload(BaseModel):
    """Uploaded image scheme."""

    file_bytes: bytes
    filename: str
    content_type: str
