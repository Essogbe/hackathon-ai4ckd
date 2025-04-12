# Base stage with shared Python setup
FROM python:3-slim AS base

RUN apt-get update && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Build stage with uv and dependencies
FROM base AS build

# Install uv binary directly (no pip)
COPY --from=ghcr.io/astral-sh/uv:0.4.9 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY uv.lock pyproject.toml ./

# Sync dependencies (no --mount)
RUN uv sync --frozen --no-install-project --no-dev

# Add source code and re-sync (in case extras are in it)
COPY ./app/ ./
COPY artefacts .


# Runtime image: minimal with only needed files and venv
FROM base AS runtime

WORKDIR /app

RUN addgroup --gid 1001 --system nonroot && \
    adduser --no-create-home --shell /bin/false \
      --disabled-password --uid 1001 --system --group nonroot

USER nonroot:nonroot

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=build --chown=nonroot:nonroot /app /app


EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
