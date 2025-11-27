from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseModel):
    """Service settings."""

    title: str
    description: str
    host: str
    port: int
    timeout: int
    workers: int

    debug: bool
    access_token_ttl: int
    refresh_token_ttl: int
    tag_metadata_auth: dict[str, str]
    tag_metadata_plant: dict[str, str]
    tag_metadata_health: dict[str, str]

    @property
    def tags_metadata(self):
        """Return tags metadata list."""
        return [
            tag_data
            for key, tag_data in self.model_dump().items()
            if key.startswith('tag_metadata_')
        ]

    @property
    def gunicorn_settings(self):
        """Return settings for gunicorn start."""
        return {
            'accesslog': '-',
            'errorlog': '-',
            'bind': f'{self.host}:{self.port}',
            'timeout': self.timeout,
            'workers': self.workers,
            'worker_class': 'uvicorn.workers.UvicornWorker',
        }


class MongoSettings(BaseModel):
    """MongoDB settings."""

    host: str
    port: int
    db: str


class RedisSettings(BaseModel):
    """Redis settings."""

    host: str
    port: int
    db: int
    decode_responses: bool


class Logger(BaseModel):
    """Logger settings."""

    format: str
    exclude: list[str]
    date_format: str
    level: Literal[
        'DEBUG',
        'INFO',
        'WARNING',
        'ERROR',
        'CRITICAL',
    ] = 'INFO'


class Secrets(BaseSettings):
    """Secrets settings."""

    bot_token: SecretStr = Field(default=SecretStr('token'), alias='BOT_TOKEN')

    mongo_user: SecretStr = Field(
        default=SecretStr('user'), alias='MONGO_INITDB_ROOT_USERNAME'
    )
    mongo_password: SecretStr = Field(
        default=SecretStr('password'), alias='MONGO_INITDB_ROOT_PASSWORD'
    )
    reset_token_secret: SecretStr = Field(
        default=SecretStr('secret'), alias='RESET_TOKEN_SECRET'
    )
    verification_token_secret: SecretStr = Field(
        default=SecretStr('secret'), alias='VERIFICATION_TOKEN_SECRET'
    )

    redis_password: SecretStr = Field(
        default=SecretStr('secret_password'), alias='REDIS_PASSWORD'
    )

    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )


class AppConfig(BaseSettings):
    """Main configuration class."""

    service: ServiceSettings
    mongodb: MongoSettings
    redis: RedisSettings
    secrets: Secrets

    logger: Logger

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='allow',
    )

    @classmethod
    def load_settings(cls, file_path: str) -> 'AppConfig':
        """Load configuration from YAML and environment variables."""
        yaml_config = yaml.safe_load(
            Path(file_path).read_text(encoding='utf-8')
        )
        return cls(**yaml_config, secrets=Secrets())

    @property
    def mongo_url(self):
        """Mongo URL."""
        return (
            f'mongodb+srv://{self.secrets.mongo_user.get_secret_value()}:'
            f'{self.secrets.mongo_password.get_secret_value()}@'
            f'{self.mongodb.host}/'
        )

    @property
    def redis_url(self):
        """Redis URL."""
        return (
            f'redis://:{self.secrets.redis_password.get_secret_value()}'
            f'@{self.redis.host}:{self.redis.port}/{self.redis.db}'
        )


config = AppConfig.load_settings('src/config/config.yaml')
