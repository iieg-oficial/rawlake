setup:
    uv sync
    chmod +x .githooks/commit-msg
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg

install:
    uv sync

lint:
    uv run ruff check src/ tests/

format:
    uv run ruff format src/ tests/

test:
    uv run pytest

db-up:
    docker compose up -d

db-down:
    docker compose down

migrate:
    uv run alembic upgrade head

revision message:
    uv run alembic revision --autogenerate -m "{{message}}"

cli *args:
    uv run rawlake {{args}}
