import datetime as dt
from decimal import Decimal
from enum import StrEnum

import pandas as pd
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Simple representation of a transaction."""

    # Financial Institution Transaction ID
    fit_id: str
    date_posted: dt.datetime
    memo: str
    amount: Decimal
    currency: str


class Statement(BaseModel):
    """Simple representation of a statement."""

    acct_id: str
    currency: str
    transactions: list[Transaction] = Field(repr=False)

    def as_dataframe(self) -> pd.DataFrame:
        """Return the statement as a pandas DataFrame."""
        return pd.DataFrame.from_records([trans.model_dump() for trans in self.transactions])


class StatementList(BaseModel):
    """Simple representation of a list of statements."""

    statements: "list[Statement | InvestStatement]"

    def get_by_acctid_suffix(self, suffix: str) -> Statement | None:
        """Get a Statement by account ID suffix."""
        for statement in self.statements:
            if str(statement.acct_id).endswith(suffix):
                return statement


class Security(BaseModel):
    """Simple representation of a security."""

    ticker: str
    sec_id: int
    name: str
    type: str
    unit_price: Decimal
    date: dt.datetime


class InvestType(StrEnum):
    """Type of investment transaction."""

    BUY = "BUY"
    DIVIDEND = "DIV"
    INTEREST = "INT"
    MISC = "MISC"
    SELL = "SELL"
    TRANSFER = "TRANS"


class InvestTransaction(Transaction):
    """Simple representation of an investment transaction."""

    ticker: str
    type: InvestType
    units: Decimal
    unit_price: Decimal | None = None


class InvestStatement(Statement):
    """Simple representation of an investment statement."""

    date: dt.datetime
    broker: str
    securities: dict[int, Security] = Field(repr=False)
    transactions: list[InvestTransaction] = Field(repr=False)


StatementType = Statement | InvestStatement
TransactionType = Transaction | InvestTransaction
