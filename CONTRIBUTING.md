# Contributing

MultiRadial welcomes focused issues and pull requests. Scientific changes need
an implementation note, regression coverage, and an explicit statement of
whether existing numerical outputs change.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test,docs,demo,io]"
pytest
sphinx-build -W -b html docs docs/_build/html
```

Public functions and classes use NumPy-style docstrings. Keep the core import
light: plotting, FITS, and interactive dependencies must remain optional and
be imported only by the modules that need them.

## Scientific preservation

Do not replace the graph-distance backend, connectivity, boundary definition,
tie rule, normalization, or default profile estimator without a documented
scientific proposal and new regression evidence. See
`docs/implementation_audit.md`.

