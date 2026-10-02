#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

if [[ "${EUID}" -ne 0 ]]; then
  die "Run through: sudo ./build/prepare-glass-host.sh"
fi

log "Installing Fly Glass build dependencies"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  git cmake g++ extra-cmake-modules qt6-tools-dev kwin-dev \
  libkf6configwidgets-dev gettext libkf6crash-dev libkf6globalaccel-dev \
  libkf6kio-dev libkf6service-dev libkf6notifications-dev libkf6kcmutils-dev \
  libkdecorations3-dev libxcb-composite0-dev libxcb-randr0-dev \
  libxcb-shm0-dev vulkan-headers dpkg-dev
