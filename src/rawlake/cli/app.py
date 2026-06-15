from __future__ import annotations

import click


@click.group()
def cli():
    """RawLake data lake CLI."""
    pass


@cli.command()
def version():
    """Show rawlake version."""
    click.echo("rawlake 0.1.0")


if __name__ == "__main__":
    cli()