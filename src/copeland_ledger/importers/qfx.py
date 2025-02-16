import itertools
import datetime as dt
import warnings
from decimal import Decimal
from pathlib import Path
from typing import Generator
from xml.etree import ElementTree as ET

import beangulp
import structlog
from beangulp import mimetypes
from beancount.core import amount, data, flags
from ofxtools.models.bank import CCSTMTRS, STMTRS
from ofxtools.models.invest import INVSTMTRS
from ofxtools.models.ofx import OFX
from ofxtools.Parser import OFXTree
from ofxtools.Types import OFXTypeError, OFXTypeWarning
from pydantic import BaseModel

from copeland_ledger.qfx.load import load_statement

logger = structlog.get_logger(__file__)
warnings.filterwarnings("ignore", category=OFXTypeWarning)

parser = OFXTree()
VALID_MIMETYPES = {
    "application/x-ofx",
    "application/vnd.intu.qbo",
    "application/vnd.intu.qfx",
}


class Transaction(BaseModel):
    """Open Financial Exchange (OFX) transaction"""

    org: str
    bankid: int | None
    acctid: str
    accttype: str
    trntype: str
    dtposted: dt.datetime
    dtuser: dt.datetime | None
    dtavail: dt.datetime | None
    trnamt: Decimal
    curdef: str = None
    ledgerbal: Decimal | None
    ledgerbal_dtasof: dt.datetime | None
    # Financial Institution Transaction ID
    fitid: str
    refnum: str | None
    name: str | None
    memo: str | None

    class Config:
        # Allow any attribute to be set
        from_attributes = True


class QfxImporter(beangulp.Importer):
    def __init__(self, org: str, acctid_suffix: str, bean_account: str):
        self.bean_account = bean_account
        self.org = org
        self.acctid_suffix = acctid_suffix
        logger.debug(
            "Initialized QfxImporter",
            bean_account=bean_account,
            org=org,
            acctid_suffix=acctid_suffix,
        )
        self.ofx: OFX | None = None
        self.statement: CCSTMTRS | STMTRS | None = None

    def account(self, filepath):
        """Return the account against which we post transactions."""
        return self.bean_account

    def identify(self, filepath: str):
        """Return True if this importer matches a QFX file."""

        # Match for a compatible MIME type.
        mimetype, _ = mimetypes.guess_type(filepath, strict=False)
        if mimetype not in VALID_MIMETYPES:
            return False

        statement = load_statement(path=filepath, acctid_suffix=self.acctid_suffix)
        if statement is not None:
            logger.info(
                "Identified QFX file",
                filename=Path(filepath).name,
                acctid_suffix=self.acctid_suffix,
                ofx_org=self.org,
            )
            return True

    def get_statement_info(self, ofx: OFX, statement: CCSTMTRS | STMTRS) -> dict:
        """Get bank/credit card account information from an OFX statement."""
        bankid = statement.account.bankid if isinstance(statement, STMTRS) else None
        if isinstance(statement, CCSTMTRS):
            # Not set in credit card statements, so we'll just use "CREDITCARD"
            accttype = "CREDITCARD"
        elif isinstance(statement, STMTRS):
            accttype = statement.account.accttype
        elif isinstance(statement, INVSTMTRS):
            accttype = "INVEST"
            breakpoint()

        return {
            "org": self.org,
            "bankid": bankid,
            "acctid": statement.account.acctid[-4:],  # Last 4 digits only
            "accttype": accttype,
            "ledgerbal": statement.ledgerbal.balamt,
            "ledgerbal_dtasof": statement.ledgerbal.dtasof.date(),
        }

    def get_transactions(self) -> Generator[Transaction, None, None]:
        statement_info = self.get_statement_info(self.ofx, self.statement)
        logger.debug("Extracting transactions", **statement_info)
        for transaction in self.statement.transactions:
            data = statement_info.copy()
            data.update(
                {
                    "trntype": transaction.trntype,
                    "dtposted": transaction.dtposted,
                    "dtuser": transaction.dtuser,
                    "dtavail": transaction.dtavail,
                    "trnamt": transaction.trnamt,
                    "fitid": transaction.fitid,
                    "refnum": transaction.refnum,
                    "name": transaction.name,
                    "memo": transaction.memo,
                    "curdef": self.statement.curdef,
                }
            )
            yield Transaction(**data)

    def build_transaction(self, transaction: Transaction) -> data.Transaction:
        """Build a beancount transaction from an OFX Transaction."""

        # Create a single posting for it; the user will have to manually
        # categorize the other side.
        units = amount.Amount(number=transaction.trnamt, currency=transaction.curdef)
        posting = data.Posting(
            account=self.bean_account,
            units=units,
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )
        narration = " / ".join(
            filter(None, [transaction.name, transaction.memo, transaction.trntype])
        )
        # Build the transaction with a single leg.
        fileloc = data.new_metadata("<build_transaction>", 0)
        return data.Transaction(
            meta=fileloc,
            date=transaction.dtposted.date(),
            flag=flags.FLAG_OKAY,
            payee=None,
            narration=narration,
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=[posting],
        )

    def extract(self, filepath, existing):
        """Extract a list of partially complete transactions from the file."""
        logger.debug("Extracting transactions", filepath=filepath)
        # Create Transaction directives.
        new_entries = []
        counter = itertools.count()

        stmt_entries = []
        transactions = list(self.get_transactions())
        for transaction in transactions:
            entry = self.build_transaction(transaction)
            entry = entry._replace(
                meta=data.new_metadata(filename=filepath, lineno=next(counter))
            )
            stmt_entries.append(entry)
        stmt_entries = data.sorted(stmt_entries)
        new_entries.extend(stmt_entries)

        transaction = transactions[0]
        if transaction.ledgerbal:
            date = transaction.ledgerbal_dtasof.date()
            # The Balance assertion occurs at the beginning of the date, so
            # move it to the following day.
            date += dt.timedelta(days=1)

            meta = data.new_metadata(filepath, next(counter))
            balance_entry = data.Balance(
                meta=meta,
                date=date,
                account=self.bean_account,
                amount=amount.Amount(
                    number=transaction.ledgerbal, currency=transaction.curdef
                ),
                tolerance=None,
                diff_amount=None,
            )
            new_entries.append(balance_entry)

        return data.sorted(new_entries)
