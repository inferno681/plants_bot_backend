from datetime import datetime, timezone
from typing_extensions import Annotated
from taskiq import TaskiqDepends
from redis.asyncio import Redis

from app.models import (
    DeliveryChannel,
    Notification,
    NotificationStatus,
    Plant,
    User,
)
from app.tasks.dependency import redis_dep
from app.tasks.broker import broker


async def get_plants_watering(
    hour: int,
    redis: Annotated[Redis, TaskiqDepends(redis_dep)],
    tg_queue_key: str = 'tg_notifications',
):
    now = datetime.now(timezone.utc)
    scheduled_for = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    plants = await Plant.find(Plant.next_watering_at <= now).to_list()
    user_ids = {plant.user_id for plant in plants}

    users = await User.find(User.id.in_(user_ids)).to_list()

    user_map = {user.id: user for user in users}
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
                {
                    'key': notification.dedup_key,
                    'user_id': str(notification.user_id),
                    'plant_id': str(notification.plant_id),
                    'name': notification.plant_name,
                    'image': notification.image or '',
                    'destination': notification.destination,
                },
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
        if user.web_notifications_enabled:
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
        await Notification.insert_many(notifications)
        await pipe.execute()

    return notifications
