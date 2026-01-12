from fastapi import Depends, Request

from app.constants.auth import UNKNOWN_LITERAL
from app.schemes import ClientInfo


def get_client_info(request: Request) -> ClientInfo:
    xff = request.headers.get('x-forwarded-for')
    if xff:
        ip = xff.split(',')[0].strip()
    else:
        client = request.client
        ip = client.host if client else "unknown"

    ua = request.headers.get('user-agent') or UNKNOWN_LITERAL

    return ClientInfo(ip=ip, ua=ua)


client_info_dependency = Depends(get_client_info)
