import re
from typing import Literal

from bson import ObjectId

INVALID_TOKEN_MESSAGE = 'Invalid token'
EXPIRED_TOKEN_MESSAGE = 'Token expired'
MISSING_FIELDS_INIT_DATA_MSG = 'Missing fields in init_data'
INVALID_SIGNATURE_MESSAGE = 'Invalid signature'
UNREGISTERED_USER_MESSAGE = 'User is not registered.'
LOGOUT_MESSAGE = 'logout successful'
USER_ALREADY_EXISTS_MESSAGE = 'User with this email already exists.'
LOGOUT_OTHERS_MESSAGE = 'other sessions logged out successfully'
LOGOUT_ALL_MESSAGE = 'all sessions logged out successfully'
INVALID_INIT_DATA_FORMAT_MESSAGE = 'Invalid init_data format'
INVALID_INIT_DATA_USER_DATA_MSG = 'Invalid user JSON in init_data'
INIT_DATA_EXPIRED_MESSAGE = 'init_data expired'
USER_ID_MISSED_INIT_DATA_MSG = 'user.id missing in init_data'
INVALID_AUTH_DATE_MESSAGE = 'Invalid auth_date'
AUTH_DATE_FUTURE_SKEW_SECONDS = 60
REQUIRED_INIT_DATA_FIELDS = ('hash', 'auth_date', 'user')
MISSED_FIELDS_MSG = 'Missing fields: {fields}'
NO_USER_DATA_MSG = 'No user data in init data'
INVALID_DOC_PASSWORD_MESSAGE = 'Invalid documentation password'
MISSING_REFRESH_TOKEN = 'Missing refresh token'
CSRF_VALIDATION_FAILED_MSG = 'CSRF validation failed'
PASSWORD_REGEX = re.compile(
    r'^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$'
)
WEAK_PASSWORD = (
    'Password requirements: min length=8, at least one: '
    'uppercase character, lowercase character, digit and special character.'
)
PASSWORD_CHANGE_SAME_AS_OLD = 'New password must be different'
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
