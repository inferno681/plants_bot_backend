from typing import Any

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

from app.constants.auth import PASSWORD_REGEX, AuthMessage


class PasswordStr(str):
    """A custom string type for password validation."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Generate base scheme."""
        schema = handler(str)
        return core_schema.no_info_after_validator_function(
            cls.validate_password, schema
        )

    @classmethod
    def validate_password(cls, password: str) -> str:
        """Validate the provided password string."""
        if not PASSWORD_REGEX.match(password):
            raise ValueError(AuthMessage.weak_password)
        return password

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Scheme generation with regex."""
        json_schema = handler(core_schema)
        json_schema['pattern'] = PASSWORD_REGEX.pattern
        json_schema['example'] = "ValidPassword123!"
        return json_schema
