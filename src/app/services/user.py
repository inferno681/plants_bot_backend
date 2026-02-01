from logging import getLogger

from beanie import PydanticObjectId
from fastapi import FastAPI, Request

from app.constants.auth import SID, SUB
from app.constants.user import USER_DELETE_MSG
from app.exceptions.auth import UserNotFoundError
from app.logs.user import USER_DELETE_LOG, USER_SERVICE_START_LOG
from app.models import User, UserStatus
from app.schemes import UserSession, WebUserInfo
from app.services import MongoPipelineBuilder, TokenService


class UserService:
    """User service."""

    def __init__(
        self,
        token_service: TokenService,
        pipeline_builder: MongoPipelineBuilder,
    ):
        """User service initialization."""
        self.token_service = token_service
        self.pipeline_builder = pipeline_builder

        self.log = getLogger(__name__)
        self.log.info(USER_SERVICE_START_LOG)

    async def get_current_user_uid_sid(self, token: str) -> UserSession:
        """Get current user DI."""
        payload = await self.token_service.check_token(token)
        return UserSession(uid=payload[SUB], sid=payload[SID])

    async def get_current_user_id(self, token: str) -> str:
        """Get current user DI."""
        return (await self.token_service.check_token(token))[SUB]

    async def get_web_user_info(
        self, user_id: PydanticObjectId
    ) -> WebUserInfo:
        """Get user info."""
        pipeline = self.pipeline_builder.build_user_info_pipeline(
            user_id=user_id
        )
        docs = await User.aggregate(pipeline).to_list()
        if not docs:
            raise UserNotFoundError()

        return WebUserInfo(**docs[0])

    async def delete_user(self, user_id: PydanticObjectId) -> dict:
        """Delete user and associated accounts."""
        user = await User.find_one(User.id == user_id)
        if not user:
            raise UserNotFoundError()
        user.status = UserStatus.deleted
        await user.save_changes()
        self.log.info(USER_DELETE_LOG, str(user_id))
        return {'message': USER_DELETE_MSG}


def init_user_service(
    app: FastAPI,
    token_service: TokenService,
    pipeline_builder: MongoPipelineBuilder,
) -> None:
    """Create UserService once and store on app.state."""
    app.state.user_service = UserService(
        token_service=token_service,
        pipeline_builder=pipeline_builder,
    )


def get_user_service(request: Request) -> UserService:
    """FastAPI dependency for UserService."""
    return request.app.state.user_service
