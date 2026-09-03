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
├── docker-compose.yml    # Local PostgreSQL and Prefect services
├── Dockerfile            # RawLake image used by Prefect
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

# Configure the local environment
cp .env.example .env

# Start local PostgreSQL, Prefect API/UI, worker, and deployments
docker compose up -d --build

# Run migrations
just migrate
```

Raw files land in `./data`, which is git-ignored and created on the first run,
so no root permissions are needed. Point `RAWLAKE_LOCAL_ROOT` at an absolute
path outside the repository for shared environments.

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

# Run ingestion in dry-run mode (no DB writes, no storage writes)
just cli ingest run --dataset <key> --dry-run

# List configured product sources
just cli sources list
just cli sources list --type http
```

## Product Manifests

Each product in `configs/products/` declares its extraction source, landing policy, schedule, and storage backend. Validation is performed by Pydantic (`ProductManifest`) before any network or DB call.

### HTTP extractor with ZIP support

For sources that publish compressed archives (e.g. INEGI's monthly ZIPs), the HTTP extractor can decompress on the fly:

```yaml
extractor:
  type: http
  url: "https://www.inegi.org.mx/contenidos/programas/aief/2018/datosabiertos/conjunto_de_datos_imaief_mensual_csv.zip"
  extract_zip: true           # decompress before returning files
  inner_path: "conjunto_de_datos"   # path inside the ZIP (subfolder)
  inner_glob: "*.csv"         # only these are extracted
  filename_glob: "*.csv"      # final filter on extracted names
```

When `extract_zip: true`, the HTTP extractor:

1. Downloads the payload.
2. Detects ZIP via the `PK\x03\x04` magic bytes.
3. Selects members under `inner_path` matching `inner_glob`.
4. Extracts them to a temp dir and returns `list[Path]`.
5. Cleans up the temp dir in `cleanup()`.

If the payload is not a ZIP, the extractor falls back to writing the raw content to a single temp file (so the same manifest can be used during transient source changes).

### `period_label` resolution

Each registered `Archivo` gets a `period_label` derived per file. The strategy is set in the manifest's `landing` block:

| Strategy | Behavior |
|---|---|
| `current_month` | All files get `YYYY-MM` of the run's UTC date. |
| `from_filename` | Parses each filename with `period_label_pattern` (regex with named groups `year`, `month`). Raises if no match. |
| `from_filename_with_fallback` | Same as `from_filename`, but uses `period_label_fallback` when the pattern doesn't match (logs a warning). |
| `manual` | Requires an explicit `period_label` arg; not supported for multi-file extractors. |

Default pattern (when `period_label_pattern` is omitted):

```
(?P<year>\d{4})_(?P<month>\d{2})\.csv$
```

The `from_filename_with_fallback` strategy is recommended for sources where the filename convention might change in future releases: the manifest declares a fallback policy that keeps the flow working even if the regex stops matching.

Example (IMAIEF):

```yaml
landing:
  period_label_strategy: from_filename_with_fallback
  period_label_pattern: '(?P<year>\d{4})_(?P<month>\d{2})\.csv$'
  period_label_fallback: current_month
```

For IMAIEF, the 44 CSVs match the pattern and resolve to `2026-03`; the `indice.csv` (no date in the name) falls back to the current month.

## Development

Every task is exposed through `just`. Run it with no arguments to list the
available recipes, grouped by area:

```bash
just
```

See [`docs/just.md`](docs/just.md) for the installation guide and the full
command reference.

## Prefect
Prefect runs as part of the local Compose stack. `prefect-server` provides the
API and UI, `prefect-worker` executes flows from the `rawlake-worker` process
pool, and the one-shot `prefect-deploy` service publishes the deployments. They
share the PostgreSQL instance with RawLake but use a separate database
(`PREFECT_DB_NAME`), because both run Alembic migrations against the same
`alembic_version` table.

```bash
# Build the RawLake image and start the full stack
docker compose up -d --build

# Follow service logs
docker compose logs -f prefect-server prefect-worker
```

The UI is available at `http://localhost:4200`. See
[`docs/prefect.md`](docs/prefect.md) for deployment, execution, and
troubleshooting instructions.

### Run a Flow from the UI

1. Open `http://localhost:4200`
2. Navigate to **Flows** → `run_ingestion`
3. Click **Run** → **Custom Run**
4. Enter the `dataset_key` parameter (e.g., `inegi_imaief`)
5. Optionally set `dry_run: true` for testing
6. Click **Run**

### Deploy Flows

Deployments are published automatically by the `prefect-deploy` service on
`docker compose up`. It waits for the server to become healthy, generates the
deployment manifest from the product manifests, publishes it, and exits. The
step is idempotent, so it runs again on every startup without side effects.

```bash
# Republish after editing a manifest, without restarting the other services
docker compose up -d --build prefect-deploy

# Inspect the result
docker compose logs prefect-deploy
```

Deployments run inside the container image at `/app` and can be triggered from
the UI or via API.

### Storage Root Validation

The `run_ingestion` flow automatically ensures the `RAWLAKE_LOCAL_ROOT` directory exists and is writable before processing files. If it doesn't exist, it is created with `mkdir -p`.

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DB_USER` - PostgreSQL user
- `DB_PASSWORD` - PostgreSQL password
- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port
- `DB_NAME` - PostgreSQL database name
- `LOG_LEVEL` - Logging level
- `RAWLAKE_LOCAL_ROOT` - Root path for raw file storage
