from redis.asyncio.client import Redis
from config import config

redis = Redis.from_url(
    config.redis_url,
    db=config.redis.db,
    decode_responses=config.redis.decode_responses,
    password=config.secrets.redis_password.get_secret_value(),
)
