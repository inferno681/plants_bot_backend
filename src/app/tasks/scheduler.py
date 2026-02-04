from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from app.tasks.broker import broker

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


@broker.task(schedule=[{'cron': '*/5 * * * *', 'args': [1]}])
async def heavy_task(value: int) -> int:
    return value + 1
