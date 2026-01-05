# copeland-ledger

My tools for tracking expenses using beancount: Double-Entry Accounting from
Text Files. This project uses the following packages:

- [Beancount](https://beancount.github.io/) (3.0): Double-Entry Accounting from Text Files
- [Beangulp](https://github.com/beancount/beangulp): Importers framework for Beancount
- [ofxtools](https://github.com/csingley/ofxtools): Python library for working with OFX files
- [Fava](https://beancount.github.io/fava/): Web interface for Beancount

## Setup

1. Configure your Python environment:

   ```shell
   # example .envrc file if you use direnv
   layout python python3.12

   export $LEDGER_HOME=~/path/to/your/ledger/directory
   ```

2. Install [uv](https://docs.astral.sh/uv/) if you haven't already:

   ```shell
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Install the required dependencies using `uv`:

   ```shell
   uv sync --all-extras
   ```

4. Create a configuration file for your accounts.

   ```yaml
   # example $LEDGER_HOME/accounts.yaml
   accounts:
     - bean_account: Assets:US:Ally:Checking
       org: Ally
       acctid_suffix: "1111"
   ```

5. Import data using the instructions below.

6. Run fava!

   ```shell
   uv run fava $LEDGER_HOME/ledger.beancount
   ```

## Import data

Download files manually to `$LEDGER_HOME/downloads` and verify the data:

```shell
uv run beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp identify $LEDGER_HOME/downloads
```

Preview the data:

```shell
uv run bean-pod preview transactions.qfx
```

Extract the data:

```shell
uv run beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp extract $LEDGER_HOME/downloads
```

Check the data:

```shell
uv run bean-check $LEDGER_HOME/ledger.beancount
```

Archive the data:

```shell
uv run beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp archive $LEDGER_HOME/downloads --destination=$LEDGER_HOME/documents
```

Fetch latest price of stocks:

```shell
uv run bean-price $LEDGER_HOME/ledger.beancount
uv run bean-price --update $LEDGER_HOME/ledger.beancount
```

## Helpful Links

- [Getting Started with Beancount](https://beancount.github.io/docs/getting_started_with_beancount.html)
- https://github.com/pwalkr/beancount-utils/
- [SQL queries for Beancount](https://aumayr.github.io/beancount-sql-queries/)
- `SELECT last(date) as last_date, account GROUP BY account ORDER BY last_date DESC;`
- https://plaintextaccounting.org/Mortgages#beancount
- https://www.reddit.com/r/plaintextaccounting/comments/hlbb2q/new_to_ledger_tracking_investments_and_and_loans/
- https://www.reddit.com/r/plaintextaccounting/comments/vd7gmg/how_do_you_handle_the_same_transaction_coming/
