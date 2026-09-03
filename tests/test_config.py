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


def test_configs_dir_defaults_to_the_repository_directory() -> None:
    """The default only holds for a checkout; containers override it with RAWLAKE_CONFIGS_DIR."""
    configs_dir = Path(Config(_env_file=None).RAWLAKE_CONFIGS_DIR)

    assert (configs_dir / "products").is_dir()


def test_local_root_defaults_inside_the_repository() -> None:
    """The default must not require root, and must not depend on the current working directory."""
    local_root = Path(Config(_env_file=None).RAWLAKE_LOCAL_ROOT)

    assert local_root.is_absolute()
    assert local_root.name == "data"
