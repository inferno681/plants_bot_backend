from fastapi import Depends

from app.services import get_email_service

email_service_dep = Depends(get_email_service)
