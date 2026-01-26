from fastapi import Depends

from app.services import get_user_service

user_service_dep = Depends(get_user_service)
