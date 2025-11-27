from logging import Filter, LogRecord
from logging.config import dictConfig
from sys import stdout

from config.config import config


class SkipEndpointFilter(Filter):
    """Logger filter."""

    def __init__(self, name: str = '', endpoints: list[str] | None = None):
        """Filter initialization."""
        super().__init__(name)
        self.endpoints = endpoints or []

    def filter(self, record: LogRecord) -> bool:
        """Apply logger filter."""
        msg = record.getMessage()
        return not any(ep in msg for ep in self.endpoints)


def setup_logging(
    skip_endpoints: list[str] | None = None, level: str = 'INFO'
):
    """Logger settings setup."""
    dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': config.logger.format,
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                },
            },
            'filters': {
                'skip_endpoints': {
                    '()': SkipEndpointFilter,
                    'endpoints': skip_endpoints or [],
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'filters': ['skip_endpoints'],
                    'stream': stdout,
                },
            },
            'root': {
                'level': level,
                'handlers': ['console'],
            },
            'loggers': {
                'uvicorn': {
                    'level': level,
                    'handlers': ['console'],
                    'propagate': False,
                },
                'uvicorn.error': {
                    'level': level,
                    'handlers': ['console'],
                    'propagate': False,
                },
                'uvicorn.access': {
                    'level': level,
                    'handlers': ['console'],
                    'propagate': False,
                },
                'app': {
                    'level': level,
                    'handlers': ['console'],
                    'propagate': False,
                },
            },
        }
    )


setup_logging(config.logger.exclude, config.logger.level)
