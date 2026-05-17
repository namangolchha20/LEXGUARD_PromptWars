FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
COPY workers/analyze-worker/pyproject.toml workers/analyze-worker/
COPY packages/shared/pyproject.toml packages/shared/
COPY packages/agents/pyproject.toml packages/agents/
COPY packages/ai/pyproject.toml packages/ai/
COPY packages/ingestion/pyproject.toml packages/ingestion/

COPY packages/ packages/
COPY workers/analyze-worker/ workers/analyze-worker/

RUN uv sync --package lexguard-analyze-worker --no-dev

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "lexguard_analyze_worker"]
