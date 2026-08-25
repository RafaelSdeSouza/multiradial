# Release checklist

RadialPaths is not yet approved for a public release. A maintainer should
complete and record every item below before creating a public repository or
uploading a distribution.

## Scientific gate

- [ ] Regression fixture matches the frozen geometry implementation.
- [ ] GZMERGER09 and GZMERGER29 assignment, coordinate, bin-count, and median
  cross-checks remain exact.
- [ ] Circular-limit and internal-boundary tests pass.
- [ ] Any numerical change has a reviewed scientific rationale and changelog.

## Name and identity gate

- [ ] Repeat the official PyPI lookup for `radialpaths`.
- [ ] Repeat GitHub account/organization and repository searches.
- [ ] Complete an appropriate trademark review.
- [ ] Reserve the final owner-scoped repository.
- [ ] Add final repository, documentation, and issue-tracker URLs to metadata.

## Package gate

- [ ] Test supported Python versions in CI.
- [ ] Run `pytest` from an installed wheel.
- [ ] Build wheel and source distribution in isolation.
- [ ] Run `twine check dist/*`.
- [ ] Build Sphinx with warnings treated as errors.
- [ ] Build and manually exercise the browser-native explorer on desktop and mobile.
- [ ] Verify the static no-JavaScript tutorial and explorer fallback.
- [ ] Re-run Python/JavaScript parity fixtures in CI.
- [ ] Validate `CITATION.cff` and add the final paper DOI/reference when known.
- [ ] Review license and third-party data/code provenance.

## Publication gate

- [ ] Obtain explicit maintainer approval for the version and changelog.
- [ ] Create a signed/tagged release.
- [ ] Upload first to TestPyPI and install from TestPyPI in a clean environment.
- [ ] Upload to PyPI only after the TestPyPI check passes.

The current automation deploys the static browser site to GitHub Pages. It
contains no PyPI, TestPyPI, or Zenodo publication step.
