from fastapi import Depends

from app.services import get_link_service

link_service_dep = Depends(get_link_service)
