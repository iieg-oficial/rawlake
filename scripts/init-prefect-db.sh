#!/bin/bash
# Prefect runs its own Alembic migrations with the default `alembic_version`
# table, which collides with RawLake's. Give it a dedicated database on the
# same instance. This script only runs when the data volume is first created.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE "$PREFECT_DB_NAME" OWNER "$POSTGRES_USER";
EOSQL
