from beanie import PydanticObjectId
from fastapi import APIRouter

from app.constants.email import (
    EMAIL_CONFIRMATION_MSG,
    EMAIL_CONFIRMATION_SENT_MSG,
)
from app.dependencies import (
    current_user_id_dep,
    email_service_dep,
    user_service_dep,
    web_auth_service_dep,
)
from app.schemes import ClientInfo, UserSettings, WebUserInfo
from app.services import EmailService, UserService, WebAuthService
from app.utils import client_info_dependency

router = APIRouter()


@router.get('/me', response_model=WebUserInfo)
async def get_web_user_info(
    user_id: str = current_user_id_dep,
    user_service: UserService = user_service_dep,
):
    """Get user info endpoint."""
    return await user_service.get_web_user_info(
        user_id=PydanticObjectId(user_id)
    )


@router.patch('/me', response_model=WebUserInfo)
async def user_info_update(
    update_info: UserSettings,
    user_id: str = current_user_id_dep,
    user_service: UserService = user_service_dep,
):
    """User data update endpoint."""
    return await user_service.update_info(
        PydanticObjectId(user_id), update_info
    )


@router.delete('/me')
async def delete_user(
    user_id: str = current_user_id_dep,
    user_service: UserService = user_service_dep,
    web_auth_service: WebAuthService = web_auth_service_dep,
):
    """Delete user endpoint."""
    message = await user_service.delete_user(user_id=PydanticObjectId(user_id))
    await web_auth_service.logout_all_sessions(user_id)
    return message


@router.post('/email/confirmation')
async def resend_confirmation_email(
    user_id: str = current_user_id_dep,
    client_info: ClientInfo = client_info_dependency,
    email_service: EmailService = email_service_dep,
):
    """Resend confirmation email endpoint."""
    await email_service.send_confirmation_email(
        user_id=PydanticObjectId(user_id), client_info=client_info
    )
    return {'message': EMAIL_CONFIRMATION_SENT_MSG}


@router.post('/email/confirm')
async def confirm_email(
    token: str,
    client_info: ClientInfo = client_info_dependency,
    email_service: EmailService = email_service_dep,
):
    """Confirm email endpoint."""
    await email_service.confirm_email(token=token, client_info=client_info)
    return {'message': EMAIL_CONFIRMATION_MSG}
