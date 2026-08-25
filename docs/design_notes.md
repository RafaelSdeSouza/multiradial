# Design notes

Geometry is determined by the support and supplied centres, while the tracer
measured on that geometry may change. The public API therefore separates
`build_geometry(...)` from
`radial_profile(data, geometry, ...)` and returns inspectable result objects.

## Precedents inspected

- [Astropy documentation guidelines](https://docs.astropy.org/en/latest/development/docguide.html)
  separate narrative documentation from generated API reference, require
  complete public docstrings, and use NumPy-style documentation. RadialPaths
  adopts that separation and numpydoc conventions.
- [Astropy's user-facing documentation](https://docs.astropy.org/en/stable/index.html)
  provides a short getting-started route before a deeper user guide, while its
  contributor material makes citation and contribution paths visible.
  RadialPaths mirrors this hierarchy without copying Astropy's branding.
- [Photutils profiles](https://photutils.readthedocs.io/en/stable/user_guide/index.html)
  use result objects whose bin edges are inputs and bin centres are outputs.
  RadialPaths likewise returns a `RadialProfile` object with edges, radii,
  counts, medians, and percentile summaries rather than a loose tuple.
- [Photutils segmentation](https://photutils.readthedocs.io/en/stable/user_guide/segmentation.html)
  cleanly distinguishes a labeled spatial representation from measurements on
  image data. This supports RadialPaths's reusable `RadialGeometry` object.
- [scikit-image's example gallery](https://scikit-image.org/docs/stable/auto_examples/)
  combines concise runnable examples with a separate narrative guide. The
  package keeps notebooks task-focused and the API reference factual.
- The browser explorer uses a small control column, responsive scientific
  views, and direct manipulation of supplied centres. It implements the
  validated graph and profile rules in JavaScript and is checked against
  Python-authored fixtures.
- Browser notebooks require separate WebAssembly dependency and kernel
  maintenance. They are not part of the primary public reading path. The
  current tutorial is static HTML with downloadable executed notebooks.
- The [Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
  motivates the `src/` layout so tests exercise the installed package instead
  of importing accidentally from the repository root.

## Applied principles

1. **Discoverable core.** The top-level import exposes only the two primary
   operations and their result classes.
2. **Inspectable science.** Geometry stores centre distances, assignment,
   boundary pixels, boundary distance, both coordinates, and extents.
3. **Preserved defaults.** Connectivity, tie handling, normalization, endpoint
   binning, minimum counts, and median statistics match the validated paper.
4. **Optional surface area.** Matplotlib, Astropy, Pillow, and Panel are extras; they do
   not load during `import radialpaths`.
5. **Meaningful examples.** Circular, compact, elongated, folded, branched,
   perforated, and merger-like supports each isolate a geometric behaviour.
6. **Restrained visuals.** Cividis fields, crisp neutral boundaries, white
   contours, and direct centre markers match the manuscript's explanatory
   grammar without reproducing its branding.
