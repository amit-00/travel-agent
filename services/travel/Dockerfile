FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.30 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/travel/pyproject.toml services/travel/
RUN uv sync --frozen --no-dev --no-install-project --package travel

COPY services/travel/src/ services/travel/src/
RUN uv sync --frozen --no-dev --package travel

RUN useradd --no-create-home appuser
USER appuser

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "travel.main:app", "--host", "0.0.0.0", "--port", "8000"]
