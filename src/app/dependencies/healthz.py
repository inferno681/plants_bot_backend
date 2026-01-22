from fastapi import Depends

from app.services import get_healthz_service

healthz_service_dep = Depends(get_healthz_service)
