import logging
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import auth_router
from app.api.v1 import v1_router
from app.exceptions import exception_handlers
from app.lifespan import lifespan
from config import config

log = logging.getLogger('uvicorn')


app = FastAPI(
    title=config.service.title,
    description=config.service.description,
    lifespan=lifespan,
    openapi_tags=config.service.tags_metadata,
    debug=config.service.debug,
    exception_handlers=exception_handlers,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
    allow_credentials=config.cors.allow_credentials,
)


@app.middleware('http')
async def calculate_process_time(request: Request, call_next):
    """Request time calculation."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers['X-Process-Time'] = str(process_time)
    return response


app.include_router(auth_router)
app.include_router(v1_router)


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=config.service.host,
        port=config.service.port,
        proxy_headers=True,
    )
