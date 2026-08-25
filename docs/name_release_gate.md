# RadialPaths name release gate

Checked on 2026-08-25. This is a practical availability screen, not legal
clearance or legal advice.

## Recommendation

**CAUTION — suitable for local adoption and migration preparation.** No exact
software, repository, package-registry, or astronomy-literature collision was
found for `RadialPaths` / `radialpaths`. The caution reflects the descriptive
nature of the words “radial paths”, which occur as ordinary technical prose in
several unrelated fields and therefore do not form a highly distinctive name.

No material collision was found that requires the migration to stop. The
GitHub repository and public documentation path must nevertheless remain
unchanged until the renamed package and browser site pass the release checks.

## Checks performed

| Check | Result |
|---|---|
| PyPI distribution `radialpaths` | The [official JSON endpoint](https://pypi.org/pypi/radialpaths/json) returned HTTP 404; no registered project was found |
| PyPI near-name `radial-paths` | The normalized project endpoint returned HTTP 404 |
| conda-forge package `radialpaths` | The [Anaconda API endpoint](https://api.anaconda.org/package/conda-forge/radialpaths) returned HTTP 404 |
| GitHub account or organization `radialpaths` | The [official user-search API](https://api.github.com/search/users?q=radialpaths) returned zero matches |
| GitHub repository named `radialpaths` | The [official repository-search API](https://api.github.com/search/repositories?q=radialpaths+in%3Aname) returned zero matches |
| npm package `radialpaths` | The official registry endpoint returned HTTP 404 |
| arXiv exact term `RadialPaths` | The [official arXiv API query](https://export.arxiv.org/api/query?search_query=all:%22RadialPaths%22&start=0&max_results=10) returned zero records |
| Astronomy software and literature | General and astronomy-specific exact-name searches found no package, project, or method called `RadialPaths` |
| Broader web use | “radial paths” occurs descriptively in power systems, robotics, radio propagation, anatomy, and other fields; none of the reviewed results was an exact software-brand collision |
| Obvious commercial or trademark collision | No obvious exact-name software product or active exact-name commercial use was found in the public searches performed |

## Migration proposal recorded before public API change

If the maintainer adopts the name, the local migration should be one reviewed
change set:

1. rename the distribution and canonical import to `radialpaths`;
2. retain a temporary `multiradial` compatibility namespace that issues a
   deprecation warning and re-exports the stable public surface;
3. update source paths, documentation, examples, notebooks, test imports,
   package metadata, and browser-site text together;
4. keep the callable public surface deliberately small:
   `build_geometry` and `radial_profile` at the package root;
5. preserve the current GitHub repository and `/multiradial/` deployment until
   the renamed package, static tutorial, browser explorer, and redirects pass
   their full checks;
6. rename the remote repository and move the canonical site to
   `/radialpaths/` only with explicit maintainer approval;
7. keep `/multiradial/` as a redirect after the public move.

## Remaining release checks

- repeat the registry and GitHub checks immediately before publication;
- have the maintainer perform any formal trademark review considered necessary
  in the intended jurisdictions and classes;
- reserve the final repository and documentation URLs;
- verify both the canonical and compatibility imports in clean environments;
- publish to PyPI or Zenodo only after explicit maintainer approval.

**Current state:** PyPI not published; Zenodo not published; remote repository
not renamed.
