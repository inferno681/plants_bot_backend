from enum import StrEnum
from typing import Any, Iterable, Tuple

from beanie import SortDirection
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator


class OrderField(StrEnum):
    ID = '_id'
    NAME = 'name'
    NEXT_WATERING_AT = 'next_watering_at'
    NEXT_FERTILIZING_AT = 'next_fertilizing_at'
    CREATED_AT = 'created_at'


class OrderItem(BaseModel):
    """Single ordering rule."""

    field: OrderField
    direction: SortDirection = SortDirection.ASCENDING

    @property
    def sort_string(self) -> str:
        sign = (
            '+'
            if self.direction == SortDirection.ASCENDING
            else '-'
        )
        return f'{sign}{self.field.value}'

    @property
    def sort_tuple(self) -> Tuple[str, SortDirection]:
        return self.field.value, self.direction


class OrderParams(BaseModel):
    """Ordering params separated from pagination, supports multiple fields."""

    order: list[OrderItem] = Field(
        default_factory=lambda: [OrderItem(field=OrderField.ID)]
    )

    @field_validator('order', mode='before')
    @classmethod
    def parse_order(cls, value: Any) -> list['OrderItem']:
        if value is None:
            return [OrderItem(field=OrderField.ID)]

        items: list[OrderItem] = []

        if isinstance(value, str):
            value = value.split(',')

        if isinstance(value, Iterable):
            for raw in value:
                if isinstance(raw, OrderItem):
                    items.append(raw)
                    continue
                if not isinstance(raw, str):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='order must be a string or list of strings',
                    )
                token = raw.strip()
                if not token:
                    continue
                direction = SortDirection.ASCENDING
                if token[0] in '+-':
                    direction = (
                        SortDirection.ASCENDING
                        if token[0] == '+'
                        else SortDirection.DESCENDING
                    )
                    token = token[1:]
                try:
                    field = OrderField(token)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f'Unsupported order field "{token}"',
                    )
                items.append(OrderItem(field=field, direction=direction))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='order must be a string or list of strings',
            )

        if not items:
            items.append(OrderItem(field=OrderField.ID))

        return items

    def with_tie_breaker(self) -> list[OrderItem]:
        """Ensure stable ordering by appending _id if missing."""
        items = list(self.order)
        if not any(item.field == OrderField.ID for item in items):
            primary_direction = (
                items[0].direction if items else SortDirection.ASCENDING
            )
            items.append(
                OrderItem(field=OrderField.ID, direction=primary_direction)
            )
        return items

    @property
    def sort_strings(self) -> list[str]:
        return [item.sort_string for item in self.with_tie_breaker()]

    @property
    def sort_tuples(self) -> list[Tuple[str, SortDirection]]:
        return [item.sort_tuple for item in self.with_tie_breaker()]
