from dataclasses import dataclass

import beangulp
import click
import yaml
from pathlib import Path

from copeland_ledger.importers.qfx import QfxImporter
from copeland_ledger.importers.pdf_archive import PdfArchiver


@dataclass
class IngestWrapper:
    importers: list
    hooks: list | None = None


@click.group("beangulp")
def beangulp_group():
    pass


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to config YAML file with account mappings.",
)
@click.pass_context
def main(ctx, config):
    config_path = Path(config)
    with config_path.open("r") as file:
        data = yaml.safe_load(file)
    accounts = data["accounts"]
    importers = [
        QfxImporter(
            bean_account=account["bean_account"],
            org=account["org"],
            acctid_suffix=account["acctid_suffix"],
        )
        for account in accounts
    ] + [
        PdfArchiver(
            bean_account=account["bean_account"],
            org=account["org"],
            acctid_suffix=account["acctid_suffix"],
        )
        for account in accounts
    ]
    ctx.obj = IngestWrapper(
        importers=[beangulp._importer(i) for i in importers],
        hooks=[],
    )


main.add_command(beangulp_group)
beangulp_group.add_command(beangulp._archive)
beangulp_group.add_command(beangulp._extract)
beangulp_group.add_command(beangulp._identify)


if __name__ == "__main__":
    main()
