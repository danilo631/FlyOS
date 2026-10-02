#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

if [[ "${EUID}" -ne 0 ]]; then
  die "ISO remaster needs root. Run: sudo ./build/build-iso.sh"
fi

mapfile -t FLY_DEBS < <(find "$PKG_DIR" -maxdepth 1 -type f -name "flyos-*.deb" ! -name "flyos-kwin-glass_*" -print | sort)
(( ${#FLY_DEBS[@]} > 0 )) || die "No Fly OS packages found. Run make package first."

BASE_ISO="$(sudo -u "${SUDO_USER:-root}" "$PROJECT_ROOT/build/download-base.sh" | tail -n1)"
[[ -f "$BASE_ISO" ]] || die "Base ISO download failed."

LIVEFS_EDIT="$BUILD_DIR/livefs-editor-venv/bin/livefs-edit"
[[ -x "$LIVEFS_EDIT" ]] || die "livefs-editor not found. Run make deps."

PACKAGES_YAML=""
while IFS= read -r pkg; do
  [[ -z "$pkg" || "$pkg" =~ ^[[:space:]]*# ]] && continue
  PACKAGES_YAML+="    - ${pkg}"$'\n'
done < "$PROJECT_ROOT/config/packages.txt"

DEBS_YAML=""
for deb in "${FLY_DEBS[@]}"; do
  DEBS_YAML+="    - ${deb}"$'\n'
done
shopt -s nullglob
GLASS_DEBS=("$PKG_DIR"/flyos-kwin-glass_*.deb)
shopt -u nullglob
if (( ${#GLASS_DEBS[@]} > 0 )); then
  GLASS_DEB="$(ls -1t "${GLASS_DEBS[@]}" | head -n1)"
  DEBS_YAML+="    - ${GLASS_DEB}"$'\n'
  log "Including optional Fly Glass package: $(basename "$GLASS_DEB")"
else
  warn "Fly Glass package not found; ISO will use KDE's built-in blur. Run make glass first for the advanced effect."
fi

ACTIONS="$BUILD_DIR/flyos-actions.yaml"
python3 - "$PROJECT_ROOT/config/flyos-actions.yaml.in" "$ACTIONS" "$PACKAGES_YAML" "$DEBS_YAML" <<'PY'
from pathlib import Path
import sys
src, dst, packages, debs = sys.argv[1:]
text = Path(src).read_text()
text = text.replace("@PACKAGES_YAML@", packages.rstrip("\n"))
text = text.replace("@DEBS_YAML@", debs.rstrip("\n"))
Path(dst).write_text(text)
PY

OUT="$DIST_DIR/FlyOS-${VERSION}-${ARCH}.iso"
rm -f "$OUT"
log "Remastering the official Kubuntu image"
"$LIVEFS_EDIT" "$BASE_ISO" "$OUT" --action-yaml "$ACTIONS"
sha256sum "$OUT" > "$OUT.sha256"
log "Fly OS ISO ready: $OUT"
log "Checksum: $OUT.sha256"
