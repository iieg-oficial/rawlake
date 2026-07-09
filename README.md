# RawLake

Data lake system for raw asset management with Prefect orchestration, SQLAlchemy ORM, and a Typer CLI.

## Stack

- **Python** 3.11+
- **Prefect** 3.0+ - Workflow orchestration
- **SQLAlchemy** 2.0+ - ORM
- **Alembic** - Database migrations
- **Typer** - CLI application
- **Pydantic** - Data validation
- **PostgreSQL** - Primary database

## Structure

```
rawlake/
├── src/rawlake/          # Main package
│   ├── core/             # Core components (config, database, logging, exceptions)
│   ├── cli/              # Typer CLI application
│   ├── extractors/       # Data extraction (BaseExtractor)
│   ├── flows/            # Prefect flows (BaseFlow)
│   ├── metadata/         # Metadata models and repository
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic (BaseService)
│   ├── storage/          # Storage abstraction (MinIO-ready)
│   └── utils/            # Utilities
├── configs/products/     # Product-specific configurations
├── flows/               # Prefect flow definitions
├── migrations/          # Alembic migrations
├── tests/               # Test suite
├── docker-compose.yml   # Local PostgreSQL
├── justfile             # Development tasks
└── pyproject.toml       # Project configuration
```

## Architecture

RawLake follows a modular architecture with clear separation of concerns:

### Core (`src/rawlake/core/`)
Cross-cutting components used throughout the system:
- `config.py` - Centralized configuration (pydantic-settings)
- `database.py` - Database engine, sessions, connection pooling
- `logging.py` - Logging configuration
- `constants.py` - Global system constants
- `exceptions.py` - Custom exception hierarchy
- `types.py` - Type aliases and protocols

### Domain Modules
- `metadata/` - ORM models (Dataset, Ingestion, Archivo) and repository
- `extractors/` - Data extractors (inherit from BaseExtractor)
- `services/` - Business logic (inherit from BaseService)
- `storage/` - Storage backends
- `flows/` - Prefect flows (inherit from BaseFlow)

### Interfaces
- `cli/` - Command-line interface

## Setup

```bash
# Install dependencies and pre-commit hooks
just setup

# Start local PostgreSQL
just db-up

# Run migrations
just migrate
```

## CLI

```bash
# Show version
just cli version
```

## Development

Common tasks available via `just`:

| Command | Description |
|---------|-------------|
| `just setup` | Install dependencies and pre-commit hooks |
| `just install` | Install dependencies with uv sync |
| `just lint` | Run ruff linter |
| `just format` | Format code with ruff |
| `just test` | Run pytest |
| `just db-up` | Start PostgreSQL container |
| `just db-down` | Stop PostgreSQL container |
| `just migrate` | Run alembic migrations |
| `just revision <msg>` | Create new alembic revision |
| `just cli <args>` | Run rawlake CLI |

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL` - PostgreSQL connection string
- `PREFECT_API_URL` - Prefect API endpoint
- `STORAGE_ROOT` - Root path for raw file storage
