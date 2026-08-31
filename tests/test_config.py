from pathlib import Path

from rawlake.core.config import Config


def test_config_ignores_variables_owned_by_other_services(tmp_path: Path) -> None:
    """The .env file is shared with Docker Compose, so unrelated keys must not break the app."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_USER=rawlake\nPREFECT_UI_PORT=4200\nPREFECT_SERVER_UI_API_URL=http://localhost:4200/api\n",
        encoding="utf-8",
    )

    config = Config(_env_file=env_file)

    assert config.DB_USER == "rawlake"
