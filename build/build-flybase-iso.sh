#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

[[ "$EUID" -eq 0 ]] || die "Fly Base ISO requires root: sudo ./build/build-flybase-iso.sh"
[[ "$ARCH" == "amd64" ]] || die "Fly Base builder currently supports amd64 only."

for cmd in debootstrap mksquashfs grub-mkrescue xorriso chroot rsync; do
  command -v "$cmd" >/dev/null 2>&1 || die "Missing host tool: $cmd (run make deps)"
done

mapfile -t FLY_DEBS < <(find "$PKG_DIR" -maxdepth 1 -type f -name "flyos-*.deb" ! -name "flyos-kwin-glass_*" -print | sort)
(( ${#FLY_DEBS[@]} > 0 )) || die "No Fly OS packages found. Run make package first."

SUITE="${FLYOS_UBUNTU_SUITE:-resolute}"
MIRROR="${FLYOS_UBUNTU_MIRROR:-http://archive.ubuntu.com/ubuntu}"
SECURITY_MIRROR="${FLYOS_UBUNTU_SECURITY_MIRROR:-http://security.ubuntu.com/ubuntu}"
ROOTFS="$BUILD_DIR/flybase-rootfs"
ISO="$BUILD_DIR/flybase-iso"
OUT="$DIST_DIR/FlyOS-${VERSION}-${ARCH}-flybase.iso"

cleanup_mounts() {
  for p in run sys proc dev/pts dev; do
    mountpoint -q "$ROOTFS/$p" && umount -lf "$ROOTFS/$p" || true
  done
}
trap cleanup_mounts EXIT

rm -rf "$ROOTFS" "$ISO"
mkdir -p "$ROOTFS" "$ISO/casper" "$ISO/boot/grub" "$ISO/.disk"

log "Bootstrapping Ubuntu $SUITE minimal rootfs (compatibility layer only)"
debootstrap --arch="$ARCH" --variant=minbase "$SUITE" "$ROOTFS" "$MIRROR"

cat > "$ROOTFS/etc/apt/sources.list" <<EOF
# Fly OS uses Ubuntu archives as a compatibility base. Fly-owned packages are
# intended to move to a separate repository as the project matures.
deb $MIRROR $SUITE main restricted universe multiverse
deb $MIRROR ${SUITE}-updates main restricted universe multiverse
deb $SECURITY_MIRROR ${SUITE}-security main restricted universe multiverse
EOF

cp -L /etc/resolv.conf "$ROOTFS/etc/resolv.conf"
mount --bind /dev "$ROOTFS/dev"
mount --bind /dev/pts "$ROOTFS/dev/pts"
mount -t proc proc "$ROOTFS/proc"
mount -t sysfs sys "$ROOTFS/sys"
mount --bind /run "$ROOTFS/run"

export DEBIAN_FRONTEND=noninteractive
chroot "$ROOTFS" apt-get update

mapfile -t PKGS < <(grep -Ev '^\s*(#|$)' "$PROJECT_ROOT/config/minimal-packages.txt")
log "Installing ${#PKGS[@]} Fly Base runtime packages"
chroot "$ROOTFS" apt-get install -y --no-install-recommends "${PKGS[@]}"

mkdir -p "$ROOTFS/tmp/flyos-debs"
cp "${FLY_DEBS[@]}" "$ROOTFS/tmp/flyos-debs/"
chroot "$ROOTFS" apt-get install -y --no-install-recommends /tmp/flyos-debs/*.deb
rm -rf "$ROOTFS/tmp/flyos-debs"

# A small live-session definition; casper creates the temporary live account.
cat > "$ROOTFS/etc/casper.conf" <<'EOF'
export USERNAME="fly"
export USERFULLNAME="Fly OS Live User"
export HOST="flyos"
export BUILD_SYSTEM="Ubuntu"
export FLAVOUR="Fly OS"
EOF

# Locale + display manager defaults.
chroot "$ROOTFS" locale-gen en_US.UTF-8 pt_BR.UTF-8 || true
printf 'LANG=pt_BR.UTF-8\n' > "$ROOTFS/etc/default/locale"
mkdir -p "$ROOTFS/etc/sddm.conf.d"
cat > "$ROOTFS/etc/sddm.conf.d/10-flyos-session.conf" <<'EOF'
[General]
DisplayServer=wayland
EOF

# Apply project identity/theme/service defaults inside the image.
chroot "$ROOTFS" /usr/lib/flyos/image-finalize || true

# Preserve a Plasma fallback only if explicitly requested; the native ISO does
# not pull the full Plasma shell by default.
if [[ "${FLYOS_INCLUDE_PLASMA_FALLBACK:-0}" == "1" ]]; then
  chroot "$ROOTFS" apt-get install -y plasma-workspace plasma-session-wayland
fi

# Clean identifiers/caches so the live system generates them at boot.
chroot "$ROOTFS" apt-get clean
rm -rf "$ROOTFS/var/lib/apt/lists/"* "$ROOTFS/var/cache/apt/archives/"* || true
truncate -s 0 "$ROOTFS/etc/machine-id" || true
rm -f "$ROOTFS/var/lib/dbus/machine-id" || true
rm -rf "$ROOTFS/tmp/"* "$ROOTFS/var/tmp/"* || true

cleanup_mounts

KERNEL="$(ls -1 "$ROOTFS"/boot/vmlinuz-* | sort -V | tail -n1)"
INITRD="${KERNEL/vmlinuz-/initrd.img-}"
[[ -f "$KERNEL" && -f "$INITRD" ]] || die "Kernel/initrd not found in Fly Base rootfs"
cp "$KERNEL" "$ISO/casper/vmlinuz"
cp "$INITRD" "$ISO/casper/initrd"

log "Creating compressed live filesystem"
mksquashfs "$ROOTFS" "$ISO/casper/filesystem.squashfs" -comp zstd -Xcompression-level 15 -noappend
printf '%s\n' "$(du -sx --block-size=1 "$ROOTFS" | cut -f1)" > "$ISO/casper/filesystem.size"
chroot "$ROOTFS" dpkg-query -W --showformat='${Package} ${Version}\n' > "$ISO/casper/filesystem.manifest" || true

cat > "$ISO/.disk/info" <<EOF
Fly OS ${VERSION} "Fly Base" - amd64
EOF
cat > "$ISO/boot/grub/grub.cfg" <<'EOF'
set timeout=7
set default=0

menuentry "Try or Install Fly OS" {
    linux /casper/vmlinuz boot=casper quiet splash ---
    initrd /casper/initrd
}
menuentry "Fly OS (safe graphics)" {
    linux /casper/vmlinuz boot=casper nomodeset ---
    initrd /casper/initrd
}
EOF

log "Building hybrid BIOS/UEFI developer ISO"
grub-mkrescue -o "$OUT" "$ISO" >/dev/null
sha256sum "$OUT" > "$OUT.sha256"
log "Fly Base ISO ready: $OUT"
warn "Fly Base is a developer pipeline. grub-mkrescue EFI media is not yet the signed Secure-Boot release path; use the remaster ISO for Secure-Boot validation until shim signing is integrated."
