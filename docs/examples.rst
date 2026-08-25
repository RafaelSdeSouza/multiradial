Examples
========

Browser demonstration
---------------------

An interactive browser-based demonstration is available at
https://RafaelSdeSouza.github.io/multiradial/. It runs locally in the browser
with JupyterLite/Pyodide and requires no software installation. The stable
landing page links to the explorer and tutorial without exposing notebook
filenames in manuscript-facing URLs.

The repository includes two notebooks:

- ``examples/tutorial.ipynb`` builds a folded support, inspects both
  coordinates, and measures two registered tracers.
- ``examples/interactive_explorer.ipynb`` provides compact Panel controls in a
  notebook environment.

For a standalone local application:

.. code-block:: bash

   panel serve app/explorer.py --show

The app exposes compact, folded, perforated, and branched supports. These are
explanatory synthetic scenes; they are not numerical experiments or frozen
paper inputs.
