from redis.asyncio.client import Redis


def init_redis(
    url: str,
    db: int,
    password: str,
    decode_responses: bool,
) -> Redis:
    """Create redis client."""
    return Redis.from_url(
        url=url,
        db=db,
        password=password,
        decode_responses=decode_responses,
    )  # type: ignore[call-overload]
