# Release checklist

RadialPaths 0.1.0 is prepared as a public source release. PyPI, TestPyPI, and
Zenodo publication remain separate actions that require explicit approval.

## Scientific gate

- [x] Regression fixture matches the frozen geometry implementation.
- [x] GZMERGER09 and GZMERGER29 assignment, coordinate, bin-count, and median
  cross-checks remain exact.
- [x] Circular-limit and internal-boundary tests pass.
- [x] No numerical change was made in the release-candidate pass.

## Name and identity gate

- [x] Repeat the official PyPI lookup for `radialpaths`.
- [x] Repeat GitHub account/organization and repository searches.
- [x] Record the public collision screen without claiming formal legal clearance.
- [x] Reserve the final owner-scoped repository.
- [x] Add final repository, documentation, and issue-tracker URLs to metadata.

## Package gate

- [x] Test supported Python versions in CI.
- [x] Run `pytest` from an installed wheel.
- [x] Build wheel and source distribution in isolation.
- [x] Run `twine check dist/*`.
- [x] Build Sphinx with warnings treated as errors.
- [x] Execute all four notebooks from the installed wheel.
- [x] Build and exercise the browser-native explorer on desktop and mobile.
- [x] Verify the static no-JavaScript tutorial and explorer fallback.
- [x] Re-run Python/JavaScript parity fixtures in CI.
- [x] Validate `CITATION.cff`; add paper and archive identifiers only when known.
- [x] Review license and third-party data/code provenance.

The exact JADES candidate-value comparison runs with
`requirements/paper-reproduction.txt`. Current dependencies are tested
separately against the public API; their last-bit floating-point differences
do not alter candidate positions, masks, geometry, or profiles.

## Publication gate

- [x] Obtain maintainer approval for version 0.1.0 and its changelog.
- [ ] Create the exact annotated `v0.1.0` tag after the final CI run.
- [ ] Upload first to TestPyPI and install from TestPyPI in a clean environment.
- [ ] Upload to PyPI only after the TestPyPI check passes.

The current automation deploys the static browser site to GitHub Pages. It
contains no PyPI, TestPyPI, or Zenodo publication step.
