FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
COPY apps/api/pyproject.toml apps/api/
COPY packages/shared/pyproject.toml packages/shared/
COPY packages/agents/pyproject.toml packages/agents/
COPY packages/ai/pyproject.toml packages/ai/
COPY packages/ingestion/pyproject.toml packages/ingestion/

COPY packages/ packages/
COPY apps/api/ apps/api/

RUN uv sync --package lexguard-api --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "lexguard_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
