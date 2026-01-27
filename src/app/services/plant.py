from datetime import date, datetime, time, timezone
from logging import getLogger
from uuid import uuid4

from beanie import PydanticObjectId, SortDirection
from beanie.operators import Set
from fastapi import FastAPI, Request
from pymongo.asynchronous.client_session import AsyncClientSession

from app.exceptions.plant import PlantNotFoundError
from app.logs.plant import (
    NO_PLANTS_FOR_MIGRATION_LOG,
    PLANT_SERVICE_START_LOG,
    PLANTS_MIGRATION_SUCCESS_LOG,
)
from app.models import Plant
from app.schemes import (
    ImageUpload,
    PlantCreteScheme,
    PlantDashboardStats,
    PlantTask,
    PlantUpdateScheme,
)
from app.services.image import ImageService
from app.services.pipeline import MongoPipelineBuilder
from app.services.scheduler import Scheduler
from app.services.storage import S3StorageService
from app.utils import (
    CursorPaginatorParams,
    OrderItem,
    OrderParams,
    PlantFilter,
    send_photo_to_telegram,
)


class PlantService:
    """Plant service."""

    def __init__(
        self,
        scheduler: Scheduler,
        pipeline_builder: MongoPipelineBuilder,
        image_service: ImageService,
        storage: S3StorageService,
    ):
        """Service constructor."""
        self.scheduler = scheduler
        self.pipeline_builder = pipeline_builder
        self.image_service = image_service
        self.storage = storage
        self.log = getLogger(__name__)
        self.log.info(PLANT_SERVICE_START_LOG)

    async def add_plant(self, user_id: str, plant_data: PlantCreteScheme):
        """Add plant."""

        plant = Plant(
            user_id=PydanticObjectId(user_id), **plant_data.model_dump()
        )
        if plant.warm_period and plant.cold_period:
            plant = self.scheduler.next_watering_date(
                plant, plant.last_watered_at if plant.last_watered_at else None
            )
        if plant.fertilizing:
            plant = self.scheduler.next_fertilizing_date(
                plant,
                plant.last_fertilized_at if plant.last_fertilized_at else None,
            )
        await plant.insert()
        return plant

    async def get_plants(
        self,
        user_id: str,
        filters: PlantFilter,
        paginator: CursorPaginatorParams,
        ordering: OrderParams,
    ) -> tuple[list[Plant], bool]:

        query = [Plant.user_id == PydanticObjectId(user_id)]

        query.extend(filters.apply(Plant))

        if paginator.cursor:
            pivot = await Plant.find_one(
                Plant.id == PydanticObjectId(paginator.cursor)
            )
            if pivot is None:
                return [], False

            cursor_filter = self._build_cursor_filter(
                pivot=pivot,
                order_items=ordering.with_tie_breaker(),
            )

            query.append(cursor_filter)

        plants = (
            await Plant.find(*query)
            .sort(ordering.sort_tuples)
            .limit(paginator.limit + 1)
            .to_list()
        )

        has_more = len(plants) > paginator.limit
        if has_more:
            plants = plants[: paginator.limit]

        return plants, has_more

    async def get_plant_by_id(self, plant_id: str, user_id: str) -> Plant:
        plant = await Plant.find_one(
            Plant.id == PydanticObjectId(plant_id),
            Plant.user_id == PydanticObjectId(user_id),
        )
        if not plant:
            raise PlantNotFoundError()
        return plant

    async def get_stats(self, user_id: str) -> PlantDashboardStats:
        """Aggregate basic dashboard stats."""
        today = date.today()
        pipeline = self.pipeline_builder.build_dashboard_pipeline(
            user_id, datetime.combine(today, time.min)
        )

        agg_result = await Plant.aggregate(pipeline).to_list()

        if not agg_result:
            return PlantDashboardStats(
                total=0, attention=0, watering_week=0, tasks=[]
            )

        dashboard_data = agg_result[0]

        return PlantDashboardStats(
            total=(
                dashboard_data['total'][0]['value']
                if dashboard_data['total']
                else 0
            ),
            attention=(
                dashboard_data['attention'][0]['value']
                if dashboard_data['attention']
                else 0
            ),
            watering_week=(
                dashboard_data['watering_week'][0]['value']
                if dashboard_data['watering_week']
                else 0
            ),
            tasks=[PlantTask(**task) for task in dashboard_data['tasks']],
        )

    async def update_plant_image(
        self,
        plant_id: str,
        user_id: str,
        file_info: ImageUpload,
    ) -> Plant:
        plant = await self.get_plant_by_id(plant_id, user_id)
        file_id, storage_key = await self._process_image(
            user_id, file_info, plant
        )
        plant.storage_key = storage_key
        plant.image = file_id
        await plant.save()
        return plant

    async def update_plant(
        self,
        plant_id: str,
        user_id: str,
        plant_update: PlantUpdateScheme,
    ) -> Plant:
        plant = await self.get_plant_by_id(plant_id, user_id)

        if plant_update is None:
            return plant

        for key, new_value in plant_update.model_dump(
            exclude_unset=True
        ).items():
            setattr(plant, key, new_value)
        await plant.save()
        return plant

    async def plant_migration(
        self,
        old_user: PydanticObjectId,
        new_user: PydanticObjectId,
        session: AsyncClientSession,
    ):
        """Plant migration between users."""
        if old_user == new_user:
            return
        migration = await Plant.find(
            Plant.user_id == old_user, session=session
        ).update(
            Set(
                {
                    Plant.user_id: new_user,
                    Plant.updated_at: datetime.now(timezone.utc),
                }
            )
        )
        if migration.modified_count > 0:
            self.log.info(
                PLANTS_MIGRATION_SUCCESS_LOG,
                migration.modified_count,
                str(old_user),
                str(new_user),
            )
        else:
            self.log.info(
                NO_PLANTS_FOR_MIGRATION_LOG,
                str(old_user),
                str(new_user),
            )

    def _build_cursor_filter(
        self,
        pivot: Plant,
        order_items: list[OrderItem],
        index: int = 0,
    ):
        """Build cursor-based filter for multi-field ordering."""
        order_item = order_items[index]

        field_expr = getattr(Plant, order_item.field.value)
        pivot_value = getattr(pivot, order_item.field.value)

        comparator = (
            field_expr < pivot_value
            if order_item.direction == SortDirection.DESCENDING
            else field_expr > pivot_value
        )

        if index == len(order_items) - 1:
            return comparator

        equals = field_expr == pivot_value
        return comparator | (
            equals & self._build_cursor_filter(pivot, order_items, index + 1)
        )

    async def _process_image(
        self, user_id: str, file_info: ImageUpload, plant: Plant
    ) -> tuple[str, str]:
        """Image processing."""
        file_id = await send_photo_to_telegram(file_info)
        new_file, ext = await self.image_service.process(file_info)
        storage_key = f'{user_id}/{uuid4()}{ext}'
        if plant.storage_key:
            await self.storage.delete_file(plant.storage_key)
        await self.storage.upload_file(storage_key, new_file)
        return file_id, storage_key


def init_plant_service(
    app: FastAPI,
    scheduler: Scheduler,
    pipeline_builder: MongoPipelineBuilder,
    image_service: ImageService,
    storage: S3StorageService,
) -> None:
    """Create PlantService once and store on app.state."""
    app.state.plant_service = PlantService(
        scheduler=scheduler,
        pipeline_builder=pipeline_builder,
        image_service=image_service,
        storage=storage,
    )


def get_plant_service(request: Request) -> PlantService:
    """FastAPI dependency for PlantService."""
    return request.app.state.plant_service
