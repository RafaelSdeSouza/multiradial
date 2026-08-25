RadialPaths
===========

**Centre-conditioned radial analysis for irregular and multi-centred
structures.**

RadialPaths defines radial position from a connected support and supplied
centres, then applies that geometry to any registered scalar field. It is aimed
at astronomers working with irregular galaxies, mergers, tidal structures,
clump complexes, resolved populations, and spatially resolved kinematics.

.. code-block:: python

   from radialpaths import build_geometry, radial_profile

   geometry = build_geometry(mask, centres)
   brightness = radial_profile(image, geometry, coordinate="rho_D")
   velocity = radial_profile(velocity_map, geometry, coordinate="rho_X")

.. warning::

   This is a provisional alpha package. It has not been published to PyPI and
   the release-name checks remain open.

.. toctree::
   :maxdepth: 2
   :caption: Learn

   getting_started
   preprocessing
   concepts
   examples

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api
   implementation_audit

.. toctree::
   :maxdepth: 1
   :caption: Project

   citing
   contributing
   design_precedents
   design_notes
   name_release_gate
   release_checklist
