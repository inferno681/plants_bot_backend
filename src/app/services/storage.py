from contextlib import asynccontextmanager
from logging import getLogger

from aioboto3 import Session  # type: ignore

from app.log_messages import STORAGE_UTIL_STARTED_LOG
from config import config


class S3StorageService:
    """Service for interacting with S3 storage using aioboto3."""

    def __init__(self):
        """S3StorageService initialization."""
        self.bucket = config.storage.bucket
        self.session = Session()
        self.endpoint_url = config.storage.endpoint_url
        self.aws_access_key = config.secrets.aws_access_key.get_secret_value()
        self.aws_secret_key = config.secrets.aws_secret_key.get_secret_value()
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

    @asynccontextmanager
    async def _s3_client(self):
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.aws_secret_key,
            aws_access_key_id=self.aws_access_key,
        ) as s3:
            yield s3


storage_service = S3StorageService()
