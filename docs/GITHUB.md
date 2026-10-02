# GitHub publication

The canonical repository is intended to be `danilo631/FlyOS`.

## Automated path

Install and authenticate GitHub CLI, then from the project root run:

```bash
./scripts/publish-github.sh danilo631/FlyOS
```

The script is deliberately safe around existing repositories: if `origin` exists it pushes there; if the requested GitHub repository exists it adds it as `origin`; otherwise it asks `gh` to create a new public repository and pushes `main`.

Set `FLYOS_REPO_VISIBILITY=private` before running if a private staging repository is desired.

## Branch policy

- `main`: buildable development line.
- `release/*`: stabilization branches.
- feature branches: focused changes merged by pull request.

Releases should be tagged `vX.Y.Z` after the release checklist passes. Developer previews may use tags such as `v0.5.0-dev`.

## Required CI gates

A change should not be released unless shell/Python syntax checks, Debian package build, package content smoke tests and repository hygiene tests pass. ISO and hardware qualification are release gates performed separately because they require privileged runners and large downloads.
