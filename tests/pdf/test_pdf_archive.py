from pathlib import Path

import pytest

from copeland_ledger.importers.pdf_archive import (
    extract_pdf_text,
    find_account_id_suffix_in_pdf,
    find_org_name_in_pdf,
)


@pytest.mark.parametrize(
    "acctid_suffix, content",
    [
        ("1234", "Account Number:  XXXX XXXX XXXX 1234"),
        ("1234", "0075531234 Other Text"),
    ],
)
def test_find_account_id_suffix_in_pdf(acctid_suffix, content):
    assert find_account_id_suffix_in_pdf(acctid_suffix, content) is True


@pytest.mark.parametrize(
    "org, content",
    [
        ("Chase", "please write to us at Chase Card Services"),
        ("Chase", "Chase Ultimate Rewards® at www.UltimateRewards.com"),
    ],
)
def test_find_org_name_in_pdf(org, content):
    assert find_org_name_in_pdf(org, content) is True


def test_extract_pdf_text():
    path = Path(__file__).parent / "test.pdf"
    assert "This is a test PDF document" in extract_pdf_text(path)
