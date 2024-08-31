"""CLI for Sigalas Calendar Translator - Sigalas Calendar Translator.

Copyright (C) 2024  Parker Wahle

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""  # noqa: E501, B950

from __future__ import annotations

import json

import typer
import uvicorn
from rich.progress import Progress

from .api import app
from .scraping import get_month_data
from ._assets import RESOURCES


cli = typer.Typer()


@cli.command()
def serve() -> None:
    typer.echo("Starting server at http://0.0.0.0:8080")
    typer.echo("Press Ctrl+C to stop the server.")
    uvicorn.run(app, host="0.0.0.0", port=8080)


@cli.command()
def once() -> None:
    with Progress() as progress:
        # add an endless task
        task_id = progress.add_task("Downloading", total=0)
        month_data = get_month_data()
        for i, period in enumerate(month_data):
            with open(f"{i+1}_calendar.ics", "w") as f:
                f.writelines(period.serialize_iter())
        progress.update(task_id, advance=1)
    typer.echo("Done! Check your CWD.")


if __name__ == "__main__":  # pragma: no cover
    cli()

__all__ = ("cli",)
