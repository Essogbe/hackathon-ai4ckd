# Pin the Python base image for all stages and
# install all shared dependencies.
FROM python:3-slim AS base

RUN apt-get update && rm -rf /var/lib/apt/lists/*

# Tweak Python to run better in Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Build stage: dev & build dependencies can be installed here
FROM base AS build

RUN apt-get update && rm -rf /var/lib/apt/lists/*

# "Install" uv to the build stage
COPY --from=ghcr.io/astral-sh/uv:0.4.9 /uv /bin/uv

# UV_COMPILE_BYTECODE=1 is an important startup time optimization
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

COPY uv.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

# Runtime stage: copy only the virtual environment.
FROM base AS runtime
WORKDIR /app

RUN addgroup --gid 1001 --system nonroot && \
    adduser --no-create-home --shell /bin/false \
      --disabled-password --uid 1001 --system --group nonroot

USER nonroot:nonroot

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=build --chown=nonroot:nonroot /app ./


EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port 8080
