import re
from enum import StrEnum
from typing import Literal

from bson import ObjectId


class AuthMessage(StrEnum):
    invalid_token = 'Invalid token'
    expired_token = 'Token expired'
    invalid_signature = 'Invalid signature'

    unregistered_user = 'User is not registered.'
    user_already_exist = 'User with this email already exists.'

    logout = 'logout successful'
    logout_others = 'other sessions logged out successfully'
    logout_all = 'all sessions logged out successfully'

    init_data_invalid_format = 'Invalid init_data format'
    init_data_invalid_user_data = 'Invalid user JSON in init_data'
    init_data_expired = 'init_data expired'
    init_data_user_id_missed = 'user.id missing in init_data'
    init_data_invalid_auth_date = 'Invalid auth_date'
    init_data_no_user_data = 'No user data in init data'
    init_data_missed_fields = 'Missing fields in init_data'

    missed_fields = 'Missing fields: {fields}'

    invalid_doc_password = 'Invalid documentation password'

    missed_refresh_token = 'Missing refresh token'
    csrf_validation_failed = 'CSRF validation failed'
    weak_password = (
        'Password requirements: min length=8, at least one: '
        'uppercase character, lowercase character, digit and '
        'special character.'
    )
    same_password_as_old = 'New password must be different'


AUTH_DATE_FUTURE_SKEW_SECONDS = 60
REQUIRED_INIT_DATA_FIELDS = frozenset(('hash', 'auth_date', 'user'))


PASSWORD_REGEX = re.compile(
    r'^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$'
)


SESSION_PREFIX = 'session:'
USER_SESSIONS_PREFIX = 'user_sessions:'
UNKNOWN_LITERAL = 'unknown'


DOC_USER = ObjectId('697a9f7f7cae65704fd51a12')

REQUIRED_FIELDS_BOT_INIT_DATA = ('bot_id', 'auth_date', 'hash')

CSRF_LENGTH = 32

SameSite = Literal['lax', 'strict', 'none']
LAX_LITERAL: SameSite = 'lax'

SUB = 'sub'
EXP = 'exp'
SID = 'sid'
IAT = 'iat'
TYPE = 'type'
USER = 'user'
