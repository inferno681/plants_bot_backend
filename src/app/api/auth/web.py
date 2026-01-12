from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.schemes import ClientInfo, Tokens
from app.services import web_auth_service
from app.utils import client_info_dependency

router = APIRouter()


@router.post('/login_doc', response_model=Tokens)
async def doc_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    client_info: ClientInfo = client_info_dependency,
):
    """Documentation user login endpoint."""
    return await web_auth_service.login_doc(
        form_data.password, client_info.ip, client_info.ua
    )
