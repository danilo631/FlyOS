#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

GLASS_REPO="${GLASS_REPO:-https://github.com/4v3ngR/kwin-effects-glass.git}"
GLASS_REF="${GLASS_REF:-main}"
SRC="$BUILD_DIR/kwin-effects-glass-src"
BLD="$BUILD_DIR/kwin-effects-glass-build"
STAGE="$BUILD_DIR/flyos-kwin-glass-stage"
ARCH="$(dpkg --print-architecture)"

for tool in git cmake c++ dpkg-deb; do
  command -v "$tool" >/dev/null 2>&1 || die "Missing $tool. Run: sudo ./build/prepare-glass-host.sh"
done

if [[ ! -d "$SRC/.git" ]]; then
  git clone "$GLASS_REPO" "$SRC"
fi

git -C "$SRC" fetch --all --tags --prune
git -C "$SRC" checkout --detach "$GLASS_REF"
git -C "$SRC" reset --hard "$GLASS_REF"
git -C "$SRC" clean -fdx

UPSTREAM_VERSION="$(sed -n 's/.*PROJECT_VERSION "\([^"]*\)".*/\1/p' "$SRC/CMakeLists.txt" | head -n1)"
[[ -n "$UPSTREAM_VERSION" ]] || UPSTREAM_VERSION="0+git"
GIT_SHORT="$(git -C "$SRC" rev-parse --short=10 HEAD)"
PKG_VERSION="${UPSTREAM_VERSION}+flyos1~git${GIT_SHORT}"
OUT="$PKG_DIR/flyos-kwin-glass_${PKG_VERSION}_${ARCH}.deb"

rm -rf "$BLD" "$STAGE"
cmake -S "$SRC" -B "$BLD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DGLASS_WAYLAND=ON \
  -DGLASS_X11=OFF
cmake --build "$BLD" -j"$(nproc)"
DESTDIR="$STAGE" cmake --install "$BLD"

mkdir -p "$STAGE/DEBIAN" "$STAGE/usr/share/doc/flyos-kwin-glass"
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: flyos-kwin-glass
Version: ${PKG_VERSION}
Section: kde
Priority: optional
Architecture: ${ARCH}
Maintainer: Fly OS Project <devnull@example.invalid>
Depends: kwin-common, plasma-workspace
Description: advanced optional glass effect for Fly OS
 Fly OS packaging of the open-source KWin Glass effect. It provides force blur,
 rounded corners and additional blur controls for KDE Plasma 6.
CONTROL

cat > "$STAGE/usr/share/doc/flyos-kwin-glass/README.FlyOS" <<DOC
This package is built from:
  ${GLASS_REPO}
Git revision:
  $(git -C "$SRC" rev-parse HEAD)
Upstream version:
  ${UPSTREAM_VERSION}
License:
  GPL-3.0 (see upstream repository)

Fly OS does not claim authorship of the upstream effect. The package is kept
separate because KWin effects may need rebuilding after major Plasma upgrades.
DOC

find "$STAGE" -type d -exec chmod g-s {} +
dpkg-deb --root-owner-group --build "$STAGE" "$OUT"
dpkg-deb --info "$OUT" >/dev/null
log "Fly Glass package ready: $OUT"
