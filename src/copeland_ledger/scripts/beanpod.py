import datetime as dt
from pathlib import Path

import click
import pandas as pd

from copeland_ledger.amortization import (
    LoanDetail,
    amortization_table,
    output_beancount_amortization_table,
)
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


@click.command()
@click.option(
    "--config-path",
    type=click.Path(exists=True, path_type=Path),
    envvar="LEDGER_CONFIG",
    help="Ledger config file path.",
)
@click.option(
    "--show-table",
    type=bool,
    default=False,
    is_flag=True,
    help="Show the DataFrame as an amortization table in the console.",
)
@click.option(
    "--latest-payments",
    type=bool,
    default=False,
    is_flag=True,
    help="Show recent payments.",
)
@click.argument(
    "loan-name",
    type=str,
    default="mortgage",
)
def amortization(
    config_path: Path, loan_name: str, show_table: bool, latest_payments: bool
):
    """Print the amortization table for a loan, either as a table or Beancount transactions."""
    loan = LoanDetail.from_config_file(path=config_path, name=loan_name)
    table_df = amortization_table(loan=loan)
    if latest_payments:
        start = dt.date.today() - dt.timedelta(days=120)
        table_df = table_df[table_df["date"] > str(start)][:10]
    if show_table:
        with pd.option_context("display.max_rows", 250):
            click.echo(table_df)
            return
    output_beancount_amortization_table(df=table_df, loan=loan)


cli.add_command(preview)
cli.add_command(amortization)


if __name__ == "__main__":
    cli()
