FROM python:3.14-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev --no-editable


FROM python:3.14-alpine

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY ./app /app/app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
