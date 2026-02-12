from beanie import PydanticObjectId
from pydantic import EmailStr
from pymongo import ASCENDING, IndexModel

from app.constants.email import EMAIL_CONFIRMATION_DB_TTL
from app.models.base import BaseDocument


class EmailConfirmation(BaseDocument):
    user_id: PydanticObjectId
    email: EmailStr

    token: str

    is_used: bool = False

    ip: str | None = None
    user_agent: str | None = None
    confirmed_ip: str | None = None
    confirmed_user_agent: str | None = None

    class Settings(BaseDocument.Settings):
        name = 'email_confirmations'
        indexes = [
            IndexModel(
                [('created_at', ASCENDING)],
                expireAfterSeconds=EMAIL_CONFIRMATION_DB_TTL,
                name='ttl_created_at',
            ),
            IndexModel([('token', ASCENDING)], unique=True, name='uniq_token'),
            IndexModel(
                [('user_id', ASCENDING), ('token', ASCENDING)],
                name='user_token_idx',
            ),
            IndexModel([('user_id', ASCENDING)], name='user_idx'),
        ]
