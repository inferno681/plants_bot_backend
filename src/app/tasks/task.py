from datetime import datetime, timezone

from beanie import PydanticObjectId
from redis.asyncio import Redis
from taskiq import TaskiqDepends
from typing_extensions import Annotated

from app.constants.task import WATERING_BATCH_SIZE, WATERING_SCHEDULE_HOUR
from app.models import (
    DeliveryChannel,
    Notification,
    NotificationStatus,
    Plant,
    User,
)
from app.schemes import PlantSchedulerViewScheme, UserSchedulerViewScheme
from app.tasks.broker import broker
from app.tasks.dependency import redis_dep


@broker.task(schedule=[{'cron': '0 10 * * *'}])
async def get_plants_watering(
    batch_size: int = WATERING_BATCH_SIZE,
):
    now = datetime.now(timezone.utc)
    scheduled_for = now.replace(
        hour=WATERING_SCHEDULE_HOUR, minute=0, second=0, microsecond=0
    )

    cursor: PydanticObjectId | None = None
    while True:
        query = [Plant.next_watering_at <= now]
        if cursor is not None:
            query.append(Plant.id > cursor)

        plants = (
            await Plant.find(*query, projection_model=PlantSchedulerViewScheme)
            .sort([('_id', 1)])
            .limit(batch_size)
            .to_list()
        )
        if not plants:
            break

        await process_watering_batch.kiq(
            plants=plants,
            scheduled_for=scheduled_for,
        )
        cursor = plants[-1].id

    return True


@broker.task
async def process_watering_batch(
    plants: list[PlantSchedulerViewScheme],
    scheduled_for: datetime,
    redis: Annotated[Redis, TaskiqDepends(redis_dep)],
    tg_queue_key: str = 'tg_notifications',
):
    pipe = redis.pipeline()
    user_map = await get_user_map({plant.user_id for plant in plants})
    notifications = _collect_notifications(
        plants=plants,
        scheduled_for=scheduled_for,
        user_map=user_map,
        pipe=pipe,
        tg_queue_key=tg_queue_key,
    )

    if notifications:
        await Notification.insert_many(notifications, ordered=False)
        await pipe.execute()

    return notifications


def _collect_notifications(
    *,
    plants: list[PlantSchedulerViewScheme],
    scheduled_for: datetime,
    user_map: dict[PydanticObjectId, UserSchedulerViewScheme],
    pipe,
    tg_queue_key: str,
) -> list[Notification]:
    notifications: list[Notification] = []

    for plant in plants:
        user = user_map.get(plant.user_id)
        if not user:
            continue

        telegram_notification = _build_telegram_notification(
            user=user,
            plant=plant,
            scheduled_for=scheduled_for,
        )
        if telegram_notification:
            notifications.append(telegram_notification)
            pipe.xadd(tg_queue_key, telegram_notification.to_queue_dict())

        email_notification = _build_email_notification(
            user=user,
            plant=plant,
            scheduled_for=scheduled_for,
        )
        if email_notification:
            notifications.append(email_notification)

        notifications.append(
            _build_web_notification(
                user=user,
                plant=plant,
                scheduled_for=scheduled_for,
            )
        )

    return notifications


def _build_telegram_notification(
    *,
    user: UserSchedulerViewScheme,
    plant: PlantSchedulerViewScheme,
    scheduled_for: datetime,
) -> Notification | None:
    if not (user.telegram_notifications_enabled and user.telegram_id):
        return None

    return Notification(
        user_id=user.id,
        plant_id=plant.id,
        plant_name=plant.name,
        image=plant.image,
        channel=DeliveryChannel.telegram,
        destination=user.telegram_id,
        scheduled_for=scheduled_for,
        status=NotificationStatus.queued,
    )


def _build_email_notification(
    *,
    user: UserSchedulerViewScheme,
    plant: PlantSchedulerViewScheme,
    scheduled_for: datetime,
) -> Notification | None:
    if not (user.email_notifications_enabled and user.email):
        return None

    return Notification(
        user_id=user.id,
        plant_id=plant.id,
        plant_name=plant.name,
        image=plant.image,
        channel=DeliveryChannel.email,
        destination=user.email,
        scheduled_for=scheduled_for,
        status=NotificationStatus.queued,
    )


def _build_web_notification(
    *,
    user: UserSchedulerViewScheme,
    plant: PlantSchedulerViewScheme,
    scheduled_for: datetime,
) -> Notification:
    return Notification(
        user_id=user.id,
        plant_id=plant.id,
        plant_name=plant.name,
        image=plant.image,
        channel=DeliveryChannel.web,
        destination=None,
        scheduled_for=scheduled_for,
        status=NotificationStatus.sent,
    )


async def get_user_map(
    user_ids: set[PydanticObjectId],
) -> dict[PydanticObjectId, UserSchedulerViewScheme]:
    users = await User.find(
        User.id.in_(user_ids), projection_model=UserSchedulerViewScheme
    ).to_list()
    return {user.id: user for user in users}
