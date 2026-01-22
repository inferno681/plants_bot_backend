from typing import Annotated

from fastapi import Depends, Query

from app.schemes import PlantQuery
from app.services import get_plant_mapper, get_plant_service
from app.utils import CursorPaginatorParams, OrderParams, PlantFilter


def ordering_params(
    order: Annotated[list[str] | None, Query(alias='order')] = None,
) -> OrderParams:
    return OrderParams.model_validate({'order': order})


async def plant_query_dependency(
    filters: Annotated[PlantFilter, Depends()],
    paginator: Annotated[CursorPaginatorParams, Depends()],
    ordering: Annotated[OrderParams, Depends(ordering_params)],
) -> PlantQuery:
    return PlantQuery(filters=filters, paginator=paginator, ordering=ordering)


plant_mapper_dep = Depends(get_plant_mapper)
plant_service_dep = Depends(get_plant_service)
plant_query_dep = Depends(plant_query_dependency)
