FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock* /app/

RUN uv sync --no-dev --frozen --no-cache --no-install-project

RUN mkdir -p ./src

COPY ./src/config  ./src/config

COPY ./alembic.ini  ./alembic.ini

COPY ./src/app  ./src/app

ENV PYTHONPATH=/app/src/

CMD ["python", "src/app/run_main.py"]
