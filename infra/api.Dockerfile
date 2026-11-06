# API image. Build from the repo root: docker build -f infra/api.Dockerfile -t reshelf-api .
# The layout under /app mirrors the repo so api.py finds data/scenarios (REPO_ROOT is parents[4]).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RESHELF_DB=/data/reshelf.db \
    PYTHONPATH=/app/data/generator

WORKDIR /app/apps/api

COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY apps/api/ ./
COPY data/generator /app/data/generator
COPY data/scenarios /app/data/scenarios
RUN uv sync --frozen --no-dev

RUN mkdir /data
VOLUME /data
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/health')"

CMD ["uv", "run", "--no-dev", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
