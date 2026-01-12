from redis.asyncio.client import Redis

from config import config

redis = Redis.from_url(
    url=config.redis_url,
    db=config.redis.db,
    password=config.secrets.redis_password.get_secret_value(),
    decode_responses=config.redis.decode_responses,
)  # type: ignore[call-overload]
