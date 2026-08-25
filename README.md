# MultiRadial

**Centre-conditioned radial analysis for irregular and multi-centred structures**

MultiRadial constructs support-constrained radial geometry from a connected
mask and supplied centres. Build the geometry once, then measure any registered
scalar field—surface brightness, colour, velocity, age, metallicity, or another
pixel-aligned tracer—without redefining radial position.

> MultiRadial is an alpha research-software package. The name is provisional
> pending the release gate in `docs/name_release_gate.md`; it has not been
> published to PyPI.

## Installation

From this repository:

```bash
python -m pip install --upgrade pip
python -m pip install .
```

For plotting and the Panel explorer:

```bash
python -m pip install ".[demo]"
```

## Quick start

```python
from multiradial import build_geometry, radial_profile

geometry = build_geometry(
    support=mask,
    centres=[(42, 31), (58, 74)],  # (row, column)
)

brightness = radial_profile(image, geometry, coordinate="rho_D")
colour = radial_profile(colour_map, geometry, coordinate="rho_X")
velocity = radial_profile(velocity_map, geometry, coordinate="rho_X")

print(brightness.median)  # shape: (n_centres, n_bins)
```

The default profile estimator is the validated observational estimator from
the paper: 30 equal bins on `[0, 1]`, `rho = 1` in the final bin, bins with
fewer than six pixels omitted, and an unweighted median per centre-associated
region.

## Coordinates

For support `Omega`, supplied centre `c_k`, and support-constrained pixel-graph
distance `d_G`:

- `rho_D = d_k / (d_k + b)` measures relative centre–boundary depth;
- `rho_X = d_k / L_k` measures normalized progression within region `B_k`;
- `L_k` is the maximum centre distance in `B_k`.

The implementation intentionally reproduces the paper's validated 8-neighbour
pixel graph. It does not silently substitute Euclidean distance or a continuous
fast-marching solver.

## Browser demonstration

An interactive browser-based demonstration of MultiRadial is available at
<https://RafaelSdeSouza.github.io/multiradial/>. The demonstration runs locally
in the browser using JupyterLite/Pyodide and requires no software installation.
The stable landing page links to both the direct explorer and the tutorial;
the GitHub repository remains the source-code record, while a future Zenodo
DOI will provide the versioned archival citation.

The package has not been published to PyPI or Zenodo.

## Run the explorer locally

```bash
panel serve app/explorer.py --show
```

The explorer switches among compact, folded, perforated, and branched supports,
compares relative boundary depth with normalized progression, and demonstrates
that the same immutable geometry can be applied to different registered tracers.

## Documentation and provenance

- `docs/getting_started.rst` — first analysis
- `docs/concepts.rst` — mathematical definitions and implementation semantics
- `docs/implementation_audit.md` — frozen-source provenance
- `docs/design_notes.md` — documentation and interaction design rationale
- `docs/name_release_gate.md` — provisional-name availability record
- `examples/tutorial.ipynb` — narrative notebook

## Citation

Until the accompanying paper has final bibliographic metadata, cite the
software using `CITATION.cff` and include the software version. See
`docs/citing.rst`.

## License

BSD 3-Clause. See `LICENSE`.
