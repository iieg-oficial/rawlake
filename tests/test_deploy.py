from __future__ import annotations

from pathlib import Path

import yaml

from rawlake.flows import deploy
from rawlake.manifests.loader import load_manifest


def test_generated_deployment_does_not_pin_a_container_path(tmp_path: Path, monkeypatch) -> None:
    """The entrypoint resolves from the working directory, so `path` only couples us to Docker."""
    manifest = load_manifest("inegi_imaief")
    monkeypatch.setattr(deploy, "load_all_manifests", lambda: [manifest])
    monkeypatch.setattr(deploy, "PREFECT_YAML_PATH", tmp_path / "prefect.yaml")

    count = deploy.generate_prefect_yaml()

    generated = yaml.safe_load((tmp_path / "prefect.yaml").read_text())
    assert count == 1
    deployment = generated["deployments"][0]
    assert deployment["name"] == "ingest-inegi_imaief"
    assert "path" not in deployment
