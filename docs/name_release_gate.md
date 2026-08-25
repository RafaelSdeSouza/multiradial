# RadialPaths name release gate

Checked on 2026-08-25. This is a practical availability screen, not legal
clearance or legal advice.

## Recommendation

**CAUTION — suitable for release preparation.** No conflicting software,
package-registry, organization, commercial product, or astronomy-literature
use was found for `RadialPaths` / `radialpaths`. The GitHub repository search
now returns this project after its authorized rename. The caution reflects the
descriptive phrase “radial paths”, which occurs as ordinary technical prose in
several unrelated fields and therefore does not form a highly distinctive
name.

No material collision requires the release to stop. This is an availability
screen, not a formal trademark opinion.

## Checks performed

| Check | Result |
|---|---|
| PyPI distribution `radialpaths` | The [official JSON endpoint](https://pypi.org/pypi/radialpaths/json) returned HTTP 404; no registered project was found |
| PyPI near-name `radial-paths` | The normalized project endpoint returned HTTP 404 |
| conda-forge package `radialpaths` | The [Anaconda API endpoint](https://api.anaconda.org/package/conda-forge/radialpaths) returned HTTP 404 |
| GitHub account or organization `radialpaths` | The [official user-search API](https://api.github.com/search/users?q=radialpaths) returned zero matches |
| GitHub repository named `radialpaths` | The name was free immediately before migration; the current exact match is this project at `RafaelSdeSouza/radialpaths` |
| npm package `radialpaths` | The official registry endpoint returned HTTP 404 |
| arXiv exact term `RadialPaths` | The [official arXiv API query](https://export.arxiv.org/api/query?search_query=all:%22RadialPaths%22&start=0&max_results=10) returned zero records |
| Crossref exact term `RadialPaths` | The public works API returned zero records |
| CRAN package `radialpaths` | The CRAN package database returned HTTP 404 |
| crates.io package `radialpaths` | The registry returned HTTP 404 |
| Astronomy software and literature | General and astronomy-specific exact-name searches found no package, project, or method called `RadialPaths` |
| Broader web use | “Radial paths” occurs descriptively; the nearest software result was PowerWorld's “Find Radial Bus Paths” command, not a product or package named RadialPaths |
| Obvious commercial or trademark collision | No obvious exact-name software product or active exact-name commercial use was found in the public searches performed |

## Migration record

The release-candidate migration uses:

1. project, distribution, and import name `radialpaths`;
2. no legacy import namespace because MultiRadial had no stable public
   release;
3. updated documentation, examples, notebooks, package metadata, and browser
   site links;
4. a deliberately small callable root API:
   `build_geometry` and `radial_profile` at the package root;
5. repository `https://github.com/RafaelSdeSouza/radialpaths`;
6. canonical site `https://rafaelsdesouza.com.br/radialpaths/`;
7. `/multiradial/` retained only as a redirect.

## Remaining release checks

- repeat the registry and GitHub checks immediately before publication;
- have the maintainer perform any formal trademark review considered necessary
  in the intended jurisdictions and classes;
- verify the canonical import in clean wheel and source-distribution installs;
- verify the old site redirects after deployment;
- publish to PyPI or Zenodo only after explicit maintainer approval.

**Current state:** PyPI not published; Zenodo not published; remote repository
renamed to `RafaelSdeSouza/radialpaths`; release QA in progress.
