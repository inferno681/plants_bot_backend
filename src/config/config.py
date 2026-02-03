from pathlib import Path
from typing import Literal

import yaml
from dns.resolver import NXDOMAIN, NoAnswer, Timeout, resolve
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

    link_ttl: int

    service_chat_id: int

    debug: bool

    is_prod: bool

    tag_metadata_auth_web: dict[str, str]
    tag_metadata_auth_telegram: dict[str, str]
    tag_metadata_auth_bot: dict[str, str]
    tag_metadata_bot: dict[str, str]
    tag_metadata_user: dict[str, str]
    tag_metadata_link: dict[str, str]
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


class AuthSettings(BaseModel):
    """Auth settings."""

    max_sessions_per_user: int

    access_token_ttl: int
    refresh_token_ttl: int

    user_init_data_ttl: int
    bot_init_data_ttl: int
    init_data_skew: int


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
    decode_responses: bool

    sid_db: int
    queue_db: int
    taskiq_db: int
    results_db: int


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


class ImageSettings(BaseSettings):
    """Uploading image settings."""

    allowed_mime: set[str]
    allowed_ext: set[str]
    max_size_bytes: int

    out_width: int
    out_height: int
    jpeg_quality: int
    webp_quality: int

    max_input_width: int
    max_input_height: int
    max_input_pixels: int

    backend: Literal['pillow', 'vips']

    max_workers: int


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
    doc_password: SecretStr = Field(
        default=SecretStr('secret_password'), alias='DOC_PASSWORD'
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
    image: ImageSettings
    auth: AuthSettings

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
        is_srv = self.is_srv_mongo(self.mongodb.host)
        return '{scheme}://{user}:{pwd}@{host}{port}/'.format(
            scheme='mongodb+srv' if is_srv else 'mongodb',
            user=self.secrets.mongo_user.get_secret_value(),
            pwd=self.secrets.mongo_password.get_secret_value(),
            host=self.mongodb.host,
            port='' if is_srv else f':{self.mongodb.port}',
        )

    def redis_url(self, db: int) -> str:
        return 'redis://:{pwd}@{host}:{port}/{db}'.format(
            pwd=self.secrets.redis_password.get_secret_value(),
            host=self.redis.host,
            port=self.redis.port,
            db=db,
        )

    @property
    def send_photo_link(self) -> str:
        return 'https://api.telegram.org/bot{token}/sendPhoto'.format(
            token=self.secrets.bot_token.get_secret_value()
        )

    @staticmethod
    def is_srv_mongo(host: str) -> bool:
        try:
            resolve(f'_mongodb._tcp.{host}', 'SRV')
            return True
        except (NoAnswer, NXDOMAIN, Timeout):
            return False


config = AppConfig.load_settings('src/config/config.yaml')
