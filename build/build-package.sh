#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"
log "Building modular Fly OS packages for $VERSION"
exec python3 "$PROJECT_ROOT/build/build-packages.py"
