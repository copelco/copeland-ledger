from xml.etree import ElementTree as ET

import pytest

from copeland_ledger.qfx.extract import fix_ofx, ofx_content_contains_account_id_suffix


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


def test_fix_ofx_uppercases_trntype():
    xml = "<ROOT><STMTTRN><TRNTYPE>Credit</TRNTYPE><NAME>Test</NAME></STMTTRN></ROOT>"
    root = ET.fromstring(xml)
    fix_ofx(root)
    assert root.find(".//TRNTYPE").text == "CREDIT"


def test_fix_ofx_uppercases_severity():
    xml = "<ROOT><STATUS><SEVERITY>info</SEVERITY></STATUS></ROOT>"
    root = ET.fromstring(xml)
    fix_ofx(root)
    assert root.find(".//SEVERITY").text == "INFO"
