import os
from contextlib import asynccontextmanager
from logging import getLogger

from aioboto3 import Session

from app.log_messages import STORAGE_UTIL_STARTED_LOG
from app.models import Plant


class S3StorageService:
    """Service for interacting with S3 storage using aioboto3."""

    def __init__(
        self,
        bucket: str,
        endpoint_url: str,
        aws_access_key: str,
        aws_secret_key: str,
    ):
        """S3StorageService initialization."""
        self.bucket = bucket
        self.session = Session()
        self.endpoint_url = endpoint_url
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.log = getLogger(__name__)

        self.log.info(STORAGE_UTIL_STARTED_LOG)

    async def download_file(self, storage_key: str) -> bytes:
        """Download a file from S3 storage."""
        async with self._s3_client() as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=storage_key)
            return await response['Body'].read()

    async def generate_presigned_url(
        self, storage_key: str, filename: str, expires: int = 300
    ) -> str:
        """Generate a presigned URL for downloading a file from S3 storage."""
        async with self._s3_client() as s3:
            return await s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': storage_key,
                    'ResponseContentDisposition': (
                        f'attachment; filename="{filename}"'
                    ),
                },
                ExpiresIn=expires,
            )

    async def presigned_url_for_plant(self, plant: Plant) -> str | None:
        """Presigned url generation."""
        if not plant.storage_key:
            return None

        ext = os.path.splitext(plant.storage_key)[1] or '.jpg'
        filename = f"{plant.name}{ext}"

        return await self.generate_presigned_url(
            storage_key=plant.storage_key,
            filename=filename,
        )

    async def upload_file(self, storage_key: str, file_bytes: bytes):
        """Upload a file to S3 storage."""
        async with self._s3_client() as s3:
            await s3.put_object(
                Bucket=self.bucket, Key=storage_key, Body=file_bytes
            )

    async def delete_file(self, storage_key: str):
        """Delete a file from S3 storage."""
        async with self._s3_client() as s3:
            await s3.delete_object(Bucket=self.bucket, Key=storage_key)

    @asynccontextmanager
    async def _s3_client(self):
        """Client in contextmanager."""
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.aws_secret_key,
            aws_access_key_id=self.aws_access_key,
        ) as s3:
            yield s3
