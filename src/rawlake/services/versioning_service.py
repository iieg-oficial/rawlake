from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class VersioningService:
    @staticmethod
    def generate_run_id() -> str:
        """Generate a unique run ID."""
        return f"run-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def generate_version_timestamp() -> datetime:
        """Generate a timestamp for version naming (UTC)."""
        return datetime.utcnow()

    @staticmethod
    def format_version_timestamp(ts: datetime) -> str:
        """Format a timestamp for use in version paths."""
        return ts.strftime("%Y-%m-%dT%H-%M-%S")

    @staticmethod
    def generate_submission_id() -> str:
        """Generate a unique submission ID for manual dropzone."""
        return f"submission-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
