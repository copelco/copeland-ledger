from dataclasses import dataclass
from pathlib import Path

import click
import yaml
from beangulp import _archive, _extract, _identify, _importer

from copeland_ledger.config import Config
from copeland_ledger.importers.pdf_archive import PdfArchiver
from copeland_ledger.importers.qfx import QfxImporter


@dataclass
class IngestWrapper:
    importers: list
    hooks: list | None = None


@click.group()
@click.option(
    "--ledger-home",
    envvar="LEDGER_HOME",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Root directory for ledger files.",
)
@click.option(
    "--config",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Path to config YAML file. Defaults to <ledger-home>/accounts.yaml.",
)
@click.pass_context
def main(ctx: click.Context, ledger_home: Path, config: Path | None):
    """Import ledger data using beangulp."""
    if ledger_home is None:
        raise click.UsageError(
            "No value for --ledger-home. Set the LEDGER_HOME environment variable "
            "or pass --ledger-home PATH."
        )
    config = config or (ledger_home / "accounts.yaml")
    if not config.is_file():
        raise click.BadParameter(f"Config file not found: {config}", param_hint="'--config'")

    ledger_config = Config.model_validate(yaml.safe_load(config.read_text()))
    accounts = ledger_config.accounts
    raw_importers = [
        QfxImporter(
            bean_account=account.bean_account,
            org=account.org,
            acctid_suffix=account.acctid_suffix,
        )
        for account in accounts
    ] + [PdfArchiver(config=account) for account in accounts]
    importers = [_importer(i) for i in raw_importers]
    ctx.obj = IngestWrapper(importers=importers, hooks=[])

    # Inject dynamic default arguments for the native beangulp subcommands
    downloads = (str(ledger_home / "downloads"),)
    ctx.default_map = {
        "identify": {"src": downloads},
        "extract": {"src": downloads},
        "archive": {
            "src": downloads,
            "destination": str(ledger_home / "documents"),
        },
    }


main.add_command(_identify, name="identify")
main.add_command(_extract, name="extract")
main.add_command(_archive, name="archive")


if __name__ == "__main__":
    main()
