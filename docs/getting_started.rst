Getting started
===============

Install from the repository
---------------------------

.. code-block:: bash

   python -m pip install --upgrade pip
   python -m pip install .

The optional plotting and explorer dependencies are installed with:

.. code-block:: bash

   python -m pip install ".[demo]"

Build geometry once
-------------------

``support`` is a two-dimensional boolean array. ``True`` pixels form the
connected domain in which paths may travel; holes and background are ``False``.
Centres default to NumPy ``(row, column)`` order.

.. code-block:: python

   from multiradial import build_geometry

   geometry = build_geometry(
       support,
       centres=[(42, 31), (58, 74)],
   )

The result exposes the complete construction:

.. code-block:: python

   geometry.distances          # one in-support distance field per centre
   geometry.labels             # centre assignment a(x)
   geometry.boundary_distance  # b(x)
   geometry.rho_D              # relative centre-boundary depth
   geometry.rho_X              # normalized progression
   geometry.extents            # L_k for every centre

Measure registered tracers
--------------------------

.. code-block:: python

   from multiradial import radial_profile

   brightness = radial_profile(image, geometry, coordinate="rho_D")
   colour = radial_profile(colour_map, geometry, coordinate="rho_X")
   velocity = radial_profile(velocity_map, geometry, coordinate="rho_X")

Each result has shape ``(n_centres, n_bins)`` for ``median``, ``p16``, ``p84``,
and ``count``. Bins that contain fewer than six selected pixels retain their
counts but have ``NaN`` summaries.

Plot the result
---------------

.. code-block:: python

   from multiradial.plotting import plot_overview

   figure, axes = plot_overview(
       image, geometry, coordinate="rho_D", profile=brightness
   )

FITS and centre order
---------------------

The optional I/O helper reads FITS data without making Astropy a core import:

.. code-block:: python

   from multiradial.io import read_fits

   image = read_fits("science.fits", extension="SCI")

If centre positions are supplied in ``(x, y)`` order, set
``centre_order="xy"`` explicitly.
