#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

BASE_NAME="kubuntu-26.04.1-desktop-amd64.iso"
BASE_URL="https://cdimage.ubuntu.com/kubuntu/releases/26.04.1/release/${BASE_NAME}"
BASE_SHA256="831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8"
OUT="$CACHE_DIR/$BASE_NAME"

if [[ ! -f "$OUT" ]]; then
  log "Downloading official Kubuntu 26.04.1 base image"
  wget -O "$OUT.part" "$BASE_URL"
  mv "$OUT.part" "$OUT"
else
  log "Using cached base image"
fi

echo "${BASE_SHA256}  ${OUT}" | sha256sum -c -
log "Base ISO verified: $OUT"
printf '%s\n' "$OUT"
