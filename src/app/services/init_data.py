import hashlib
import hmac
import json
import time
import urllib
from enum import StrEnum, auto
from logging import getLogger

from app.constants import REQUIRED_INIT_DATA_FIELDS, AuthMessage
from app.exceptions.auth import InvalidInitDataError, InvalidSignatureError
from app.logs.auth import (
    INVALID_INIT_DATA_FORMAT_LOG,
    INVALID_INIT_DATA_LOG,
    INVALID_INIT_DATA_SIGN_LOG,
)


class ClientType(StrEnum):
    """Client type."""

    user = auto()
    bot = auto()


class InitDataChecker:
    """Init data checker."""

    def __init__(
        self,
        secret: str,
        user_init_data_ttl: int,
        bot_init_data_ttl: int,
        skew: int,
    ):
        """Initialize InitDataChecker."""
        self.secret = secret
        self.user_init_data_ttl = user_init_data_ttl
        self.bot_init_data_ttl = bot_init_data_ttl
        self.skew = skew
        self.log = getLogger(__name__)

    def verify_init_data(
        self, init_data: str, client_type: ClientType = ClientType.user
    ) -> dict:
        """Verify init data."""
        parsed = self._parse_init_data(init_data, client_type)
        user_data = self._check_init_data(parsed, client_type)

        calculated_hash = hmac.new(
            hmac.new(
                key=(
                    b'WebAppData'
                    if client_type == ClientType.user
                    else b'PlantsBot'
                ),
                msg=self.secret.encode(),
                digestmod=hashlib.sha256,
            ).digest(),
            '\n'.join(
                f'{key}={field}'
                for key, field in sorted(
                    (key, field)
                    for key, field in parsed.items()
                    if key != 'hash'
                )
            ).encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, parsed['hash']):
            self.log.warning(INVALID_INIT_DATA_SIGN_LOG, client_type)
            raise InvalidSignatureError()
        return user_data

    def _parse_init_data(
        self, init_data: str, client_type: ClientType = ClientType.user
    ) -> dict:
        """Parse init data."""
        try:
            parsed_raw = urllib.parse.parse_qs(init_data, strict_parsing=True)
        except Exception:
            self.log.warning(INVALID_INIT_DATA_FORMAT_LOG, client_type)
            raise InvalidInitDataError()
        return {key: field[0] for key, field in parsed_raw.items()}

    def _check_init_data(
        self, parsed: dict, client_type: ClientType = ClientType.user
    ) -> dict:
        """Check init data."""
        errors: list = []

        self._check_required_fields(parsed, errors)
        user_data = self._check_user_data(parsed, errors)
        self._check_auth_date(parsed, errors, client_type)

        if errors:
            self.log.warning(INVALID_INIT_DATA_LOG, client_type, errors)
            raise InvalidInitDataError()

        return user_data

    def _check_required_fields(self, parsed: dict, errors: list):
        """Check required fields."""
        missing = [
            field
            for field in REQUIRED_INIT_DATA_FIELDS
            if field not in parsed or parsed.get(field) in (None, '')
        ]
        if missing:
            errors.append(
                AuthMessage.missed_fields.format(fields=', '.join(missing))
            )

    def _check_auth_date(
        self,
        parsed: dict,
        errors: list,
        client_type: ClientType = ClientType.user,
    ):
        """Check auth date."""
        try:
            auth_date = int(parsed.get('auth_date', 0))
        except ValueError:
            errors.append(AuthMessage.init_data_invalid_auth_date)
            return

        now = int(time.time())
        if auth_date > now + self.skew:
            errors.append(AuthMessage.init_data_invalid_auth_date)
            return
        max_age = (
            self.user_init_data_ttl
            if client_type == ClientType.user
            else self.bot_init_data_ttl
        )
        if now - auth_date > max_age:
            errors.append(AuthMessage.init_data_expired)

    def _check_user_data(self, parsed: dict, errors: list) -> dict:
        """Check user data."""
        try:
            user_data = json.loads(parsed.get('user', '{}'))
        except Exception:
            errors.append(AuthMessage.init_data_invalid_user_data)
            return {}

        if not user_data:
            errors.append(AuthMessage.init_data_no_user_data)
            return {}

        user_id = user_data.get('id')
        if not user_id:
            errors.append(AuthMessage.init_data_user_id_missed)
            return {}

        return user_data
