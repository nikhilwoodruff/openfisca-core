openfisca serve
===============

Additional arguments
--------------------

`openfisca serve` uses `gunicorn` under the hood. In addition to the
arguments listed above, you can use any `gunicorn` arguments when
running `openfisca serve` (e.g. `--reload`, `--workers`, `--timeout`,
`--bind`). See:

``` {.sourceCode .shell}
gunicorn --help
```

Examples
--------

### Basic use

``` {.sourceCode .shell}
openfisca serve --country-package openfisca_france
```

### Serving extensions

``` {.sourceCode .shell}
openfisca serve --country-package openfisca_france --extensions openfisca_paris
```

### Serving reforms

``` {.sourceCode .shell}
openfisca serve --country-package openfisca_france --reforms openfisca_france.reforms.plf2015.plf2015
```

### Using a configuration file

You can setup `openfisca serve` using a configuration file. Be careful
as parameters with a '-' in their name on command line change to an '\_'
when used from the config file. See this example of configuration:

**config.py:**

``` {.sourceCode .py}
port = 4000
workers = 4
bind = '0.0.0.0:{}'.format(port)
country_package = 'openfisca_france'
extensions = ['openfisca_paris']
```

**Command line:**

``` {.sourceCode .shell}
openfisca serve --configuration-file config.py
```