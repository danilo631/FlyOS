#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(cat "$PROJECT_ROOT/VERSION")"
ARCH="${ARCH:-amd64}"
BUILD_DIR="$PROJECT_ROOT/.build"
CACHE_DIR="$PROJECT_ROOT/.cache"
DIST_DIR="$PROJECT_ROOT/dist"
PKG_DIR="$PROJECT_ROOT/.packages"

log() { printf '\033[1;36m[FlyOS]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[FlyOS]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[FlyOS]\033[0m ERROR: %s\n' "$*" >&2; exit 1; }

mkdir -p "$BUILD_DIR" "$CACHE_DIR" "$DIST_DIR" "$PKG_DIR"
