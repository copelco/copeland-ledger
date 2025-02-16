import click
from pathlib import Path

from copeland_ledger.qfx.load import load


@click.group()
def cli():
    pass


@click.command()
@click.option(
    "--home",
    type=click.Path(exists=True),
    envvar="LEDGER_HOME",
    help="Ledger home directory.",
)
@click.argument("filename")
def preview(home, filename):
    "Hello"
    path = Path(home) / "downloads" / filename
    statement_list = load(path=path)
    for statement in statement_list.statements:
        print(statement.as_dataframe())


cli.add_command(preview)


if __name__ == "__main__":
    cli()
