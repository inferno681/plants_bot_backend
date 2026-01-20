from datetime import date, timedelta
from logging import getLogger

from beanie import PydanticObjectId

from app.logs.plant import PLANT_SERVICE_START_LOG
from app.models import Plant
from app.schemes import PlantCreteScheme, PlantDashboardStats, PlantTask
from app.services.scheduler import scheduler
from app.utils.filters import PlantFilter
from app.utils.ordering import OrderDirection, OrderItem, OrderParams
from app.utils.pagination import CursorPaginatorParams


class PlantService:
    """Plant service."""

    def __init__(self):
        self.log = getLogger(__name__)
        self.log.info(PLANT_SERVICE_START_LOG)

    async def add_plant(self, user_id: str, plant_data: PlantCreteScheme):
        """Add plant."""

        plant = Plant(
            user_id=PydanticObjectId(user_id), **plant_data.model_dump()
        )
        if plant.warm_period and plant.cold_period:
            plant = scheduler.next_watering_date(
                plant, plant.last_watered_at if plant.last_watered_at else None
            )
        if plant.fertilizing:
            plant = scheduler.next_fertilizing_date(
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

            cursor_filter = Plant._build_cursor_filter(
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

    async def get_plant_by_id(
        self, plant_id: str, user_id: str
    ) -> 'Plant | None':
        return await Plant.find_one(
            Plant.id == PydanticObjectId(plant_id),
            Plant.user_id == PydanticObjectId(user_id),
        )

    async def get_stats(self, user_id: str) -> dict:
        """Aggregate basic dashboard stats."""
        today = date.today()
        week_limit = today + timedelta(days=7)
        pipeline = [
            {'$match': {'user_id': PydanticObjectId(user_id)}},
            {
                '$facet': {
                    'total': [{'$count': 'value'}],
                    'attention': [
                        {
                            '$match': {
                                '$or': [
                                    {'next_watering_at': {'$lte': today}},
                                    {'next_fertilizing_at': {'$lte': today}},
                                ]
                            }
                        },
                        {'$count': 'value'},
                    ],
                    'watering_week': [
                        {
                            '$match': {
                                'next_watering_at': {
                                    '$gte': today,
                                    '$lte': week_limit,
                                }
                            }
                        },
                        {'$count': 'value'},
                    ],
                    'tasks': [
                        {'$match': {'next_watering_at': {'$ne': None}}},
                        {'$sort': {'next_watering_at': 1}},
                        {'$limit': 10},
                        {
                            '$project': {
                                'plant_id': '$_id',
                                'name': 1,
                                'date': '$next_watering_at',
                                'type': {
                                    '$cond': [
                                        {
                                            '$eq': [
                                                '$next_watering_at',
                                                '$next_fertilizing_at',
                                            ]
                                        },
                                        'watering_with_fertilizing',
                                        'watering',
                                    ]
                                },
                            }
                        },
                    ],
                }
            },
        ]

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
            if order_item.direction == OrderDirection.DESC
            else field_expr > pivot_value
        )

        if index == len(order_items) - 1:
            return comparator

        equals = field_expr == pivot_value
        return comparator | (
            equals & self._build_cursor_filter(pivot, order_items, index + 1)
        )


plant_service = PlantService()
