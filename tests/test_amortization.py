import datetime as dt

from copeland_ledger.amortization import (
    LoanDetail,
    amortization_table,
)


def test_loan_detail_from_config_file(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
        loans:
          mortgage:
            interest_rate: 0.05
            years: 10
            principal: 100000
            monthly_payment: 1000
            start_date: 2000-01-01
            account_bank: Assets:Checking
            account_liability: Liabilities:Mortgage
            account_interest_expense: Expenses:Interest
            account_escrow: Assets:Escrow
        """
    )
    loan = LoanDetail.from_config_file(path=config_path, name="mortgage")
    assert loan.interest_rate == 0.05
    assert loan.years == 10
    assert loan.principal == 100000
    assert loan.monthly_payment == -1000
    assert loan.start_date == dt.date(2000, 1, 1)
    assert loan.account_bank == "Assets:Checking"
    assert loan.account_liability == "Liabilities:Mortgage"
    assert loan.account_interest_expense == "Expenses:Interest"
    assert loan.account_escrow == "Assets:Escrow"


def test_amortization_table():
    loan = LoanDetail(
        interest_rate=0.05,
        years=1,
        principal=10000,
        monthly_payment=-856.07,
        start_date=dt.date(2000, 1, 1),
        account_bank="Assets:Checking",
        account_liability="Liabilities:Mortgage",
        account_interest_expense="Expenses:Interest",
        account_escrow="Assets:Escrow",
    )
    df = amortization_table(loan)
    assert df.shape == (12, 9)
    assert df["payment"].sum() == -10272.84
    assert df["principal"].sum() == -10000.0
    assert df["interest"].sum() == -272.89
    assert df["principal_addl"].sum() == 0
    assert df["monthly_payment"].sum() == -10272.84
    assert df.iloc[-1]["curr_balance"] == 0
