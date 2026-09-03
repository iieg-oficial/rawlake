"""Ensure Docker Compose variables are documented and sensitive values are interpolated."""

from __future__ import annotations

import re
import sys
from pathlib import Path

COMPOSE_PATH = Path("docker-compose.yml")
ENV_EXAMPLE_PATH = Path(".env.example")
VARIABLE_PATTERN = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")
ENV_ASSIGNMENT_PATTERN = re.compile(r"^\s{6}([A-Z][A-Z0-9_]*):\s*(.+?)\s*$", re.MULTILINE)
# Keys that carry host configuration or credentials, and must never be written
# literally in the Compose file. Container-internal constants (mount targets,
# service hostnames, in-network ports) are deliberately excluded: they are part
# of the image contract, not of the environment.
SENSITIVE_KEYS = {
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "PREFECT_API_DATABASE_CONNECTION_URL",
    "PREFECT_SERVER_UI_API_URL",
}


def main() -> int:
    compose = COMPOSE_PATH.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    referenced = set(VARIABLE_PATTERN.findall(compose))
    documented = {
        line.split("=", maxsplit=1)[0]
        for raw_line in env_example.splitlines()
        if (line := raw_line.strip()) and not line.startswith("#") and "=" in line
    }
    missing = sorted(referenced - documented)

    assignments = dict(ENV_ASSIGNMENT_PATTERN.findall(compose))
    hardcoded = sorted(
        key for key in SENSITIVE_KEYS if key in assignments and "${" not in assignments[key]
    )

    errors: list[str] = []
    if missing:
        errors.append(f"Missing from {ENV_EXAMPLE_PATH}: {', '.join(missing)}")
    if hardcoded:
        errors.append(f"Hardcoded Compose values: {', '.join(hardcoded)}")
    if not errors:
        return 0

    print("Compose environment contract failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
