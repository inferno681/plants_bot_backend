from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.token import TOKEN_MAP, TokenError
from app.constants import MSG, TYPE, STATUS


async def token_exception_handler(request: Request, exc: TokenError):
    error_info = TOKEN_MAP[type(exc)]

    return JSONResponse(
        status_code=error_info[STATUS],
        content={
            'detail': [
                {
                    'loc': ['token'],
                    'msg': error_info[MSG],
                    'type': error_info[TYPE],
                }
            ]
        },
    )


def register_handlers(app: FastAPI):
    app.add_exception_handler(TokenError, token_exception_handler)
