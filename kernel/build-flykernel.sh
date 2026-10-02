#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/.build/flykernel"
OUT="$ROOT/dist/kernel"
LINUX_TAG="${LINUX_TAG:-v7.2.8}"
FLAVOUR="${FLAVOUR:-fly}"
JOBS="${JOBS:-$(nproc)}"

mkdir -p "$WORK" "$OUT"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing tool: $1" >&2; exit 1; }; }
for t in git make gcc scripts/config dpkg-buildpackage; do
  if [[ "$t" == "scripts/config" ]]; then continue; fi
  need "$t"
done

if [[ ! -d "$WORK/linux/.git" ]]; then
  git clone --filter=blob:none https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git "$WORK/linux"
fi

if [[ ! -d "$WORK/ukpack/.git" ]]; then
  git clone --depth 1 https://github.com/ubuntu/ukpack.git "$WORK/ukpack"
fi

cd "$WORK/linux"
git fetch --tags --force origin "$LINUX_TAG"
git reset --hard "$LINUX_TAG"
git clean -fdx

git apply "$ROOT/kernel/patches/0001-flyos-banner.patch"

make x86_64_defconfig
scripts/kconfig/merge_config.sh -m .config "$ROOT/kernel/flykernel.fragment"
make olddefconfig

KVER="${LINUX_TAG#v}"
TOML="$WORK/flykernel.toml"
cat > "$TOML" <<EOF
linux-${FLAVOUR} (${KVER}-0fly1) resolute; urgency=medium

 * Fly OS development kernel

 -- Fly OS Project <devnull@example.invalid>  Wed, 30 Sep 2026 00:00:00 -0300
---
arch = "amd64"
config = "$WORK/linux/.config"
orig = "${LINUX_TAG}"

[pkg.source]
Maintainer = "Fly OS Project <devnull@example.invalid>"
EOF

TARBALL="$WORK/linux-${KVER}.tar.xz"
if [[ ! -f "$TARBALL" ]]; then
  git archive --format=tar --prefix="linux-${KVER}/" "$LINUX_TAG" | xz -T0 > "$TARBALL"
fi

rm -rf "$WORK/output"
mkdir -p "$WORK/output"

"$WORK/ukpack/ukpack" -o "$TARBALL" -d "$WORK/output" "$TOML"

cp -av "$WORK/output"/* "$OUT/" || true
echo "FlyKernel build output: $OUT"
