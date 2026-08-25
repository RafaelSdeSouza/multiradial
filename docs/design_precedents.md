# Scientific documentation precedents

Reviewed on 2026-08-25. This note records specific structural decisions; it is
not a list of visual brands to imitate.

## Learn Astropy

[Learn Astropy](https://learn.astropy.org/) organizes tutorial material around
a concrete scientific task, states learning goals, exposes the notebook source,
and offers a route for browser execution. We adopt the task-first structure and
explicit learning goals. We do not make a notebook runtime the primary reading
surface: every RadialPaths tutorial receives a static rendered page first.

## Photutils

[Photutils 3.0](https://photutils.readthedocs.io/en/stable/) separates getting
started material, conceptual user guidance, and factual API reference on its
front page. We use the same information hierarchy. The RadialPaths landing page
will lead with the two-operation workflow, then link separately to tutorials,
coordinate definitions, and API reference.

## SunPy

The [SunPy example gallery](https://docs.sunpy.org/en/stable/generated/gallery/index.html)
groups examples by scientific operation and gives each example a direct,
descriptive title. We adopt concise task titles and a visual tutorial index,
but limit the initial gallery to four maintained notebooks so it remains easy
to scan.

## scikit-image

The [scikit-image gallery](https://scikit-image.org/docs/stable/auto_examples/)
pairs rendered results with runnable source and organizes examples by image
operation. We adopt the rendered-result preview and source/download pairing.
Our examples remain astronomy-facing and distinguish geometry construction
from tracer measurement.

## Gammapy

[Gammapy 2.1](https://docs.gammapy.org/) provides a short getting-started path,
conceptual user guide, tutorial notebooks, and a distinct API reference. Its
[tutorial collection](https://docs.gammapy.org/dev/tutorials/index.html)
offers both rendered notebooks and downloadable notebook/source bundles. We
adopt the visible separation between learning material and reference material.
The current gallery provides static HTML and notebook downloads; Colab links
remain gated on an immutable release tag.

## Decisions for this project

1. The landing page explains one workflow: build geometry once, then measure
   registered tracers on that geometry.
2. `/tutorial/` is static HTML and remains useful with JavaScript disabled.
3. `/explorer/` is a bounded browser-native experiment. It demonstrates the
   coordinate construction without loading Python or a notebook kernel.
4. Four notebooks form the maintained tutorial sequence. Each declares its
   author, summary, learning goals, keywords, and resources in the first cell.
5. Tutorial cards show a real rendered result, not a decorative stock image.
6. API reference stays factual. Explanatory comparisons belong in concepts or
   tutorials, not in generated signatures.
7. Navigation labels use astronomer-facing terms: Learn, Explore, Reference,
   and Cite. “Provenance” is not used as a top-level public label.
