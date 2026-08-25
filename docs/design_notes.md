# Design notes

MultiRadial is designed around one scientific sentence: geometry is determined
by the support and supplied centres, while the tracer measured on that geometry
may change. The public API therefore separates `build_geometry(...)` from
`radial_profile(data, geometry, ...)` and returns inspectable result objects.

## Precedents inspected

- [Astropy documentation guidelines](https://docs.astropy.org/en/latest/development/docguide.html)
  separate narrative documentation from generated API reference, require
  complete public docstrings, and use NumPy-style documentation. MultiRadial
  adopts that separation and numpydoc conventions.
- [Astropy's user-facing documentation](https://docs.astropy.org/en/stable/index.html)
  provides a short getting-started route before a deeper user guide, while its
  contributor material makes citation and contribution paths visible.
  MultiRadial mirrors this hierarchy without copying Astropy's branding.
- [Photutils profiles](https://photutils.readthedocs.io/en/stable/user_guide/index.html)
  use result objects whose bin edges are inputs and bin centres are outputs.
  MultiRadial likewise returns a `RadialProfile` object with edges, radii,
  counts, medians, and percentile summaries rather than a loose tuple.
- [Photutils segmentation](https://photutils.readthedocs.io/en/stable/user_guide/segmentation.html)
  cleanly distinguishes a labeled spatial representation from measurements on
  image data. This supports MultiRadial's reusable `RadialGeometry` object.
- [scikit-image's example gallery](https://scikit-image.org/docs/stable/auto_examples/)
  combines concise runnable examples with a separate narrative guide. The
  package keeps notebooks task-focused and the API reference factual.
- [Panel's responsive-layout guidance](https://panel.holoviz.org/tutorials/basic/size.html)
  favors explicit responsive sizing and direct widgets. The explorer uses a
  small control column and a responsive scientific view, with no decorative
  dashboard chrome.
- [JupyterLite's deployment guide](https://jupyterlite.readthedocs.io/en/stable/quickstart/standalone.html)
  shows that browser-native notebooks are static deployable artifacts but need
  deliberate kernel and dependency handling. A JupyterLite release remains a
  gated follow-up until the local wheel and WebAssembly dependency set are
  tested; the current deliverables are portable notebooks and a Panel app.
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
4. **Optional surface area.** Matplotlib, Astropy, and Panel are extras; they do
   not load during `import multiradial`.
5. **Meaningful examples.** Compact, folded, perforated, and branched supports
   each illustrate a distinct geometric behavior.
6. **Restrained visuals.** Cividis fields, crisp neutral boundaries, white
   contours, and direct centre markers match the manuscript's explanatory
   grammar without reproducing its branding.

