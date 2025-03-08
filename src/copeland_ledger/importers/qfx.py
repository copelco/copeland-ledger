import datetime as dt

from pathlib import Path

import beangulp
import structlog
from beancount.core import amount, data, flags
from beangulp import mimetypes

from copeland_ledger.models import StatementType, TransactionType, InvestTransaction
from copeland_ledger.qfx.extract import ofx_content_contains_account_id_suffix
from copeland_ledger.qfx.load import load_statement

logger = structlog.get_logger(__file__)

VALID_MIMETYPES = {
    "application/x-ofx",
    "application/vnd.intu.qbo",
    "application/vnd.intu.qfx",
}


def build_bean_invest_transaction(
    transaction: TransactionType, bean_account: str
) -> data.Transaction:
    """Build a beancount transaction from an OFX Investment Transaction."""

    # if transaction.date_posted.date() == dt.date(2024, 11, 14):
    #     breakpoint()
    account = f"{bean_account}:{transaction.ticker}"
    cost = data.Cost(
        number=transaction.unit_price,
        currency=transaction.currency,
        date=None,
        label=None,
    )
    # price = amount.Amount(number=transaction.unit_price, currency=transaction.currency)
    units = amount.Amount(number=transaction.units, currency=transaction.ticker)
    posting = data.Posting(
        account=account,
        units=units,
        cost=cost,
        price=None,
        flag=None,
        meta={"type": transaction.type, "amount": transaction.amount},
    )
    # Build the transaction with a single leg.
    fileloc = data.new_metadata("<build_transaction>", 0)
    return data.Transaction(
        meta=fileloc,
        date=transaction.date_posted.date(),
        flag=flags.FLAG_OKAY,
        payee=None,
        narration=transaction.memo,
        tags=data.EMPTY_SET,
        links=data.EMPTY_SET,
        postings=[posting],
    )


class QfxImporter(beangulp.Importer):
    """A beangulp importer for QFX files."""

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
        self.statement: StatementType | None = None

    def account(self, filepath):
        """Return the account against which we post transactions."""
        return self.bean_account

    def date(self, filepath: str) -> dt.date | None:
        """Return the date of the last transaction of the statement."""
        if self.statement:
            return self.statement.transactions[-1].date_posted.date()

    def filename(self, filepath: str) -> str:
        """Return the archival filename for the given file."""
        path = Path(filepath)
        return f"{self.org}_{self.acctid_suffix}{path.suffix}"

    def identify(self, filepath: str):
        """Return True if this importer matches a QFX file."""

        # Match for a compatible MIME type.
        mimetype, _ = mimetypes.guess_type(filepath, strict=False)
        if mimetype not in VALID_MIMETYPES:
            return False

        content = Path(filepath).read_text()
        if ofx_content_contains_account_id_suffix(
            ofx_content=content, account_id_suffix=self.acctid_suffix
        ):
            self.statement = load_statement(
                path=filepath, acctid_suffix=self.acctid_suffix
            )
            logger.info(
                "Identified QFX file",
                filename=Path(filepath).name,
                acctid_suffix=self.acctid_suffix,
                ofx_org=self.org,
            )
            return True

    def build_bean_transaction(self, transaction: TransactionType) -> data.Transaction:
        """Build a beancount transaction from an OFX Transaction."""

        if isinstance(transaction, InvestTransaction):
            return build_bean_invest_transaction(
                transaction=transaction, bean_account=self.bean_account
            )

        # Create a single posting for it; the user will have to manually
        # categorize the other side.
        units = amount.Amount(number=transaction.amount, currency=transaction.currency)
        posting = data.Posting(
            account=self.bean_account,
            units=units,
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )
        # Build the transaction with a single leg.
        fileloc = data.new_metadata("<build_transaction>", 0)
        return data.Transaction(
            meta=fileloc,
            date=transaction.date_posted.date(),
            flag=flags.FLAG_OKAY,
            payee=None,
            narration=transaction.memo,
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=[posting],
        )

    def extract(self, filepath: str, existing: data.Directive) -> data.Directives:
        """Extract a list of partially complete transactions from the file."""
        logger.debug("Extracting transactions", filepath=filepath)

        stmt_entries = []
        transactions = self.statement.transactions if self.statement else []
        for i, transaction in enumerate(transactions):
            entry = self.build_bean_transaction(transaction)
            entry = entry._replace(meta=data.new_metadata(filename=filepath, lineno=i))
            stmt_entries.append(entry)

        return data.sorted(stmt_entries)
