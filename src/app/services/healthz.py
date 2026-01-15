from logging import getLogger

from redis.asyncio import Redis

from app.constants import OK, STATUS
from app.db import DbHelper, db_helper
from app.logs.healthz import (
    HEALTH_SERVICE_START_LOG,
    MONGO_NOT_READY_LOG,
    REDIS_NOT_READY_LOG,
)
from app.redis_service import redis


class HealthService:
    """Health check service."""

    def __init__(self, mongo: DbHelper, redis: Redis):
        self.mongo = mongo
        self.redis = redis
        self.log = getLogger(__name__)
        self.log.info(HEALTH_SERVICE_START_LOG)

    def health_check(self):
        """Liveness probe."""
        return {STATUS: OK}

    async def ready_check(self) -> dict:
        """Readiness probe."""
        deps = {}
        try:
            await self.mongo.ping()
            deps['mongo'] = OK
        except Exception as exc:
            self.log.warning(MONGO_NOT_READY_LOG, str(exc))
            deps['mongo'] = 'not ready'
        try:
            await self.redis.ping()
            deps['redis'] = OK
        except Exception as exc:
            self.log.warning(REDIS_NOT_READY_LOG, str(exc))
            deps['redis'] = 'not ready'
        return {
            STATUS: (
                'ready'
                if all(field == OK for field in deps.values())
                else 'not-ready'
            ),
            'deps': deps,
        }


health_service = HealthService(mongo=db_helper, redis=redis)
