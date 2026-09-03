from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = PROJECT_ROOT / "scripts" / "validate_compose_env.py"


def run_validator(
    tmp_path: Path, compose: str, env_example: str
) -> subprocess.CompletedProcess[str]:
    (tmp_path / "docker-compose.yml").write_text(compose, encoding="utf-8")
    (tmp_path / ".env.example").write_text(env_example, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )


def test_reports_variable_missing_from_env_example(tmp_path: Path) -> None:
    result = run_validator(
        tmp_path,
        "services:\n  worker:\n    environment:\n      RAWLAKE_LOCAL_ROOT: ${RAWLAKE_LOCAL_ROOT}\n",
        "DB_NAME=rawlake\n",
    )

    assert result.returncode == 1
    assert "Missing from .env.example: RAWLAKE_LOCAL_ROOT" in result.stderr


def test_reports_fully_hardcoded_sensitive_value(tmp_path: Path) -> None:
    result = run_validator(
        tmp_path,
        "services:\n  postgres:\n    environment:\n      POSTGRES_PASSWORD: rawlake\n",
        "DB_PASSWORD=rawlake\n",
    )

    assert result.returncode == 1
    assert "Hardcoded Compose values: POSTGRES_PASSWORD" in result.stderr


def test_accepts_connection_url_with_interpolated_credentials(tmp_path: Path) -> None:
    result = run_validator(
        tmp_path,
        (
            "services:\n  prefect-server:\n    environment:\n"
            "      PREFECT_API_DATABASE_CONNECTION_URL: "
            "postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}\n"
        ),
        "DB_USER=rawlake\nDB_PASSWORD=rawlake\nDB_NAME=rawlake\n",
    )

    assert result.returncode == 0


def test_accepts_container_path_pinned_alongside_an_interpolated_bind_mount(
    tmp_path: Path,
) -> None:
    """The mount target inside the container is fixed; only the host side is configurable."""
    result = run_validator(
        tmp_path,
        (
            "services:\n  worker:\n    environment:\n"
            "      RAWLAKE_LOCAL_ROOT: /mnt/datalake\n"
            "    volumes:\n"
            "      - ${RAWLAKE_LOCAL_ROOT:-./data}:/mnt/datalake\n"
        ),
        "RAWLAKE_LOCAL_ROOT=./data\n",
    )

    assert result.returncode == 0, result.stderr
