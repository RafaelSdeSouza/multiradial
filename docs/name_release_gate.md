# Provisional name release gate

Checked on 2026-08-24; this is an availability screen, not legal advice.

| Check | Result |
|---|---|
| PyPI distribution `multiradial` | Official JSON endpoint returned HTTP 404; no registered project found |
| Local Python import | `importlib.util.find_spec("multiradial")` returned `None` before package installation |
| GitHub account/organization `multiradial` | Official search API returned zero users/organizations |
| GitHub repositories containing the name | Two repositories found; one exact-case-insensitive `andrasmayer/multiRadial` is an unrelated 2020 radial-menu project, and `samaktbo/Parallel-MultiRadial-Method` is an unrelated notebook repository |
| Obvious web/trademark collision | An old US `MULTIRADIAL` registration for ski edges is cancelled/expired; unrelated descriptive mathematical and medical uses exist |

GitHub repository names are scoped by owner, so the unrelated repository does
not prevent an `OWNER/multiradial` repository. It does mean the bare name is not
globally unique on GitHub.

Before public release:

- reserve the intended GitHub account/organization and repository;
- repeat PyPI and GitHub API checks immediately before publishing;
- run a broader trademark review in intended jurisdictions/classes;
- add the reserved repository and documentation URLs to `CITATION.cff` and
  package metadata;
- confirm the import name in a clean release environment;
- publish only after explicit maintainer approval.

No PyPI upload or public repository creation is part of the present work.
