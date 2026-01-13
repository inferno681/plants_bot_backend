import asyncio
import random
from contextlib import asynccontextmanager
from typing import AsyncIterator

from beanie import init_beanie
from fastapi import Depends
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.models import Bot, Plant, TelegramAccount, User, WebAccount
from config import config


class DbHelper:
    """Database helper with transaction support and retry logic."""

    def __init__(
        self,
        client: AsyncMongoClient,
        max_retries: int = 3,
        backoff_base: float = 0.05,
        backoff_jitter: float = 0.05,
    ):
        self.client = client
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_jitter = backoff_jitter

    async def init_db(self):
        await init_beanie(
            database=self.client[config.mongodb.db],
            document_models=[User, WebAccount, TelegramAccount, Plant, Bot],
        )

    async def transaction(self) -> AsyncIterator:
        """Transaction context manager with retry logic."""
        attempt = 0

        while True:
            try:
                async with self._transaction_block() as session:
                    yield session
                    return

            except PyMongoError as exc:
                if not self._should_retry(exc, attempt):
                    raise

                await asyncio.sleep(self._backoff(attempt))
                attempt += 1

    @asynccontextmanager
    async def _transaction_block(self):
        """Transaction block context manager."""
        async with self.client.start_session() as session:
            async with await session.start_transaction():
                yield session

    def _should_retry(self, exc: PyMongoError, attempt: int) -> bool:
        """Returns True if the operation should be retried."""
        if attempt >= self.max_retries - 1:
            return False

        return exc.has_error_label(
            'TransientTransactionError'
        ) or exc.has_error_label('UnknownTransactionCommitResult')

    def _backoff(self, attempt: int) -> float:
        """Calculates backoff time with jitter."""
        return self.backoff_base * (2**attempt) + random.uniform(
            0, self.backoff_jitter
        )


db_helper = DbHelper(
    client=AsyncMongoClient(config.mongo_url_dev),
    max_retries=config.mongodb.max_retries,
    backoff_base=config.mongodb.backoff_base,
    backoff_jitter=config.mongodb.backoff_jitter,
)

session_dependency = Depends(db_helper.transaction)
