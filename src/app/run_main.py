from logging import Formatter

import filelock
from fastapi import FastAPI
from gunicorn.app.base import BaseApplication  # type: ignore
from gunicorn.arbiter import Arbiter  # type: ignore
from gunicorn.glogging import Logger  # type: ignore
from gunicorn.workers.base import Worker  # type: ignore

from app.main import app
from config import SkipEndpointFilter, config

fmt = Formatter(fmt=config.logger.format, datefmt=config.logger.date_format)


class GunicornLogger(Logger):
    """Gunicorn logger."""

    def setup(self, cfg) -> None:
        """Gunicorn logger config setup."""
        super().setup(cfg)
        skip_filter = SkipEndpointFilter(endpoints=config.logger.exclude)

        self._set_handler(log=self.access_log, output=cfg.accesslog, fmt=fmt)
        self._set_handler(log=self.error_log, output=cfg.errorlog, fmt=fmt)

        self.access_log.addFilter(skip_filter)
        self.error_log.addFilter(skip_filter)


options = config.service.gunicorn_settings
options['logger_class'] = GunicornLogger
options['log_level'] = config.logger.level


def post_fork(server: Arbiter, worker: Worker):
    """Make unique worker_id for prometheus multiprocess."""
    worker.log.info('[post_fork] age: %s. pid: %s', worker.age, worker.pid)

    worker_id = None
    for idx in range(server.cfg.workers):
        wid = idx + 1
        lock_file = f'worker_id_{wid}.lock'
        try:
            lock = filelock.FileLock(lock_file).acquire(timeout=0)
        except filelock.Timeout:
            continue
        else:
            worker_id = wid
            setattr(worker, 'worker_id', worker_id)
            setattr(worker, 'worker_id_lock', lock)
            break

    if not worker_id:
        worker.log.error(
            '[post_fork] No available worker_id for worker pid %s', worker.pid
        )
        return

    worker.log.info('[post_fork] worker_id assigned: %s', worker_id)


class Application(BaseApplication):
    """Gunicorn app setup."""

    def __init__(
        self,
        application: FastAPI,
        options: dict | None = None,
    ):
        """Gunicorn app initialization."""
        self.options = options or {}
        self.application = application
        super().__init__()

    def load(self):
        """Load fastapi app."""
        return self.application

    @property
    def config_options(self) -> dict:
        """Config options loader."""
        return {
            key: option
            for key, option in self.options.items()
            if key in self.cfg.settings and option is not None
        }

    def load_config(self):
        """Config loader."""
        for key, option in self.config_options.items():
            self.cfg.set(key.lower(), option)


def main():
    """Gunicorn start with python."""

    options['post_fork'] = post_fork
    Application(application=app, options=options).run()


if __name__ == '__main__':
    main()
