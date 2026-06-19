.PHONY: install dev lint test py-dev py-lint py-test listings-dev listings-lint listings-test ts-dev ts-lint ts-test

install:
	uv sync --all-packages --all-groups
	pnpm install

dev:
	$(MAKE) -j2 wander-agent-dev ts-dev

wander-agent-dev:
	uv run --package wander-agent uvicorn wander_agent.main:app --reload

wander-agent-lint:
	uv run --package wander-agent ruff check services/wander-agent/src services/wander-agent/tests
	uv run --package wander-agent ruff format --check services/wander-agent/src services/wander-agent/tests
	uv run --package wander-agent mypy services/wander-agent/src

wander-agent-test:
	uv run --package wander-agent pytest services/wander-agent/tests/ -v

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

lint: wander-agent-lint listings-lint travel-lint ts-lint

test: wander-agent-test listings-test travel-test ts-test
