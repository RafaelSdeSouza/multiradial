Contributing
============

Create an isolated environment and install the development dependencies:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e ".[test,docs,demo,io]"
   pytest
   sphinx-build -W -b html docs docs/_build/html

Scientific changes require an implementation note, regression coverage, and
an explicit statement of whether existing numerical outputs change. Do not
replace graph connectivity, boundary semantics, normalization, tie handling,
or profile defaults without a documented scientific proposal. The repository
``CONTRIBUTING.md`` contains the complete contributor guide.
