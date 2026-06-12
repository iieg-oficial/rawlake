import typer

app = typer.Typer(name="rawlake", help="RawLake data lake CLI")


@app.command()
def version():
    typer.echo("rawlake 0.1.0")


if __name__ == "__main__":
    app()
