import datetime as dt
from decimal import Decimal

from copeland_ledger.importers.qfx import build_bean_invest_transactions
from copeland_ledger.models import InvestTransaction, InvestType

BEAN_ACCOUNT = "Assets:US:Vanguard:Brokerage"
CASH = "USD"


def make_dividend_transaction() -> InvestTransaction:
    """A synthetic DRIP dividend: $210.00 of VUSFX reinvested at $21.00/share."""
    return InvestTransaction(
        fit_id="VG-1",
        date_posted=dt.datetime(2025, 12, 31),
        memo="DIVIDEND REINVESTMENT",
        amount=Decimal("210.00"),
        currency=CASH,
        ticker="VUSFX",
        type=InvestType.DIVIDEND,
        units=Decimal("10.00"),
        unit_price=Decimal("21.00"),
    )


def test_dividend_income_posting_credits_income():
    entries = build_bean_invest_transactions(make_dividend_transaction(), BEAN_ACCOUNT)
    income_entry = next(e for e in entries if e.payee == "Dividend Income")
    income_posting = next(p for p in income_entry.postings if p.account.startswith("Income"))
    # Income is a credit: the amount must be negative so the cash leg is positive.
    assert income_posting.units.number == Decimal("-210.00")


def test_dividend_income_posting_with_negative_source_amount():
    # Older Vanguard QFX files emit a negative TOTAL for dividends.
    txn = make_dividend_transaction()
    txn = txn.model_copy(update={"amount": Decimal("-200.00")})
    entries = build_bean_invest_transactions(txn, BEAN_ACCOUNT)
    income_entry = next(e for e in entries if e.payee == "Dividend Income")
    income_posting = next(p for p in income_entry.postings if p.account.startswith("Income"))
    # Income credit is the same sign regardless of the source sign convention.
    assert income_posting.units.number == Decimal("-200.00")


def make_cash_dividend_transaction() -> InvestTransaction:
    """A synthetic Vanguard cash dividend (VSMAX): $75.00 cash, no shares."""
    return InvestTransaction(
        fit_id="VG-99",
        date_posted=dt.datetime(2026, 1, 31),
        memo="DIVIDEND PAYMENT",
        amount=Decimal("75.0"),
        currency=CASH,
        ticker="VSMAX",
        type=InvestType.DIVIDEND,
        units=None,
        unit_price=None,
    )


def test_cash_dividend_posts_income_and_cash():
    entries = build_bean_invest_transactions(make_cash_dividend_transaction(), BEAN_ACCOUNT)
    # A single balanced transaction: income credited, cash deposited.
    assert len(entries) == 1
    postings = entries[0].postings
    income_posting = next(p for p in postings if p.account.startswith("Income"))
    cash_posting = next(p for p in postings if p.account.endswith(":Cash"))
    assert income_posting.units.number == Decimal("-75.0")
    assert cash_posting.units.number == Decimal("75.0")


def test_dividend_drip_cash_leg_net_zero():
    entries = build_bean_invest_transactions(make_dividend_transaction(), BEAN_ACCOUNT)
    drip_entry = next(e for e in entries if e.payee != "Dividend Income")
    income_entry = next(e for e in entries if e.payee == "Dividend Income")

    # Each entry is two-leg: shares (or income) against an unfilled cash leg,
    # which beancount infers as the negative of the filled leg.
    shares_posting = next(p for p in drip_entry.postings if p.units is not None)
    drip_cash = -(shares_posting.units.number * shares_posting.cost.number)
    income_posting = next(p for p in income_entry.postings if p.account.startswith("Income"))
    income_cash = -income_posting.units.number

    # The DRIP spends exactly the dividend it was paid, within pricing rounding.
    assert abs(drip_cash + income_cash) < Decimal("0.01")
