import structlog
from ofxtools.models.bank import CCSTMTRS, STMTTRN
from ofxtools.models.invest import (
    BUYMF,
    INCOME,
    INVBUY,
    INVSTMTRS,
    INVTRAN,
    MFINFO,
    REINVEST,
    SECINFO,
    SELLMF,
    TRANSFER,
)
from ofxtools.models.ofx import OFX

from ..models import (
    InvestStatement,
    InvestTransaction,
    Security,
    Statement,
    StatementList,
    Transaction,
)

logger = structlog.getLogger(__name__)


def transform_ofx(ofx: OFX) -> StatementList:
    """Get a list of Statements from an OFX object."""
    if ofx.creditcardmsgsrsv1 or ofx.bankmsgsrsv1:
        # Credit card and bank statements
        return transform_statement_list(ofx=ofx)
    elif ofx.invstmtmsgsrsv1:
        return transform_invest_statement_list(ofx=ofx)
    else:
        breakpoint()
        raise NotImplementedError(f"{ofx} is not yet supported.")


# Bank and credit card statements


def transform_statement_list(ofx: OFX) -> StatementList:
    """Create a StatmentList from an OFX object."""
    statements = [
        transform_statement(ofx_statement=statement) for statement in ofx.statements
    ]
    return StatementList(statements=statements)


def transform_statement(ofx_statement: CCSTMTRS) -> Statement:
    """Create a Statement from an OFX statement."""
    transactions = [
        transform_transaction(ofx_transaction=ofx_transaction)
        for ofx_transaction in ofx_statement.transactions
    ]
    statement = Statement(
        currency=ofx_statement.curdef,
        acct_id=ofx_statement.account.acctid,
        transactions=transactions,
    )
    logger.debug("Loaded statement", statement=statement)
    return statement


def transform_transaction(ofx_transaction: STMTTRN) -> Transaction:
    """Create a Transaction from an OFX transaction."""
    return Transaction(
        fit_id=ofx_transaction.fitid,
        date_posted=ofx_transaction.dtposted,
        memo=ofx_transaction.name,
        amount=ofx_transaction.trnamt,
    )


# Investment statements


def transform_invest_securities(ofx: OFX) -> dict[int, Security]:
    """Parse OFX securities and return a map of IDs to Security objects."""
    securities: dict[int, Security] = {}
    ofx_securities: list[MFINFO | SECINFO] = ofx.securities
    for ofx_security in ofx_securities:
        security = Security(
            ticker=ofx_security.ticker,
            sec_id=ofx_security.secinfo.secid.uniqueid,
            date=ofx_security.dtasof,
            name=ofx_security.secname,
            type=(
                ofx_security.mftype
                if isinstance(ofx_security, MFINFO)
                else ofx_security.stocktype
            ),
            unit_price=ofx_security.unitprice,
        )
        securities[security.sec_id] = security
    logger.debug("Loaded securities", tickers=[s.ticker for s in securities.values()])
    return securities


def transform_invest_statement_list(ofx: OFX) -> StatementList:
    """Create a StatmentList from an OFX object."""

    securities = transform_invest_securities(ofx=ofx)
    statements = [
        transform_invest_statement(ofx_statement=statement, securities=securities)
        for statement in ofx.statements
    ]
    return StatementList(statements=statements)


def transform_invest_statement(
    ofx_statement: INVSTMTRS, securities: dict[int, Security]
) -> InvestStatement:
    transactions = [
        transform_invest_transaction(
            transaction=ofx_transaction,
            securities=securities,
        )
        for ofx_transaction in ofx_statement.transactions
    ]
    statement = InvestStatement(
        currency=ofx_statement.curdef,
        acct_id=ofx_statement.account.acctid,
        broker=ofx_statement.account.brokerid,
        date=ofx_statement.dtasof,
        securities=securities,
        transactions=transactions,
    )
    logger.debug("Transformed investment statement", statement=statement)
    return statement


def transform_invest_transaction(
    transaction: BUYMF | SELLMF | REINVEST, securities: dict[int, Security]
) -> InvestTransaction:
    """Create an InvestTransaction from an OFX transaction."""
    ticker = securities[int(transaction.secid.uniqueid)].ticker
    if isinstance(transaction, (INCOME, REINVEST, SELLMF, TRANSFER)):
        return transform_invtran(transaction=transaction, ticker=ticker)
    elif isinstance(transaction, BUYMF):
        return transform_invbuy(transaction=transaction, ticker=ticker)
    else:
        raise ValueError(f"Unsupported transaction type: {transaction}")


def transform_invtran(transaction: REINVEST, ticker: str) -> InvestTransaction:
    """Create an InvestTransaction from an INVTRAN transaction."""
    invtran: INVTRAN = transaction.invtran
    return InvestTransaction(
        fit_id=invtran.fitid,
        ticker=ticker,
        date_posted=invtran.dtsettle,
        memo=invtran.memo,
        units=transaction.units if hasattr(transaction, "units") else None,
        unit_price=transaction.unitprice if hasattr(transaction, "unitprice") else None,
        amount=transaction.total if hasattr(transaction, "total") else None,
    )


def transform_invbuy(transaction: BUYMF, ticker: str) -> InvestTransaction:
    """Create an InvestTransaction from an INVBUY transaction."""
    invbuy: INVBUY = transaction.invbuy
    return InvestTransaction(
        fit_id=invbuy.invtran.fitid,
        ticker=ticker,
        date_posted=invbuy.invtran.dtsettle,
        memo=invbuy.invtran.memo,
        units=invbuy.units,
        unit_price=invbuy.unitprice,
        amount=invbuy.total,
    )
