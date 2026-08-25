Concepts
========

Support-constrained distance
----------------------------

Let :math:`\Omega` be the connected accepted support and :math:`c_k` a supplied
centre. MultiRadial computes

.. math::

   d_k(x) = d_G(c_k, x),

where :math:`d_G` is the shortest path on the 8-neighbour in-support pixel
graph. Paths cannot cross background or internal holes. Axial graph steps cost
one pixel and diagonal steps cost :math:`\sqrt{2}` pixels.

Centre-associated regions
-------------------------

Each support pixel is assigned to its closest supplied centre:

.. math::

   a(x) = \operatorname*{arg\,min}_k d_k(x),
   \qquad B_k = \{x \in \Omega : a(x) = k\}.

Exact distance ties are assigned to the first centre in the supplied sequence,
matching ``numpy.argmin`` and the validated implementation.

Relative centre–boundary depth
------------------------------

Let :math:`b(x)` be the in-support graph distance to the closest boundary
pixel. A boundary pixel is in :math:`\Omega` and touches an excluded pixel in
its 3-by-3 neighborhood. This includes the edge of any internal hole.

.. math::

   \rho_{D,k}(x) = \frac{d_k(x)}{d_k(x) + b(x)}, \qquad x \in B_k.

The coordinate is zero at its centre and one on represented support
boundaries.

Normalized progression
----------------------

For each centre-associated region,

.. math::

   L_k = \max_{x \in B_k} d_k(x),
   \qquad
   \rho_{X,k}(x) = \frac{d_k(x)}{L_k}.

This coordinate describes progression from a supplied centre to the furthest
point assigned to it. Unlike :math:`\rho_D`, it is not a boundary-depth
coordinate.

Profiles
--------

The default profile estimator follows the observational figures: 30 equal
bins on :math:`[0,1]`, unweighted median intensity in each centre-associated
region, at least six pixels per populated bin, and :math:`\rho=1` included in
the final bin. The 16th and 84th percentiles are returned for descriptive
spread. No curve or spline is fitted.

Geometry is tracer-independent
------------------------------

The support and centres determine :math:`B_k`, :math:`\rho_D`, and
:math:`\rho_X`. The intensity or physical tracer enters only when
``radial_profile`` is called. Registered maps can therefore share an identical
radial geometry, making cross-tracer comparisons explicit.

