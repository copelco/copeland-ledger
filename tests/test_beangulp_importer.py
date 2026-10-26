from click.testing import CliRunner

from copeland_ledger.scripts.beangulp_importer import main


def make_ledger_home(tmp_path):
    (tmp_path / "downloads").mkdir()
    (tmp_path / "documents").mkdir()
    (tmp_path / "accounts.yaml").write_text(
        """
accounts:
  - bean_account: Assets:US:Amex:Checking
    org: Amex
    acctid_suffix: "1111"
"""
    )
    return tmp_path


def test_no_argument_commands_use_ledger_home(tmp_path, monkeypatch):
    home = make_ledger_home(tmp_path)
    monkeypatch.setenv("LEDGER_HOME", str(home))
    runner = CliRunner()
    for command in ("identify", "extract", "archive"):
        result = runner.invoke(main, [command])
        assert result.exit_code == 0, (command, result.output, result.exception)


def test_missing_ledger_home_fails_cleanly(tmp_path, monkeypatch):
    monkeypatch.delenv("LEDGER_HOME", raising=False)
    result = CliRunner().invoke(main, ["identify"])
    assert result.exit_code != 0
    assert "LEDGER_HOME" in result.output
