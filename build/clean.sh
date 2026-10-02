#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

rm -rf "$BUILD_DIR" "$PKG_DIR"
log "Build artifacts removed. Download cache and dist/ were preserved."
