#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

BUNDLE_DIR="$DIST_DIR/release-${VERSION}"
SRC_TAR="$BUNDLE_DIR/FlyOS-source-${VERSION}.tar.gz"
SRC_ZIP="$BUNDLE_DIR/FlyOS-source-${VERSION}.zip"
mkdir -p "$BUNDLE_DIR"

if ! compgen -G "$PKG_DIR/flyos-*_${VERSION}_all.deb" >/dev/null; then
  "$PROJECT_ROOT/build/build-package.sh"
fi
cp -f "$PKG_DIR"/flyos-*_${VERSION}_all.deb "$BUNDLE_DIR/"
"$PROJECT_ROOT/build/sbom.py" >/dev/null
cp -f "$DIST_DIR/FlyOS-${VERSION}.spdx.json" "$BUNDLE_DIR/"

rm -f "$SRC_ZIP" "$SRC_TAR"
tar \
  --exclude='./.git' --exclude='./.build' --exclude='./.cache' \
  --exclude='./.packages' --exclude='./dist' --exclude='*/__pycache__' \
  --exclude='*.pyc' -C "$PROJECT_ROOT" -czf "$SRC_TAR" .
(
  cd "$PROJECT_ROOT"
  zip -qry "$SRC_ZIP" . \
    -x ".git/*" ".build/*" ".cache/*" ".packages/*" "dist/*" \
       "*/__pycache__/*" "*.pyc"
)
(
  cd "$BUNDLE_DIR"
  sha256sum FlyOS-source-"${VERSION}".* FlyOS-"${VERSION}".spdx.json flyos-*_${VERSION}_all.deb > SHA256SUMS
)
echo "Release bundle: $BUNDLE_DIR"
