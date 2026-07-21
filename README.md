# RawLake

Data lake system for raw asset management with Prefect orchestration, SQLAlchemy ORM, and a Click CLI.

## Stack

- **Python** 3.11+
- **Prefect** 3.0+ - Workflow orchestration
- **SQLAlchemy** 2.0+ - ORM
- **Alembic** - Database migrations
- **Click** - CLI application
- **Pydantic** - Data validation
- **PostgreSQL** - Primary database

## Structure

```
rawlake/
├── configs/products/     # Product manifests (YAML)
├── src/rawlake/          # Main package
│   ├── core/             # Cross-cutting (config, database, logging, exceptions)
│   ├── cli/              # Click CLI application
│   ├── extractors/       # Data extraction (BaseExtractor, HttpExtractor)
│   ├── flows/            # Prefect flows (run_ingestion)
│   ├── manifests/        # Manifest loader and sync
│   ├── metadata/         # ORM models and repository
│   ├── schemas/          # Pydantic schemas (ProductManifest)
│   ├── services/         # Business logic (IngestionService)
│   ├── storage/          # Storage abstraction (local, future: s3)
│   └── utils/            # Utilities
├── migrations/           # Alembic migrations
├── tests/                # Test suite
├── docker-compose.yml    # Local PostgreSQL
├── justfile              # Development tasks
└── pyproject.toml        # Project configuration
```

## Architecture

RawLake follows a modular architecture with clear separation of concerns:

### Core (`src/rawlake/core/`)
Cross-cutting components used throughout the system:
- `config.py` - Centralized configuration with `.env` loading (pydantic-settings)
- `database.py` - Database engine and sessions
- `logging.py` - Structured logging
- `exceptions.py` - Custom exception hierarchy

### Domain Modules
- `metadata/` - ORM models (Dataset, Ingestion, Archivo) and repository
- `extractors/` - Data extractors (BaseExtractor + HttpExtractor generic)
- `services/` - Business logic (IngestionService)
- `storage/` - Storage backends
- `flows/` - Single Prefect flow (`run_ingestion`) for all products

### Product Configuration
Each product is declared in a YAML manifest under `configs/products/`:
- Extraction source, extractor type, landing config, schedule
- Validated by Pydantic (`ProductManifest`) before touching network or DB
- A product that is just "URL -> CSV" only adds a `.yaml`, no `.py`

### Interfaces
- `cli/` - Command-line interface (Click)

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

# List datasets
just cli datasets list

# List ingestions
just cli ingestions list

# Register an archivo manually
just cli register --dataset <key> --period <label> --file <path>

# Run ingestion from manifest
just cli ingest run --dataset <key>

# Deploy Prefect deployments for all products
just cli flows deploy
```

## Development

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

- `DB_USER` - PostgreSQL user
- `DB_PASSWORD` - PostgreSQL password
- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port
- `DB_NAME` - PostgreSQL database name
- `LOG_LEVEL` - Logging level
- `RAWLAKE_LOCAL_ROOT` - Root path for raw file storage
