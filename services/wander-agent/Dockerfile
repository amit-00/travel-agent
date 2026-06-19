FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.30 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/wander-agent/pyproject.toml services/wander-agent/
RUN uv sync --frozen --no-dev --no-install-project --package wander-agent

COPY services/wander-agent/src/ services/wander-agent/src/
RUN uv sync --frozen --no-dev --package wander-agent

RUN useradd --no-create-home appuser
USER appuser

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "wander_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
