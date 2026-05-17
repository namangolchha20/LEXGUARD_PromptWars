.PHONY: install dev api web worker lint format test docker-up docker-down

install:
	uv sync --all-packages
	pnpm install

dev:
	docker compose up -d postgres redis
	uv run --package lexguard-api uvicorn lexguard_api.main:app --reload --host 0.0.0.0 --port 8000

api:
	uv run --package lexguard-api uvicorn lexguard_api.main:app --reload --host 0.0.0.0 --port 8000

web:
	pnpm --filter @lexguard/web dev

worker:
	uv run --package lexguard-analyze-worker python -m lexguard_analyze_worker

lint:
	uv run ruff check apps packages workers
	uv run ruff format --check apps packages workers
	pnpm lint

format:
	uv run ruff format apps packages workers
	uv run ruff check --fix apps packages workers
	pnpm format

test:
	uv run pytest

docker-up:
	docker compose up -d

docker-down:
	docker compose down
