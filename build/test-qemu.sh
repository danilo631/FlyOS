#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

ISO="$DIST_DIR/FlyOS-${VERSION}-${ARCH}.iso"
[[ -f "$ISO" ]] || die "ISO not found. Run make iso."

RAM="${RAM:-4096}"
CPUS="${CPUS:-4}"
DISK="$BUILD_DIR/flyos-test.qcow2"

if [[ ! -f "$DISK" ]]; then
  qemu-img create -f qcow2 "$DISK" 64G
fi

OVMF_CODE=""
for candidate in \
  /usr/share/OVMF/OVMF_CODE_4M.fd \
  /usr/share/OVMF/OVMF_CODE.fd; do
  [[ -f "$candidate" ]] && OVMF_CODE="$candidate" && break
done

args=(
  -machine q35,accel=kvm:tcg
  -m "$RAM"
  -smp "$CPUS"
  -cpu host
  -device virtio-vga-gl
  -display gtk,gl=on
  -device ich9-intel-hda
  -device hda-duplex
  -nic user,model=virtio-net-pci
  -drive "file=$DISK,if=virtio,format=qcow2"
  -cdrom "$ISO"
  -boot d
)

if [[ -n "$OVMF_CODE" ]]; then
  args+=( -drive "if=pflash,format=raw,readonly=on,file=$OVMF_CODE" )
fi

log "Booting Fly OS test VM"
exec qemu-system-x86_64 "${args[@]}"
