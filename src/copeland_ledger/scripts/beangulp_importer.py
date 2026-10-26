import os
from dataclasses import dataclass
from pathlib import Path

import beangulp
import click
import yaml

from copeland_ledger.config import Config
from copeland_ledger.importers.pdf_archive import PdfArchiver
from copeland_ledger.importers.qfx import QfxImporter


@dataclass
class IngestWrapper:
    importers: list
    hooks: list | None = None


def ledger_home() -> Path:
    """Return the $LEDGER_HOME directory or fail with a clear message."""
    home = os.environ.get("LEDGER_HOME")
    if not home:
        raise click.ClickException("LEDGER_HOME environment variable is not set")
    return Path(os.path.expanduser(home))


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to config YAML file with account mappings. Defaults to $LEDGER_HOME/accounts.yaml.",
)
@click.pass_context
def main(ctx, config):
    """Import ledger data using beangulp."""
    if config is None:
        config = str(ledger_home() / "accounts.yaml")
        if not Path(config).is_file():
            raise click.ClickException(f"Config file not found: {config}")
    config_path = Path(config)
    ledger_config = Config.model_validate(yaml.safe_load(config_path.read_text()))
    accounts = ledger_config.accounts
    importers = [
        QfxImporter(
            bean_account=account.bean_account,
            org=account.org,
            acctid_suffix=account.acctid_suffix,
        )
        for account in accounts
    ] + [PdfArchiver(config=account) for account in accounts]
    ctx.obj = IngestWrapper(
        importers=[beangulp._importer(i) for i in importers],
        hooks=[],
    )


@click.command()
@click.argument("src", nargs=-1, type=click.Path(exists=True, resolve_path=True))
@click.option("--failfast", "-x", is_flag=True, help="Stop after the first error.")
@click.option("--verbose", "-v", is_flag=True)
def identify(src, failfast, verbose):
    """Identify bank-statement files in $LEDGER_HOME/downloads."""
    beangulp._identify.callback(src or (str(ledger_home() / "downloads"),), failfast, verbose)


@click.command()
@click.argument("src", nargs=-1, type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--output",
    "-o",
    type=click.File("w"),
    default="-",
    show_default=True,
    help="Write extracted entries to this file.",
)
@click.option("--existing", "-e", type=click.Path(exists=True), help="File with existing entries.")
@click.option("--reverse", "-r", is_flag=True, help="Print transactions in reverse order.")
@click.option("--failfast", "-x", is_flag=True, help="Stop after the first error.")
@click.option("--quiet", "-q", count=True, help="Silence output.")
def extract(src, output, existing, reverse, failfast, quiet):
    """Extract transactions from files in $LEDGER_HOME/downloads."""
    beangulp._extract.callback(
        src or (str(ledger_home() / "downloads"),),
        output,
        existing,
        reverse,
        failfast,
        quiet,
    )


@click.command()
@click.argument("src", nargs=-1, type=click.Path(exists=True, resolve_path=True))
@click.option(
    "--destination",
    "-o",
    metavar="DIR",
    default=None,
    help="Destination directory. Defaults to $LEDGER_HOME/documents.",
)
@click.option("--overwrite", "-f", is_flag=True, help="Overwrite existing files.")
@click.option("--dry-run", "-n", is_flag=True, help="Show what would be done.")
@click.option("--failfast", "-x", is_flag=True, help="Stop after the first error.")
@click.option("--quiet", "-q", count=True, help="Silence output.")
def archive(src, destination, overwrite, dry_run, failfast, quiet):
    """Archive imported files from $LEDGER_HOME/downloads into $LEDGER_HOME/documents."""
    if destination is None:
        destination = str(ledger_home() / "documents")
    beangulp._archive.callback(
        src or (str(ledger_home() / "downloads"),),
        destination,
        dry_run,
        overwrite,
        failfast,
        quiet,
    )


main.add_command(identify)
main.add_command(extract)
main.add_command(archive)


if __name__ == "__main__":
    main()
