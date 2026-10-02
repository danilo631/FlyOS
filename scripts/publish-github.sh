#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-danilo631/FlyOS}"
VISIBILITY="${FLYOS_REPO_VISIBILITY:-public}"

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
command -v gh >/dev/null 2>&1 || {
  echo "GitHub CLI (gh) is required for automatic repository creation." >&2
  echo "Install gh, authenticate with 'gh auth login', then rerun this script." >&2
  exit 1
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .git ]]; then
  git init -b main
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "Fly OS $(cat VERSION) developer preview"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Using existing origin: $(git remote get-url origin)"
  git push -u origin HEAD:main
elif gh repo view "$REPO" >/dev/null 2>&1; then
  git remote add origin "https://github.com/${REPO}.git"
  git push -u origin HEAD:main
else
  gh repo create "$REPO" "--${VISIBILITY}" --source=. --remote=origin --push \
    --description "Fly OS — open-source Ubuntu/KDE desktop with Fly Shell, Wine, recovery and adaptive performance."
fi
