# RawLake - Sesión de desarrollo

## Proyecto
Data lake institucional para ingesta de archivos raw. MVP construido con Python 3.11+, Prefect (en lugar de Airflow), SQLAlchemy, Alembic, PostgreSQL, Click CLI.

## Convenciones de Git Flow

### Ramas
- Formato: `{issue_number}-{type}-{short-description}-phase-{N}`
- Tipos: `feat`, `fix`, `chore`, `docs`
- Ejemplo: `3-feat-implementar-core-de-register-raw-asset-fase-1`

### Commits
- Formato: `type(scope): description`
- Tipos: `feat`, `fix`, `chore`, `docs`
- Ejemplo: `feat(cli): add register command`

### Issues
- Título: `type: descripción corta (Fase N)`
- Body incluye:
  - Objetivo
  - Entregables (checkboxes)
  - Decisiones de diseño
  - **Instrucciones para el revisor** (paso a paso qué correr y cómo verificar)
  - Tabla de archivos clave

### PRs
- Base: `develop`
- Body incluye:
  - Resumen ejecutivo
  - Cambios detallados
  - Checklist de完成
  - Criterio de aceptación con comandos de prueba

## Arquitectura

- `register_raw_asset()` es el corazón del sistema
- Repository único (evitar sobreingeniería)
- Lógica de negocio en `services/`
- Storage abstraction (preparado para MinIO)
- Timestamps ISO para versionado

## Setup rápido

```bash
git checkout -b {rama}
uv sync
cp .env.example .env  # editar RAWLAKE_LOCAL_ROOT
docker compose up -d
uv run alembic upgrade head
```

## Comandos útiles

```bash
just install    # Instalar dependencias
just lint       # Ruff check
just format     # Ruff format
just test       # Pytest
just db-up      # Levantar PostgreSQL
just migrate    # Alembic upgrade
rawlake --help  # Ver CLI
```

## Stack
- Python 3.11+, uv, hatchling (src layout)
- SQLAlchemy 2.0+, Alembic
- Click CLI (no Typer - tiene problemas con entry points)
- Pydantic, pydantic-settings
- Prefect 3.0+
- PostgreSQL 16
- Ruff, pytest