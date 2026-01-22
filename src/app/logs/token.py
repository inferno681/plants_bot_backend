TOKEN_PROVIDER_START_LOG = 'Token provider started'
SESSION_STORE_START_LOG = 'Session store started'
TOKEN_SERVICE_START_LOG = 'Token service started'
TOKEN_REFRESH_SCRIPT_LOADED_LOG = 'Refresh Lua script loaded: %s'
SESSION_CREATE_SCRIPT_LOADED_LOG = 'Session creation Lua script loaded: %s'
INVALID_ACCESS_TOKEN_LOG = 'Invalid access token: %s'
INVALID_REFRESH_TOKEN_LOG = 'Invalid refresh token: %s'
SESSION_DELETED_LOG = 'Session deleted for user %s'
ALL_SESSION_DELETED_LOG = 'All sessions deleted for user %s'
SESSION_DELETED_OTHERS_LOG = 'All sessions deleted for user %s except current'
REFRESH_REJECTED_LOG = 'Refresh token rejected for user %s due to %s'
TOKEN_REFRESHED_LOG = 'Tokens refreshed for user %s'
REFRESH_REPLAY_DETECTED_LOG = (
    'Refresh replay detected for user %s, IP: %s, ua=%s, user_type=%s'
)
REFRESH_INVALID_OWNER_LOG = (
    'Invalid owner detected during token refresh for '
    'user %s, IP: %s, ua=%s, user_type=%s'
)
REFRESH_UNKNOWN_ERROR_LOG = 'Unknown error during token refresh: %s'
SESSIONS_EVICTED_LOG = (
    'Sessions evicted: '
    'uid=%s,sid=%s, ip=%s, ua=%s, created_at=%s, ttl=%s, user_type=%s'
)

TOKEN_MISSED_UID_TYPE_LOG = (
    'Token missing uid/type in session store for user: %s'
)
TOKEN_OWNER_MISMATCH_LOG = 'Token owner mismatch: expected=%s got=%s'
TOKEN_TYPE_MISMATCH_LOG = 'Token type mismatch: expected=%s got=%s'
