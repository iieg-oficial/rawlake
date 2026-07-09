"""Constantes globales del sistema RawLake."""

# Ingestion Modes
MODE_MANUAL = "manual"
MODE_AUTOMATED = "automated"
MODE_HYBRID = "hybrid"

# Run Status
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_DUPLICATED = "duplicated"

# Trigger Types
TRIGGER_SCHEDULED = "scheduled"
TRIGGER_MANUAL_AIRFLOW = "manual_airflow"
TRIGGER_MANUAL_DROPZONE = "manual_dropzone"
TRIGGER_MANUAL_CLI = "manual_cli"
TRIGGER_BACKFILL = "backfill"
TRIGGER_RETRY = "retry"

# Storage
DEFAULT_STORAGE_BACKEND = "local"
METADATA_FILENAME = "metadata.json"

# Hashing
HASH_ALGORITHM = "sha256"
HASH_CHUNK_SIZE = 8192
