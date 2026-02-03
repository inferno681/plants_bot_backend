from logging import basicConfig, getLogger
from redis.asyncio import ConnectionPool
from taskiq import SmartRetryMiddleware, TaskiqEvents, TaskiqState
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from app.logs.tasks import BROKER_START_LOG
from config import config

log = getLogger(__name__)
broker = RedisStreamBroker(
    config.redis_url(config.redis.taskiq_db)
).with_result_backend(
    RedisAsyncResultBackend(config.redis_url(config.redis.results_db))
)
broker.add_middlewares(SmartRetryMiddleware())


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def on_worker_startup(state: TaskiqState) -> None:
    """Worker startup settings."""
    basicConfig(
        level=config.logger.level,
        format=config.logger.format,
        datefmt=config.logger.date_format,
    )
    state.redis = ConnectionPool.from_url(
        config.redis_url(config.redis.queue_db)
    )
    log.info(BROKER_START_LOG, state)


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    """Worker shutdown settings."""
    await state.redis.disconnect()
