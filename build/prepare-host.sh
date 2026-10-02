#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

if [[ "${EUID}" -ne 0 ]]; then
  die "Run through: sudo ./build/prepare-host.sh"
fi

log "Installing build dependencies"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  ca-certificates curl wget git python3 python3-venv python3-pip apt-utils \
  xorriso squashfs-tools liblz4-tool python3-debian gpg debootstrap \
  grub-pc-bin grub-efi-amd64-bin mtools dosfstools \
  dpkg-dev fakeroot qemu-system-x86 ovmf make rsync

VENV="$BUILD_DIR/livefs-editor-venv"
if [[ ! -x "$VENV/bin/livefs-edit" ]]; then
  log "Installing livefs-editor in an isolated virtual environment"
  rm -rf "$BUILD_DIR/livefs-editor-src"
  git clone --depth 1 https://github.com/mwhudson/livefs-editor.git "$BUILD_DIR/livefs-editor-src"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install "$BUILD_DIR/livefs-editor-src"
fi

log "Host is ready."
