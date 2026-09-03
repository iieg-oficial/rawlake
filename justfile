# Show every available recipe, grouped by area.
default:
    @just --list --unsorted

# Install dependencies and register the git hooks.
[group('entorno')]
setup:
    uv sync
    chmod +x .githooks/commit-msg
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg

# Sync dependencies without touching the hooks.
[group('entorno')]
install:
    uv sync

# Report lint errors in source and tests.
[group('calidad')]
lint:
    uv run ruff check src/ tests/

# Rewrite source and tests with the project formatter.
[group('calidad')]
format:
    uv run ruff format src/ tests/

# Run the test suite.
[group('calidad')]
test:
    uv run pytest

# Run every pre-commit hook over the whole repository.
[group('calidad')]
hooks:
    uv run pre-commit run --all-files --show-diff-on-failure

# Apply pending Alembic migrations.
[group('base de datos')]
migrate:
    uv run alembic upgrade head

# Autogenerate a migration from the current models.
[group('base de datos')]
revision message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Open a psql session against the RawLake database.
[group('base de datos')]
psql:
    docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

# Build the images and start the whole stack in the background.
[group('compose')]
up:
    docker compose up -d --build

# Stop the stack, keeping the database volume.
[group('compose')]
down:
    docker compose down

# Show the state of every service, including the ones that exited.
[group('compose')]
ps:
    docker compose ps -a

# Follow the logs of one service, or of every service when none is given.
[group('compose')]
logs service="":
    docker compose logs -f {{service}}

# Rebuild the image and republish the Prefect deployments.
[group('compose')]
deploy:
    docker compose up -d --build prefect-deploy

# Ingest a dataset through its Prefect deployment, writing to storage and the database.
[group('compose')]
ingest dataset:
    docker compose exec prefect-worker \
        prefect deployment run 'run_ingestion/ingest-{{dataset}}' --param dry_run=false

# Extract a dataset and resolve its periods without writing anything.
[group('compose')]
ingest-dry dataset:
    docker compose exec prefect-worker \
        prefect deployment run 'run_ingestion/ingest-{{dataset}}' --param dry_run=true

# Run the RawLake CLI on the host.
[group('cli')]
cli *args:
    uv run rawlake {{args}}
