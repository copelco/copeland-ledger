import datetime as dt

from pydantic import BaseModel


class PdfArchive(BaseModel):
    """Config to archive PDFs for a given account"""

    org: str


class Account(BaseModel):
    """
    Config for an account to import transactions from.

    Sample account YAML:
        bean_account: Assets:US:Amex:Checking
        org: Amex
        acctid_suffix: "1111"
        pdf_archive:
            org: American Express
    """

    bean_account: str
    org: str
    acctid_suffix: str
    pdf_archive: PdfArchive | None = None


class Loan(BaseModel):
    """Config for a loan."""

    interest_rate: float
    years: int
    principal: float
    monthly_payment: float
    start_date: dt.date
    account_bank: str
    account_liability: str
    account_interest_expense: str
    account_escrow: str


class Config(BaseModel):
    """Config for the ledger."""

    accounts: list[Account]
    loans: dict[str, Loan] | None = None
