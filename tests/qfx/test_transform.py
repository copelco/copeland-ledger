from unittest.mock import MagicMock

from copeland_ledger.qfx.transform import transform_invest_statement


def test_transform_invest_statement_none_transactions():
    """transform_invest_statement should not raise when transactions is None."""
    ofx_statement = MagicMock()
    ofx_statement.transactions = None
    ofx_statement.curdef = "USD"
    ofx_statement.account.acctid = "12345"
    ofx_statement.account.brokerid = "broker"
    ofx_statement.dtasof = None

    result = transform_invest_statement(ofx_statement=ofx_statement, securities={})
    assert result.transactions == []
