import datetime as dt
from pathlib import Path
from decimal import Decimal

import numpy_financial as npf
import pandas as pd
import yaml
from beancount.core import amount, data, flags
from beancount.parser import printer
from pydantic import BaseModel, field_validator


class LoanDetail(BaseModel):
    """Loan details, including beanount accounts."""

    # Annual interest rate
    interest_rate: float
    # Loan term in years
    years: int
    # Number of payments per year
    payments_year: int = 12
    # Initial loan amount
    principal: float
    # Additional principal payment
    addl_principal: float = 0.0
    # Start date of the loan
    start_date: dt.date
    # Monthly payment including escrow
    monthly_payment: float
    # Loan currency
    currency: str = "USD"
    # Beancount accounts
    account_bank: str
    account_liability: str
    account_interest_expense: str
    account_escrow: str

    @classmethod
    def from_config_file(cls, path: Path, name: str) -> "LoanDetail":
        """Create a Loan object from a YAML config file."""
        config = yaml.safe_load(path.read_text())
        loan = config["loans"][name]
        return cls.model_validate(loan)

    @field_validator("monthly_payment", "addl_principal")
    @classmethod
    def ensure_negative(cls, value: float) -> float:
        """Ensure that the monthly payment and additional principal are negative."""
        return -value if value > 0 else value


def amortization_table(loan: LoanDetail) -> pd.DataFrame:
    """
    Calculate the amortization schedule given the loan details.

    Based on:
    https://github.com/chris1610/pbpython/blob/master/notebooks/Amortization-Model-Article.ipynb
    """
    # Create an index of the payment dates
    rng = pd.date_range(
        name="date",
        start=loan.start_date,
        periods=loan.years * loan.payments_year,
        freq="MS",
    )

    # Build up the Amortization schedule as a DataFrame
    df = pd.DataFrame(
        index=rng,
        columns=[
            "payment",
            "principal",
            "interest",
            "principal_addl",
            "monthly_payment",
            "curr_balance",
            "principal_cum",
            "currency",
        ],
        dtype="float",
    )

    # Add index by period (start at 1 not 0)
    df.reset_index(inplace=True)
    df.index += 1
    df.index.name = "period"

    df["currency"] = loan.currency
    df["monthly_payment"] = loan.monthly_payment

    # Calculate the payment, principal and interests amounts using built in
    # Numpy functions
    per_payment = npf.pmt(
        loan.interest_rate / loan.payments_year,
        loan.years * loan.payments_year,
        loan.principal,
    )
    df["payment"] = per_payment
    df["principal"] = npf.ppmt(
        loan.interest_rate / loan.payments_year,
        df.index,
        loan.years * loan.payments_year,
        loan.principal,
    )
    df["interest"] = npf.ipmt(
        loan.interest_rate / loan.payments_year,
        df.index,
        loan.years * loan.payments_year,
        loan.principal,
    )
    df["principal_addl"] = loan.addl_principal

    # Store the Cumulative Principal Payments and ensure it never gets larger
    # than the original principal
    df["principal_cum"] = (df["principal"] + df["principal_addl"]).cumsum()
    df["principal_cum"] = df["principal_cum"].clip(lower=float(-loan.principal))
    # Calculate the current balance for each period
    df["curr_balance"] = loan.principal + df["principal_cum"]

    # Round the values
    df = df.round(2)

    return df


def output_beancount_amortization_table(df: pd.DataFrame, loan: LoanDetail):
    """Output the amortization table as Beancount transactions."""
    entries = []
    for row in df.itertuples():
        payment_amount = round(Decimal(row.monthly_payment), 2)
        principle_amount = abs(round(Decimal(row.principal), 2))
        interest_amount = abs(round(Decimal(row.interest), 2))
        currency: str = row.currency

        payment = data.Posting(
            account=loan.account_bank,
            units=amount.Amount(number=payment_amount, currency=currency),
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )
        principle = data.Posting(
            account=loan.account_liability,
            units=amount.Amount(number=principle_amount, currency=currency),
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )
        interest = data.Posting(
            account=loan.account_interest_expense,
            units=amount.Amount(number=interest_amount, currency=currency),
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )
        escrow = data.Posting(
            account=loan.account_escrow,
            units=None,
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )
        fileloc = data.new_metadata("<build_transaction>", 0)
        transaction = data.Transaction(
            meta=fileloc,
            date=row.date.date(),
            flag=flags.FLAG_OKAY,
            payee=None,
            narration="Mortgage payment",
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=[payment, principle, interest, escrow],
        )
        entries.append(transaction)
    printer.print_entries(entries)
