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

    user_map: dict[PydanticObjectId, UserSchedulerViewScheme] = get_user_map(
        {plant.user_id for plant in plants}
    )
    notifications = []
    pipe = redis.pipeline()

    for plant in plants:
        user = user_map.get(plant.user_id)
        if not user:
            continue

        if user.telegram_notifications_enabled and user.telegram_id:
            notification = Notification(
                user_id=user.id,
                plant_id=plant.id,
                plant_name=plant.name,
                image=plant.image,
                channel=DeliveryChannel.telegram,
                destination=user.telegram_id,
                scheduled_for=scheduled_for,
                status=NotificationStatus.queued,
            )
            notifications.append(notification)
            pipe.xadd(
                tg_queue_key,
                notification.to_queue_dict(),
            )

        if user.email_notifications_enabled and user.email:
            notifications.append(
                Notification(
                    user_id=user.id,
                    plant_id=plant.id,
                    plant_name=plant.name,
                    image=plant.image,
                    channel=DeliveryChannel.email,
                    destination=user.email,
                    scheduled_for=scheduled_for,
                    status=NotificationStatus.queued,
                )
            )
        notifications.append(
            Notification(
                user_id=user.id,
                plant_id=plant.id,
                plant_name=plant.name,
                image=plant.image,
                channel=DeliveryChannel.web,
                destination=None,
                scheduled_for=scheduled_for,
                status=NotificationStatus.sent,
            )
        )

    if notifications:
        await Notification.insert_many(notifications, ordered=False)
        await pipe.execute()

    return notifications


async def get_user_map(
    user_ids: set[PydanticObjectId],
) -> dict[PydanticObjectId, UserSchedulerViewScheme]:
    users = await User.find(
        User.id.in_(user_ids), projection_model=UserSchedulerViewScheme
    ).to_list()
    return {user.id: user for user in users}
