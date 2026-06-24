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
│   ├── cli/              # Typer CLI application
│   ├── config/           # Configuration management
│   ├── extractors/       # Data extraction
│   ├── metadata/         # Metadata handling
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
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
