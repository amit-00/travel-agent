.PHONY: install dev lint test py-dev py-lint py-test listings-dev listings-lint listings-test ts-dev ts-lint ts-test

install:
	uv sync --all-packages --all-groups
	pnpm install

dev:
	$(MAKE) -j2 py-dev ts-dev

py-dev:
	uv run --package agent uvicorn agent.main:app --reload

py-lint:
	uv run --package agent ruff check services/
	uv run --package agent ruff format --check services/
	uv run --package agent mypy services/agent/src

py-test:
	uv run --package agent pytest services/agent/tests/ -v

listings-dev:
	uv run --package listings uvicorn listings.main:app --reload --port 8001

listings-lint:
	uv run --package listings ruff check services/listings/src services/listings/tests
	uv run --package listings ruff format --check services/listings/src services/listings/tests
	uv run --package listings mypy services/listings/src

listings-test:
	uv run --package listings pytest services/listings/tests/ -v

ts-dev:
	pnpm --filter web dev

ts-lint:
	pnpm --filter web lint
	pnpm --filter web exec prettier --check .

ts-test:
	pnpm --filter web test

lint: py-lint ts-lint

test: py-test ts-test
