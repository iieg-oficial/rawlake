from __future__ import annotations

from pathlib import Path

import click

from rawlake.core.database import get_db_session
from rawlake.flows.ingestion_flow import run_ingestion
from rawlake.manifests.loader import load_all_manifests
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
def datasets():
    """Manage datasets."""
    pass


@datasets.command("list")
def datasets_list():
    """List all datasets."""
    with get_db_session() as session:
        repo = Repository(session)
        dataset_list = repo.list_datasets()
        if not dataset_list:
            click.echo("No datasets found.")
            return
        for d in dataset_list:
            click.echo(f"{d.nombre_corto} - {d.nombre}")


@cli.group()
def ingestions():
    """Manage ingestions."""
    pass


@ingestions.command("list")
@click.option("--dataset", help="Filter by dataset key")
@click.option("--limit", default=20, help="Number of ingestions to show")
def ingestions_list(dataset, limit):
    """List recent ingestions."""
    with get_db_session() as session:
        repo = Repository(session)
        ingestion_list = repo.list_ingestions(dataset_key=dataset, limit=limit)
        if not ingestion_list:
            click.echo("No ingestions found.")
            return
        for i in ingestion_list:
            status_icon = {
                "running": "🔄",
                "success": "✅",
                "failed": "❌",
                "duplicated": "📋",
            }.get(i.status.value, "❓")
            click.echo(
                f"{status_icon} {i.run_id} | {i.status.value} | "
                f"{i.created_at.strftime('%Y-%m-%d %H:%M')}"
            )


@cli.group()
def archivos():
    """Manage archivos."""
    pass


@archivos.command("latest")
@click.option("--dataset", required=True, help="Dataset key")
def archivos_latest(dataset):
    """Get the latest archivo for a dataset."""
    with get_db_session() as session:
        repo = Repository(session)
        ds = repo.get_dataset_by_key(dataset)
        if not ds:
            click.echo(f"Dataset not found: {dataset}", err=True)
            return
        archivo = repo.get_latest_archivo_by_dataset(ds.id)
        if not archivo:
            click.echo(f"No latest archivo found for {dataset}", err=True)
            return
        click.echo(f"Path: {archivo.storage_path}")
        click.echo(f"Size: {archivo.file_size_bytes} bytes")
        click.echo(f"Hash: {archivo.hash_sha256}")
        click.echo(f"Period: {archivo.period_label}")


@cli.command()
@click.option("--dataset", required=True, help="Dataset key")
@click.option("--period", required=True, help="Period label (e.g., 2026-01)")
@click.option("--file", "file_path", required=True, help="Path to the file to register")
@click.option(
    "--mode", default="manual", type=click.Choice(["manual", "automated"]), help="Ingestion mode"
)
@click.option("--actor", help="Who is initiating this registration")
@click.option("--source-url", help="Original URL of the file")
@click.option("--notes", help="Additional notes")
def register(dataset, period, file_path, mode, actor, source_url, notes):
    """Register an archivo in the datalake."""
    if not Path(file_path).exists():
        click.echo(f"File not found: {file_path}", err=True)
        return

    ingestion_mode = IngestionMode.MANUAL if mode == "manual" else IngestionMode.AUTOMATED
    trigger_type = TriggerType.MANUAL_CLI

    service = IngestionService()
    result = service.register_archivo(
        dataset_key=dataset,
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
        click.echo("⚠️  Duplicate detected (SHA256 match with existing archivo)")
        click.echo(f"    Dataset: {dataset}")
        click.echo(f"    Period: {period}")
        return

    archivo = result.archivo
    click.echo("✅ Archivo registered successfully!")
    click.echo(f"    Dataset: {dataset}")
    click.echo(f"    Period: {period}")
    click.echo(f"    Hash: {archivo.hash_sha256}")
    click.echo(f"    Path: {archivo.storage_path}")


@cli.group()
def ingest():
    """Run ingestion flows."""
    pass


@cli.group()
def flows():
    """Manage Prefect flows."""
    pass


@ingest.command("run")
@click.option("--dataset", required=True, help="Dataset key (must have a manifest YAML)")
@click.option("--period", default=None, help="Period label override (e.g., 2026-01)")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Extract and resolve period_label, but skip DB writes and storage",
)
def ingest_run(dataset, period, dry_run):
    """Run ingestion for a dataset using its manifest."""
    try:
        result = run_ingestion(
            dataset_key=dataset,
            trigger_type=TriggerType.MANUAL_CLI.value,
            period_label=period,
            dry_run=dry_run,
        )
        for r in result["results"]:
            period_str = f" [{r.get('period_label', period)}]"
            if r["success"]:
                if r.get("dry_run"):
                    click.echo(f"🔍 Would ingest{period_str}: {r['file']}")
                elif r["is_duplicate"]:
                    click.echo(f"📋 Duplicate{period_str}: {r['file']}")
                else:
                    click.echo(f"✅ Ingested{period_str}: {r['file']}")
            else:
                click.echo(f"❌ Failed: {r['file']} - {r['error']}", err=True)
        if dry_run:
            click.echo("(dry-run: no files were written to storage or DB)")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def sources():
    """List configured product sources."""
    pass


@sources.command("list")
@click.option(
    "--type",
    "extractor_type",
    default=None,
    type=click.Choice(["http", "custom"], case_sensitive=False),
    help="Filter by extractor type",
)
def sources_list(extractor_type):
    """List product sources from configs/products/."""
    try:
        manifests = load_all_manifests()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return

    if extractor_type:
        manifests = [m for m in manifests if m.extractor.type == extractor_type]

    if not manifests:
        click.echo("No sources found.")
        return

    for m in manifests:
        schedule = "—"
        if m.schedule and m.schedule.enabled:
            schedule = f"{m.schedule.cron} ({m.schedule.timezone})"
        click.echo(f"• {m.dataset_key} [{m.extractor.type}]  {m.nombre}")
        click.echo(f"    schedule: {schedule}")
        if m.extractor.type == "http":
            click.echo(f"    url: {m.extractor.url}")


@flows.command("deploy")
def flows_deploy():
    """Deploy Prefect deployments for all product manifests."""
    from rawlake.flows.deploy import deploy_all

    try:
        count = deploy_all()
        click.echo(f"✅ Deployed {count} deployment(s)")
    except Exception as e:
        click.echo(f"Error deploying: {e}", err=True)


if __name__ == "__main__":
    cli()
