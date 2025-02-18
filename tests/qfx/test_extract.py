import pytest

from copeland_ledger.qfx.extract import ofx_content_contains_account_id_suffix


@pytest.mark.parametrize(
    "content, suffix",
    [
        ("ACCTID>123456", "123456"),
        ("<ACCTID>ABCDEFG|01234</ACCTID>", "01234"),
        ("<ACCTID>ABCDEFG-01234</ACCTID>", "01234"),
    ],
)
def test_me(content, suffix):
    assert ofx_content_contains_account_id_suffix(content, suffix) is True
