class InvalidPlantDataError(Exception):
    """Plant data main exception."""


class PeriodCrossingError(InvalidPlantDataError):
    """Crossed periods provided."""


class NoWateringPeriodError(InvalidPlantDataError):
    """No watering period."""


class NoDaysSchedulerError(InvalidPlantDataError):
    """No days provided for scheduler."""
