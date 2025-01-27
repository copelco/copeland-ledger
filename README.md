# copeland-ledger

Tracking our expenses.

## Development

1. Configure your environment:

      ```sh
      layout python python3.12
      ```

2. Install the required dependencies.

      Here we are using `-e`, for ["editable
      mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs),
      so that when our code is modified, the changes automatically apply.

      ```sh
      pip install -e ".[dev]"
      ```

3. Run fava!

      ```sh
      fava $LEDGER_HOME/ledger.beancount
      ```


## Import data

Download files and verify the data:

```sh
beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp identify $LEDGER_HOME/downloads
```

Extract the data:

```sh
beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp extract $LEDGER_HOME/downloads
```

Check the data:

```sh
bean-check $LEDGER_HOME/ledger.beancount
```

Archive the data:

```sh
beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp archive $LEDGER_HOME/downloads --destination=$LEDGER_HOME/documents
```

Fetch latest price of stocks:

```sh
bean-price $LEDGER_HOME/ledger.beancount
bean-price --update $LEDGER_HOME/ledger.beancount
```


## Helpful Links

* [Getting Started with Beancount](https://beancount.github.io/docs/getting_started_with_beancount.html)
* https://github.com/pwalkr/beancount-utils/
