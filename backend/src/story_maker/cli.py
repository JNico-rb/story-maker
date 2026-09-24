"""CLI `story-maker`; cada spec añade sus comandos."""

from importlib.metadata import version
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(version("story-maker"))
        raise typer.Exit


@app.callback()
def main(
    _version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_print_version, is_eager=True, help="Muestra la versión."
        ),
    ] = False,
) -> None:
    """Novelas personalizadas de regalo."""
