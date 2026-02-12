from redis.asyncio.client import Redis


def init_redis(
    url: str,
    password: str,
    decode_responses: bool,
) -> Redis:
    """Create redis client."""
    return Redis.from_url(
        url=url,
        password=password,
        decode_responses=decode_responses,
    )  # type: ignore[call-overload]
