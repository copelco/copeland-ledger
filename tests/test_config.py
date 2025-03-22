import datetime as dt

import yaml

from copeland_ledger.config import Account, Config, Loan, PdfArchive


def test_account():
    config = yaml.safe_load(
        """
        bean_account: Assets:US:Amex:Checking
        org: Amex
        acctid_suffix: "1111"
        """
    )
    account = Account.model_validate(config)
    assert account.bean_account == "Assets:US:Amex:Checking"
    assert account.org == "Amex"
    assert account.acctid_suffix == "1111"


def test_account_with_pdf_archive():
    config = yaml.safe_load(
        """
        bean_account: Assets:US:Amex:Checking
        org: Amex
        acctid_suffix: "1111"
        pdf_archive:
            org: American Express
        """
    )
    account = Account.model_validate(config)
    assert account.bean_account == "Assets:US:Amex:Checking"
    assert account.org == "Amex"
    assert account.acctid_suffix == "1111"
    assert isinstance(account.pdf_archive, PdfArchive)
    assert account.pdf_archive.org == "American Express"


def test_config_with_multiple_accounts():
    config = yaml.safe_load(
        """
        accounts:
          - bean_account: Assets:US:Amex:Checking
            org: Amex
            acctid_suffix: "1111"
          - bean_account: Assets:US:Amex:Savings
            org: Amex
            acctid_suffix: "2222"
        """
    )
    ledger_config = Config.model_validate(config)
    assert len(ledger_config.accounts) == 2
    assert ledger_config.accounts[0].bean_account == "Assets:US:Amex:Checking"
    assert ledger_config.accounts[0].org == "Amex"
    assert ledger_config.accounts[0].acctid_suffix == "1111"
    assert ledger_config.accounts[1].bean_account == "Assets:US:Amex:Savings"
    assert ledger_config.accounts[1].org == "Amex"
    assert ledger_config.accounts[1].acctid_suffix == "2222"


def test_loan():
    config = yaml.safe_load(
        """
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
    loan = Loan.model_validate(config)
    assert loan.interest_rate == 0.05
    assert loan.years == 10
    assert loan.principal == 100000
    assert loan.monthly_payment == 1000
    assert loan.start_date == dt.date(2000, 1, 1)
    assert loan.account_bank == "Assets:Checking"
    assert loan.account_liability == "Liabilities:Mortgage"
    assert loan.account_interest_expense == "Expenses:Interest"
    assert loan.account_escrow == "Assets:Escrow"


def test_config_with_loans():
    config = yaml.safe_load(
        """
        accounts:
          - bean_account: Assets:US:Amex:Checking
            org: Amex
            acctid_suffix: "1111"
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
    ledger_config = Config.model_validate(config)
    assert len(ledger_config.accounts) == 1
    assert ledger_config.accounts[0].bean_account == "Assets:US:Amex:Checking"
    assert ledger_config.loans is not None
    mortgage = ledger_config.loans["mortgage"]
    assert mortgage.interest_rate == 0.05
    assert mortgage.years == 10
    assert mortgage.principal == 100000
    assert mortgage.monthly_payment == 1000
    assert mortgage.start_date == dt.date(2000, 1, 1)
    assert mortgage.account_bank == "Assets:Checking"
    assert mortgage.account_liability == "Liabilities:Mortgage"
    assert mortgage.account_interest_expense == "Expenses:Interest"
    assert mortgage.account_escrow == "Assets:Escrow"
