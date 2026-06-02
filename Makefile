.PHONY: install dev lint test py-dev py-lint py-test ts-dev ts-lint ts-test

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

ts-dev:
	pnpm --filter web dev

ts-lint:
	pnpm --filter web lint
	pnpm --filter web exec prettier --check .

ts-test:
	pnpm --filter web test

lint: py-lint ts-lint

test: py-test ts-test
