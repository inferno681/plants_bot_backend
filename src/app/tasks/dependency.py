from typing import Annotated
from redis.asyncio import Redis
from taskiq import Context, TaskiqDepends
from config import config


def redis_dep(context: Annotated[Context, TaskiqDepends()]) -> Redis:
    return Redis(
        connection_pool=context.state.redis,
        decode_responses=config.redis.decode_responses,
    )
