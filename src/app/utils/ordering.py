from enum import StrEnum
from typing import Any, Iterable, Tuple

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator


class OrderDirection(StrEnum):
    ASC = 'asc'
    DESC = 'desc'

    @property
    def sign(self) -> str:
        return '+' if self == OrderDirection.ASC else '-'

    @property
    def sort_direction(self) -> int:
        return 1 if self == OrderDirection.ASC else -1


class OrderField(StrEnum):
    ID = '_id'
    NAME = 'name'
    NEXT_WATERING_AT = 'next_watering_at'
    NEXT_FERTILIZING_AT = 'next_fertilizing_at'
    CREATED_AT = 'created_at'


class OrderItem(BaseModel):
    """Single ordering rule."""

    field: OrderField
    direction: OrderDirection = OrderDirection.ASC

    @property
    def sort_string(self) -> str:
        return f'{self.direction.sign}{self.field.value}'

    @property
    def sort_tuple(self) -> Tuple[str, int]:
        return self.field.value, self.direction.sort_direction


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
                direction = OrderDirection.ASC
                if token[0] in '+-':
                    direction = (
                        OrderDirection.ASC
                        if token[0] == '+'
                        else OrderDirection.DESC
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
                items[0].direction if items else OrderDirection.ASC
            )
            items.append(
                OrderItem(field=OrderField.ID, direction=primary_direction)
            )
        return items

    @property
    def sort_strings(self) -> list[str]:
        return [item.sort_string for item in self.with_tie_breaker()]

    @property
    def sort_tuples(self) -> list[Tuple[str, int]]:
        return [item.sort_tuple for item in self.with_tie_breaker()]
