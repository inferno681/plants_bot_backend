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
    max_sessions_per_user: int

    service_chat_id: int

    debug: bool
    access_token_ttl: int
    refresh_token_ttl: int

    init_data_max_age: int
    bot_init_data_max_age: int

    tag_metadata_auth_web: dict[str, str]
    tag_metadata_auth_telegram: dict[str, str]
    tag_metadata_auth_bot: dict[str, str]
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
    max_retries: int
    backoff_base: float
    backoff_jitter: float


class RedisSettings(BaseModel):
    """Redis settings."""

    host: str
    port: int
    db: int
    decode_responses: bool


class CORS(BaseModel):
    """CORS settings."""

    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]


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
    refresh_token_secret: SecretStr = Field(
        default=SecretStr('secret'), alias='REFRESH_TOKEN_SECRET'
    )
    access_token_secret: SecretStr = Field(
        default=SecretStr('secret'), alias='ACCESS_TOKEN_SECRET'
    )
    aws_access_key: SecretStr = Field(
        default=SecretStr('minioadmin'), alias='AWS_ACCESS_KEY'
    )
    aws_secret_key: SecretStr = Field(
        default=SecretStr('minioadmin'), alias='AWS_SECRET_KEY'
    )
    redis_password: SecretStr = Field(
        default=SecretStr('secret_password'), alias='REDIS_PASSWORD'
    )

    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )


class StorageS3(BaseModel):
    """S3 settings."""

    bucket: str
    endpoint_url: str


class AppConfig(BaseSettings):
    """Main configuration class."""

    service: ServiceSettings
    mongodb: MongoSettings
    redis: RedisSettings
    storage: StorageS3
    secrets: Secrets
    cors: CORS

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
    def mongo_url(self) -> str:
        return 'mongodb+srv://{user}:{pwd}@{host}/'.format(
            user=self.secrets.mongo_user.get_secret_value(),
            pwd=self.secrets.mongo_password.get_secret_value(),
            host=self.mongodb.host,
        )

    @property
    def mongo_url_dev(self) -> str:
        return 'mongodb://{user}:{pwd}@{host}:{port}/'.format(
            user=self.secrets.mongo_user.get_secret_value(),
            pwd=self.secrets.mongo_password.get_secret_value(),
            host=self.mongodb.host,
            port=self.mongodb.port,
        )

    @property
    def redis_url(self) -> str:
        return 'redis://:{pwd}@{host}:{port}/{db}'.format(
            pwd=self.secrets.redis_password.get_secret_value(),
            host=self.redis.host,
            port=self.redis.port,
            db=self.redis.db,
        )

    @property
    def send_photo_link(self) -> str:
        return 'https://api.telegram.org/bot{token}/sendPhoto'.format(
            token=self.secrets.bot_token.get_secret_value()
        )


config = AppConfig.load_settings('src/config/config.yaml')
