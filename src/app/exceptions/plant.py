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
