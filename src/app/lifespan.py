from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI
from pymongo import AsyncMongoClient
from redis.asyncio import Redis

from app import services
from app.db import init_db_helper
from app.redis_service import init_redis
from config import config, setup_logging

logger = getLogger(__name__)


def init_auth(
    app: FastAPI, redis: Redis, pipeline_builder: services.MongoPipelineBuilder
):
    """Auth services initialization."""

    token_service = services.TokenService(
        provider=services.TokenProvider(
            access_secret=(
                config.secrets.access_token_secret.get_secret_value()
            ),
            refresh_secret=(
                config.secrets.refresh_token_secret.get_secret_value()
            ),
            access_ttl=config.auth.access_token_ttl,
            refresh_ttl=config.auth.refresh_token_ttl,
        ),
        store=services.SessionStore(
            redis=redis,
            refresh_ttl=config.auth.refresh_token_ttl,
            max_session=config.auth.max_sessions_per_user,
        ),
    )
    services.init_web_auth_service(
        app=app,
        token_service=token_service,
        doc_pass=config.secrets.doc_password.get_secret_value(),
    )
    init_data_checker = services.InitDataChecker(
        secret=config.secrets.bot_token.get_secret_value(),
        user_init_data_ttl=config.auth.user_init_data_ttl,
        bot_init_data_ttl=config.auth.bot_init_data_ttl,
        skew=config.auth.init_data_skew,
    )
    services.init_telegram_auth_service(
        app=app,
        token_service=token_service,
        init_data_checker=init_data_checker,
    )
    services.init_bot_auth_service(
        app=app,
        token_service=token_service,
        init_data_checker=init_data_checker,
    )
    services.init_user_service(
        app=app,
        token_service=token_service,
        pipeline_builder=pipeline_builder,
        redis=redis,
        link_ttl=config.service.link_ttl,
    )


async def init_mongo(app: FastAPI):
    """Db initialization."""
    db_helper = init_db_helper(
        app=app,
        client=AsyncMongoClient(config.mongo_url),
        db=config.mongodb.db,
        max_retries=config.mongodb.max_retries,
        backoff_base=config.mongodb.backoff_base,
        backoff_jitter=config.mongodb.backoff_jitter,
    )
    await db_helper.init_db()
    logger.info('db initialized')
    return db_helper


def init_plant(app: FastAPI, pipeline_builder: services.MongoPipelineBuilder):
    """Plant services initialization."""
    storage = services.S3StorageService(
        bucket=config.storage.bucket,
        endpoint_url=config.storage.endpoint_url,
        aws_access_key=config.secrets.aws_access_key.get_secret_value(),
        aws_secret_key=config.secrets.aws_secret_key.get_secret_value(),
    )
    services.init_plant_mapper(app=app, storage=storage)
    image_service = services.ImageService(config.image)
    services.init_plant_service(
        app,
        scheduler=services.Scheduler(),
        pipeline_builder=pipeline_builder,
        image_service=image_service,
        storage=storage,
    )
    return image_service


async def create_resources(app: FastAPI):
    """Services initialization."""
    redis = init_redis(
        url=config.redis_url,
        db=config.redis.db,
        password=config.secrets.redis_password.get_secret_value(),
        decode_responses=config.redis.decode_responses,
    )
    pipeline_builder = services.MongoPipelineBuilder()
    init_auth(app, redis, pipeline_builder)

    db_helper = await init_mongo(app)
    image_service = init_plant(app, pipeline_builder)

    services.init_healthz_service(app=app, mongo=db_helper, redis=redis)

    return redis, db_helper, image_service


async def close_resources(
    redis: Redis | None,
    db_helper,
    image_service,
):
    """Services closing."""
    if db_helper:
        await db_helper.close()
    if redis:
        await redis.close()
    if image_service:
        image_service.close()
    logger.info('connections closed')


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(config.logger.exclude, config.logger.level)
    try:
        redis, db_helper, image_service = await create_resources(app)
        yield
    finally:
        await close_resources(redis, db_helper, image_service)
