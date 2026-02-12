from types import MappingProxyType
from typing import Any, Type

from fastapi import status

from app.constants import MSG, STATUS, TYPE


class InvalidPlantDataError(Exception):
    """Plant data main exception."""


class PeriodCrossingError(InvalidPlantDataError):
    """Crossed periods provided."""


class NoWateringPeriodError(InvalidPlantDataError):
    """No watering period."""


class NoDaysSchedulerError(InvalidPlantDataError):
    """No days provided for scheduler."""


class PlantNotFoundError(InvalidPlantDataError):
    """Plant not found."""


class OnePeriodMissingError(InvalidPlantDataError):
    """One of the watering periods is missing."""


PLANT_ERROR_MAP: MappingProxyType[
    Type[InvalidPlantDataError], dict[str, Any]
] = MappingProxyType(
    {
        PeriodCrossingError: {
            MSG: 'plant.period_crossing',
            TYPE: 'period_crossing',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
        NoWateringPeriodError: {
            MSG: 'plant.no_watering_period',
            TYPE: 'no_watering_period',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
        NoDaysSchedulerError: {
            MSG: 'plant.no_days_scheduler',
            TYPE: 'no_days_scheduler',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
        PlantNotFoundError: {
            MSG: 'plant.not_found',
            TYPE: 'plant_not_found',
            STATUS: status.HTTP_404_NOT_FOUND,
        },
        OnePeriodMissingError: {
            MSG: 'plant.one_period_missing',
            TYPE: 'one_period_missing',
            STATUS: status.HTTP_400_BAD_REQUEST,
        },
    }
)
