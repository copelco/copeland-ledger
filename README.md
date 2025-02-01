# copeland-ledger

Tracking our expenses using:

* [Beancount](https://beancount.github.io/) (3.0)
* [Beangulp](https://github.com/beancount/beangulp)
* [Fava](https://beancount.github.io/fava/)

## Setup

1. Configure your Python environment:

      ```shell
      # example .envrc file if you use direnv
      layout python python3.12
      ```

2. Install the required dependencies.

      Here we are using `-e`, for ["editable
      mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs),
      so that when our code is modified, the changes automatically apply.

      ```shell
      pip install -e ".[dev]"
      ```

3. Run fava!

      ```shell
      fava $LEDGER_HOME/ledger.beancount
      ```


## Import data

Download files and verify the data:

```shell
beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp identify $LEDGER_HOME/downloads
```

Extract the data:

```shell
beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp extract $LEDGER_HOME/downloads
```

Check the data:

```shell
bean-check $LEDGER_HOME/ledger.beancount
```

Archive the data:

```shell
beangulp-import --config=$LEDGER_HOME/accounts.yaml beangulp archive $LEDGER_HOME/downloads --destination=$LEDGER_HOME/documents
```

Fetch latest price of stocks:

```shell
bean-price $LEDGER_HOME/ledger.beancount
bean-price --update $LEDGER_HOME/ledger.beancount
```


## Helpful Links

* [Getting Started with Beancount](https://beancount.github.io/docs/getting_started_with_beancount.html)
* https://github.com/pwalkr/beancount-utils/
