from __future__ import annotations

from pathlib import Path

import click
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from rawlake.metadata.db import get_db_session
from rawlake.metadata.models import IngestionMode, TriggerType
from rawlake.metadata.repository import Repository
from rawlake.services.ingestion_service import IngestionService


@click.group()
def cli():
    """RawLake data lake CLI."""
    pass


@cli.command()
def version():
    """Show rawlake version."""
    click.echo("rawlake 0.1.0")


@cli.group()
def products():
    """Manage products."""
    pass


@products.command("list")
def products_list():
    """List all products."""
    with get_db_session() as session:
        repo = Repository(session)
        product_list = repo.list_products()
        if not product_list:
            click.echo("No products found.")
            return
        for p in product_list:
            status = "active" if p.is_active else "inactive"
            click.echo(f"[{status}] {p.product_key} - {p.name}")


@cli.group()
def sources():
    """Manage sources."""
    pass


@sources.command("list")
@click.option("--product", help="Filter by product key")
def sources_list(product):
    """List all sources, optionally filtered by product."""
    with get_db_session() as session:
        repo = Repository(session)
        source_list = repo.list_sources(product_key=product)
        if not source_list:
            click.echo("No sources found.")
            return
        for s in source_list:
            status = "active" if s.is_active else "inactive"
            click.echo(
                f"[{status}] {s.source_key} - {s.name} (type: {s.source_type.value}, mode: {s.ingestion_mode.value})"
            )


@cli.group()
def runs():
    """Manage ingestion runs."""
    pass


@runs.command("list")
@click.option("--product", help="Filter by product key")
@click.option("--limit", default=20, help="Number of runs to show")
def runs_list(product, limit):
    """List recent ingestion runs."""
    with get_db_session() as session:
        repo = Repository(session)
        run_list = repo.list_runs(product_key=product, limit=limit)
        if not run_list:
            click.echo("No runs found.")
            return
        for r in run_list:
            status_icon = {
                "running": "🔄",
                "success": "✅",
                "failed": "❌",
                "duplicated": "📋",
                "rejected": "🚫",
            }.get(r.status.value, "❓")
            click.echo(
                f"{status_icon} {r.run_id} | {r.status.value} | {r.period_label} | {r.created_at.strftime('%Y-%m-%d %H:%M')}"
            )


@cli.group()
def assets():
    """Manage raw assets."""
    pass


@assets.command("latest")
@click.option("--product", required=True, help="Product key")
@click.option("--source", required=True, help="Source key")
@click.option("--period", required=True, help="Period label")
def assets_latest(product, source, period):
    """Get the latest asset for a product/source/period."""
    with get_db_session() as session:
        repo = Repository(session)
        prod = repo.get_product_by_key(product)
        if not prod:
            click.echo(f"Product not found: {product}", err=True)
            return
        src = repo.get_source_by_key(prod.id, source)
        if not src:
            click.echo(f"Source not found: {source}", err=True)
            return
        asset = repo.get_latest_asset(prod.id, src.id, period)
        if not asset:
            click.echo(f"No latest asset found for {product}/{source}/{period}", err=True)
            return
        click.echo(f"Version: {asset.version_number}")
        click.echo(f"Timestamp: {asset.version_timestamp}")
        click.echo(f"Path: {asset.storage_path}")
        click.echo(f"Size: {asset.file_size_bytes} bytes")
        click.echo(f"Checksum: {asset.checksum_sha256}")


@cli.command()
@click.option("--product", required=True, help="Product key")
@click.option("--source", required=True, help="Source key")
@click.option("--period", required=True, help="Period label (e.g., 2026-01)")
@click.option("--file", "file_path", required=True, help="Path to the file to register")
@click.option(
    "--mode", default="manual", type=click.Choice(["manual", "automated"]), help="Ingestion mode"
)
@click.option("--actor", help="Who is initiating this registration")
@click.option("--source-url", help="Original URL of the file")
@click.option("--notes", help="Additional notes")
def register(product, source, period, file_path, mode, actor, source_url, notes):
    """Register a raw asset in the datalake."""
    if not Path(file_path).exists():
        click.echo(f"File not found: {file_path}", err=True)
        return

    ingestion_mode = IngestionMode.MANUAL if mode == "manual" else IngestionMode.AUTOMATED
    trigger_type = TriggerType.MANUAL_CLI

    service = IngestionService()
    result = service.register_raw_asset(
        product_key=product,
        source_key=source,
        period_label=period,
        file_path=file_path,
        ingestion_mode=ingestion_mode,
        trigger_type=trigger_type,
        actor=actor,
        source_url=source_url,
        notes=notes,
    )

    if not result.success:
        click.echo(f"Error: {result.error_message}", err=True)
        return

    if result.is_duplicate:
        click.echo(f"⚠️  Duplicate detected (SHA256 match with existing asset)")
        click.echo(f"    Product: {product}")
        click.echo(f"    Source: {source}")
        click.echo(f"    Period: {period}")
        click.echo(f"    Existing version: {result.asset.version_number}")
        return

    asset = result.asset
    click.echo("✅ Asset registered successfully!")
    click.echo(f"    Product: {product}")
    click.echo(f"    Source: {source}")
    click.echo(f"    Period: {period}")
    click.echo(f"    Version: {asset.version_number}")
    click.echo(f"    Hash: {asset.checksum_sha256}")
    click.echo(f"    Path: {asset.storage_path}")


if __name__ == "__main__":
    cli()
