Examples
========

Browser demonstration
---------------------

An interactive browser-based demonstration is available at
https://rafaelsdesouza.com.br/multiradial/. Its browser-native JavaScript
implementation provides seven synthetic supports, one to four supplied
centres, draggable centre markers, pixel-level path inspection, and animated
profile construction. The static tutorial remains readable without
JavaScript.

The maintained notebook sequence is:

- ``examples/01_quickstart.ipynb`` constructs geometry and a first profile;
- ``examples/02_understanding_coordinates.ipynb`` examines an internal
  boundary;
- ``examples/03_your_own_image.ipynb`` shows every preprocessing stage;
- ``examples/04_registered_tracers.ipynb`` reuses one geometry for several
  scalar fields.

All four notebooks are stored with executed outputs. A Colab link will be
added after an immutable package tag exists, so its installation cell can pin
an exact source revision.

For a standalone local application:

.. code-block:: bash

   panel serve app/explorer.py --show

The optional Panel app remains available for local Python use. The public site
does not require Panel, Pyodide, or a notebook kernel.
