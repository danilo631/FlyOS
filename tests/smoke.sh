#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p .build/pycache
export PYTHONPYCACHEPREFIX="$ROOT/.build/pycache"

# Shell syntax for every project script.
while IFS= read -r f; do
  bash -n "$f"
done < <(grep -rlE '^#!(/usr/bin/env bash|/bin/bash)' build kernel scripts packages tests || true)

# Python syntax without polluting the source tree.
mapfile -t PYS < <(find packages/flyos-base/rootfs/usr build -type f -print | while read -r f; do
  head -n1 "$f" 2>/dev/null | grep -q '^#!/usr/bin/env python3' && echo "$f" || true
done)
PYS+=(
  packages/flyos-base/rootfs/usr/lib/flyos/fly-center.py
  packages/flyos-base/rootfs/usr/lib/flyos/fly-welcome.py
  packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
  packages/flyos-base/rootfs/usr/lib/flyos/fly-health.py
  packages/flyos-base/rootfs/usr/lib/flyos/fly-apps.py
  packages/flyos-base/rootfs/usr/lib/flyos/fly-updater.py
  build/build-packages.py
)
python3 -m py_compile "${PYS[@]}"

python3 - <<'PY'
import configparser, json
from pathlib import Path
root=Path('packages/flyos-base/rootfs')
for p in root.rglob('*.json'):
    json.loads(p.read_text())
for p in root.rglob('*.desktop'):
    if not p.is_file():
        continue
    c=configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform=str
    c.read(p, encoding='utf-8')
    if not c.sections():
        raise SystemExit(f'Empty desktop-style metadata: {p}')
    if ('/applications/' in p.as_posix() or '/wayland-sessions/' in p.as_posix()) and 'Desktop Entry' not in c:
        raise SystemExit(f'Invalid launcher/session file: {p}')
print('metadata: OK')
PY

# systemd unit syntax: missing host commands are expected in the build container,
# but parser/unknown-directive errors are always release blockers.
if command -v systemd-analyze >/dev/null 2>&1; then
  unit_log="$(mktemp)"
  mapfile -t UNIT_FILES < <(find packages/flyos-base/rootfs/usr/lib/systemd -type f \
    \( -name '*.service' -o -name '*.timer' -o -name '*.target' -o -name '*.slice' \) -print)
  systemd-analyze verify "${UNIT_FILES[@]}" >"$unit_log" 2>&1 || true
  if grep -E 'Unknown key|Unknown lvalue|Failed to parse|Invalid section|Invalid setting' "$unit_log"; then
    echo 'Invalid systemd unit syntax detected' >&2
    cat "$unit_log" >&2
    rm -f "$unit_log"
    exit 1
  fi
  rm -f "$unit_log"
fi
! grep -Rq '^ConditionPathIsExecutable=' packages/flyos-base/rootfs/usr/lib/systemd

# Source-tree hygiene: generated Python bytecode must never be packaged/committed.
if find packages -type f \( -name '*.pyc' -o -path '*/__pycache__/*' \) -print -quit | grep -q .; then
  echo 'Source tree contains Python bytecode' >&2
  exit 1
fi

test ! -d packages/flyos-base/DEBIAN
for control in flyos-base flyos-core flyos-shell flyos-center flyos-search flyos-update flyos-recovery flyos-privacy flyos-performance flyos-wine flyos-branding flyos-repo; do
  test -s "packages/components/${control}.control"
done

# Native Fly session must not leak into unrelated desktops.
! grep -q '^WantedBy=default.target' packages/flyos-base/rootfs/usr/lib/systemd/user/flyos-session.target
! grep -q '^StopWhenUnneeded=yes' packages/flyos-base/rootfs/usr/lib/systemd/user/flyos-session.target
grep -q 'systemctl --user start flyos-session.target' packages/flyos-base/rootfs/usr/lib/flyos/fly-session-inner

# Rapid shell shortcuts are queued instead of overwriting one command file.
grep -q 'path.open("a"' packages/flyos-base/rootfs/usr/bin/fly-shellctl
grep -q 'unset-environment.*FLYOS_SAFE_MODE' packages/flyos-base/rootfs/usr/bin/fly-shellctl
grep -q 'def restart_normal' packages/flyos-base/rootfs/usr/lib/flyos/fly-rescue-ui.py
grep -q 'queued.splitlines()' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'osd-volume:' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'mediaAction' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml

# Fly Base installs the complete local package set with no Recommends, so the
# optional Plasma fallback cannot be pulled in accidentally.
grep -q -- '--no-install-recommends /tmp/flyos-debs/\*.deb' build/build-flybase-iso.sh

# The derivative identity must not overwrite Ubuntu-owned /usr/lib/os-release.
if grep -REn '(^|[[:space:]])(cp|install|mv).*[/]usr/lib/os-release' packages/flyos-base/rootfs/usr/lib/flyos packages/components; then
  echo 'Unsafe /usr/lib/os-release overwrite detected' >&2
  exit 1
fi

./build/build-package.sh
VERSION="$(cat VERSION)"
PKGS=(flyos-core flyos-shell flyos-center flyos-search flyos-update flyos-recovery flyos-privacy flyos-performance flyos-wine flyos-branding flyos-repo flyos-base)
for pkg in "${PKGS[@]}"; do
  deb=".packages/${pkg}_${VERSION}_all.deb"
  test -s "$deb"
  dpkg-deb --info "$deb" >/dev/null
done

# Metapackage wiring and modular ownership regression tests.
dpkg-deb -f ".packages/flyos-base_${VERSION}_all.deb" Depends | grep -q "flyos-core (= ${VERSION})"
dpkg-deb -f ".packages/flyos-base_${VERSION}_all.deb" Depends | grep -q "flyos-shell (= ${VERSION})"
dpkg-deb -f ".packages/flyos-base_${VERSION}_all.deb" Depends | grep -q "flyos-search (= ${VERSION})"
dpkg-deb -f ".packages/flyos-base_${VERSION}_all.deb" Depends | grep -q "flyos-recovery (= ${VERSION})"
dpkg-deb -f ".packages/flyos-base_${VERSION}_all.deb" Depends | grep -q "flyos-privacy (= ${VERSION})"
dpkg-deb -f ".packages/flyos-base_${VERSION}_all.deb" Depends | grep -q "flyos-performance (= ${VERSION})"
dpkg-deb -f ".packages/flyos-base_${VERSION}_all.deb" Depends | grep -q "flyos-repo (= ${VERSION})"
pkg_has() {
  local deb="$1" path="$2" listing
  listing="$(mktemp)"
  dpkg-deb -c "$deb" > "$listing"
  grep -Fq "$path" "$listing" || { rm -f "$listing"; echo "Missing $path in $deb" >&2; return 1; }
  rm -f "$listing"
}
pkg_has ".packages/flyos-shell_${VERSION}_all.deb" './usr/share/wayland-sessions/flyos.desktop'
pkg_has ".packages/flyos-shell_${VERSION}_all.deb" './usr/bin/fly-volume'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/lib/flyos/fly-center.py'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-center'
pkg_has ".packages/flyos-search_${VERSION}_all.deb" './usr/bin/fly-indexer'
pkg_has ".packages/flyos-search_${VERSION}_all.deb" './usr/bin/fly-search'
pkg_has ".packages/flyos-update_${VERSION}_all.deb" './usr/lib/flyos/fly-updater.py'
pkg_has ".packages/flyos-recovery_${VERSION}_all.deb" './usr/bin/fly-recovery'
pkg_has ".packages/flyos-recovery_${VERSION}_all.deb" './usr/lib/flyos/fly-offline-update-helper'
pkg_has ".packages/flyos-recovery_${VERSION}_all.deb" './usr/lib/systemd/system/flyos-offline-update.service'
pkg_has ".packages/flyos-privacy_${VERSION}_all.deb" './usr/lib/flyos/fly-privacy-monitor'
pkg_has ".packages/flyos-performance_${VERSION}_all.deb" './usr/lib/flyos/fly-performance-monitor'
pkg_has ".packages/flyos-performance_${VERSION}_all.deb" './usr/bin/fly-activity'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-storage'
pkg_has ".packages/flyos-wine_${VERSION}_all.deb" './usr/bin/fly-wine-run'
pkg_has ".packages/flyos-branding_${VERSION}_all.deb" './usr/share/sddm/themes/flyos/Main.qml'
pkg_has ".packages/flyos-core_${VERSION}_all.deb" './usr/lib/systemd/system/flyos-identity.service'

# No generated bytecode in any package and no payload file owned by two Fly packages.
python3 - "$VERSION" <<'PY'
from pathlib import Path
import subprocess, sys
version=sys.argv[1]
seen={}
for deb in sorted(Path('.packages').glob(f'flyos-*_{version}_all.deb')):
    out=subprocess.check_output(['dpkg-deb','--fsys-tarfile',str(deb)])
    # tar bytes are intentionally not parsed here; use dpkg-deb -c for portable text paths.
    listing=subprocess.check_output(['dpkg-deb','-c',str(deb)], text=True)
    if '__pycache__' in listing or '.pyc' in listing:
        raise SystemExit(f'bytecode leaked into {deb}')
    for line in listing.splitlines():
        parts=line.split(maxsplit=5)
        if len(parts)<6: continue
        path=parts[-1]
        if path.endswith('/'): continue
        if path in seen:
            raise SystemExit(f'duplicate payload ownership: {path}: {seen[path]} and {deb.name}')
        seen[path]=deb.name
print(f'modular ownership: {len(seen)} files')
PY


# Offline updates must follow the systemd marker model and remove the marker
# before applying packages to avoid boot loops.
grep -q 'remove_marker' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
grep -q -- '--no-download full-upgrade' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
test -L packages/flyos-base/rootfs/usr/lib/systemd/system/system-update.target.wants/flyos-offline-update.service

# Accessibility controls are Fly-native rather than hard-wired to transparency.
grep -q 'def textScale' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'highContrast' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml

# QML regression guard for a removed, unregistered image provider.
! grep -q 'image://icon/' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
if command -v qmlformat >/dev/null 2>&1; then
  qmlformat -n packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml >/dev/null
fi

grep -q '^CONFIG_NTSYNC=m' kernel/flykernel.fragment
grep -q '^CONFIG_SECURITY_LANDLOCK=y' kernel/flykernel.fragment
grep -q '^CONFIG_SCHED_CLASS_EXT=y' kernel/flykernel.fragment

echo 'Fly OS smoke test: OK'

# Alpha3 integration regressions: Fly owns notifications and keeps a rescue UI.
grep -q 'org.freedesktop.Notifications' packages/flyos-base/rootfs/usr/lib/flyos/fly-notifications
grep -q 'id: notificationCenter' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q 'OnFailure=fly-rescue-ui.service' packages/flyos-base/rootfs/usr/lib/systemd/user/fly-shell.service
grep -q 'fly-rescue-ui.py' build/build-packages.py
! grep -q 'swaync-client' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
! grep -q 'sway-notification-center' packages/components/flyos-shell.control

# App installation stays inside the Fly UI instead of spawning a terminal.
grep -q 'QProcess' packages/flyos-base/rootfs/usr/lib/flyos/fly-apps.py
! grep -q 'konsole.*apt-get' packages/flyos-base/rootfs/usr/lib/flyos/fly-apps.py

# Offline update integrity is verified before dpkg is touched.
grep -q 'sha256sum -c' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
grep -q 'verify_payload' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
grep -q 'flock -n' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper

# Privacy and adaptive-power regression guards.
grep -q 'DB.chmod(0o600)' packages/flyos-base/rootfs/usr/bin/fly-indexer
grep -q 'CACHE.chmod(0o700)' packages/flyos-base/rootfs/usr/bin/fly-indexer
grep -q 'tmp.chmod(0o600)' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'fly-power-auto.timer' packages/flyos-base/rootfs/usr/lib/systemd/user/flyos-session.target
grep -q '^  auto)' packages/flyos-base/rootfs/usr/bin/fly-profile
grep -q '^  refresh)' packages/flyos-base/rootfs/usr/bin/fly-profile

# Alpha4 interaction + transaction safety regressions.
grep -q '\["actions", "body", "persistence"\]' packages/flyos-base/rootfs/usr/lib/flyos/fly-notifications
grep -q 'ActionInvoked' packages/flyos-base/rootfs/usr/lib/flyos/fly-notifications
grep -q 'def notificationAction' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'fly.notificationAction' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q 'def setAudioOutput' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'text: "Saída de áudio"' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q 'cmd == "reset"' packages/flyos-base/rootfs/usr/bin/fly-shellctl
grep -q 'Restaurar configurações do Fly Shell' packages/flyos-base/rootfs/usr/lib/flyos/fly-rescue-ui.py
grep -q 'TRANSACTION=' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
grep -q 'cmp -s "$TRANSACTION"' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
grep -q 'dpkg --audit' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
grep -q 'APT dependency check failed' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper
grep -q 'resolver requested removal of a protected system package' packages/flyos-base/rootfs/usr/lib/flyos/fly-offline-update-helper

# Alpha5 native-integration regressions.
grep -q 'settings-reload' packages/flyos-base/rootfs/usr/bin/fly-shellctl
grep -q 'def reloadSettings' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'toggleEffect' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'def switchWorkspace' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'def toggleNightLight' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'def toggleMicrophoneMute' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'Área de trabalho.*fly.currentDesktop' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q 'fly.toggleNightLight' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q 'fly.toggleMicrophoneMute' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q '^Exec=fly-shellctl notifications$' packages/flyos-base/rootfs/usr/share/applications/fly-notification-center.desktop
! grep -Rq 'swaync-client' packages/flyos-base/rootfs config packages/components build/build-packages.py
! grep -Rq '^sway-notification-center$' config
! test -d packages/flyos-base/rootfs/etc/xdg/swaync
! grep -q 'qdbus-qt6' packages/components/flyos-shell.control
# Fly-owned app/update surfaces are primary; legacy desktop catalogs stay optional.
! grep -q '^plasma-discover' config/minimal-packages.txt
! grep -q '^plasma-discover' config/packages.txt
grep -q 'Suggests:.*plasma-discover' packages/components/flyos-center.control


# 0.8 performance/integration regressions.
grep -q 'fly-performance-monitor.service' packages/flyos-base/rootfs/usr/lib/systemd/user/flyos-session.target
grep -q 'QFileSystemWatcher' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'self.slow_timer.start(12000)' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'self.interactive_timer.start(4500)' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'def update_polling_policy' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'os.replace(self.command_file, processing)' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'def calculate_expression' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'def setAudioInput' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'text: "Entrada de áudio"' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q 'fly.runAction("activity")' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
grep -q 'adaptive_performance' packages/flyos-base/rootfs/usr/lib/flyos/fly-center.py
grep -q 'def nm_wifi_networks' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'def nm_hotspot' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-login-items'
grep -q 'X-FlyOS-DisableOverride' packages/flyos-base/rootfs/usr/bin/fly-login-items

# 0.9 hardware/product integration regressions.
grep -q 'def refresh_interactive' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'old_status = (' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'fly-bluetooth' packages/flyos-base/rootfs/usr/lib/flyos/fly-center.py
grep -q 'fly-battery-dashboard' packages/flyos-base/rootfs/usr/lib/flyos/fly-center.py
grep -q 'fly-gpu' packages/flyos-base/rootfs/usr/lib/flyos/fly-center.py
grep -q 'fly-support-report' packages/flyos-base/rootfs/usr/lib/flyos/fly-center.py
grep -q 'Mode Timings' packages/flyos-base/rootfs/usr/bin/fly-nightlight
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-bluetooth'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-battery-dashboard'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-gpu-run'
pkg_has ".packages/flyos-shell_${VERSION}_all.deb" './usr/bin/fly-nightlight'
pkg_has ".packages/flyos-core_${VERSION}_all.deb" './usr/bin/fly-support-report'
grep -q '^upower$' config/minimal-packages.txt
grep -q '^switcheroo-control$' config/minimal-packages.txt
grep -q 'zip -qry' build/release-bundle.sh


# 0.10 reliability/power regressions.
grep -q 'SCHEMA_VERSION = 2' packages/flyos-base/rootfs/usr/lib/flyos/flyconfig.py
grep -q 'ConditionFileIsExecutable=/usr/bin/swayidle' packages/flyos-base/rootfs/usr/lib/systemd/user/fly-idle.service
grep -q '_schedule_expiration' packages/flyos-base/rootfs/usr/lib/flyos/fly-notifications
grep -q 'NotificationClosed(dbus.UInt32(ident), dbus.UInt32(1))' packages/flyos-base/rootfs/usr/lib/flyos/fly-notifications
grep -q 'fly-airplane.service' packages/flyos-base/rootfs/usr/lib/systemd/user/flyos-session.target
grep -q 'fly-battery-watch.service' packages/flyos-base/rootfs/usr/lib/systemd/user/flyos-session.target
grep -q 'def should_defer' packages/flyos-base/rootfs/usr/bin/fly-indexer
grep -q 'LOCK_EX | fcntl.LOCK_NB' packages/flyos-base/rootfs/usr/bin/fly-indexer
grep -q 'def toggleAirplane' packages/flyos-base/rootfs/usr/lib/flyos/fly-shell.py
grep -q 'fly.airplaneMode' packages/flyos-base/rootfs/usr/share/flyos/shell/Main.qml
pkg_has ".packages/flyos-core_${VERSION}_all.deb" './usr/bin/fly-airplane'
pkg_has ".packages/flyos-core_${VERSION}_all.deb" './usr/lib/flyos/flyconfig.py'
pkg_has ".packages/flyos-shell_${VERSION}_all.deb" './usr/lib/systemd/user/fly-battery-watch.service'
grep -q 'def launch' packages/flyos-base/rootfs/usr/lib/flyos/fly-center.py
grep -q '^Exec=fly-center$' packages/flyos-base/rootfs/usr/share/applications/fly-center.desktop


# 0.11 platform-independence/repository regressions.
pkg_has ".packages/flyos-repo_${VERSION}_all.deb" './etc/apt/sources.list.d/flyos.sources'
pkg_has ".packages/flyos-repo_${VERSION}_all.deb" './usr/share/keyrings/flyos-archive-keyring.gpg'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-files'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-audio'
pkg_has ".packages/flyos-center_${VERSION}_all.deb" './usr/bin/fly-firewall'
pkg_has ".packages/flyos-recovery_${VERSION}_all.deb" './usr/bin/fly-recovery-ui'
grep -q 'def nm_wifi_networks' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'def bluez_devices' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'def media_state' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'def set_brightness_percent' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'org.freedesktop.portal.Screenshot' packages/flyos-base/rootfs/usr/bin/fly-screenshot
grep -q 'fly-package-helper' packages/flyos-base/rootfs/usr/lib/flyos/fly-apps.py
grep -q 'fly-recovery-helper' packages/flyos-base/rootfs/usr/lib/flyos/fly-recovery-ui.py
grep -q 'fly-firewall-helper' packages/flyos-base/rootfs/usr/lib/flyos/fly-firewall.py
! grep -REq 'nmcli|bluetoothctl|playerctl|pactl|brightnessctl|wl-copy|wl-paste|notify-send|pkcon' packages/flyos-base/rootfs/usr/lib/flyos packages/flyos-base/rootfs/usr/bin/fly-airplane packages/flyos-base/rootfs/usr/bin/fly-media packages/flyos-base/rootfs/usr/bin/fly-brightness
! grep -qxE '(qdbus-qt6|brightnessctl|wl-clipboard|playerctl|dolphin|spectacle|systemsettings|packagekit-tools|pavucontrol)' config/minimal-packages.txt
# An amd64 client index must contain Architecture: all Fly packages.
FLYOS_CHANNEL=dev ./build/build-apt-repo.sh >/dev/null
grep -q '^Package: flyos-core$' dist/apt-repo/dists/dev/main/binary-amd64/Packages
# 0.11 semantic integration guards.
grep -q 'return True, getattr(dbus.Interface' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'ok, _value = kwin_call' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q 'def _preferred_mpris_player' packages/flyos-base/rootfs/usr/lib/flyos/flyplatform.py
grep -q "cmd=\['apt-get','install','-y','--no-install-recommends','--',pkg\]" packages/flyos-base/rootfs/usr/lib/flyos/fly-package-helper

# Repository package channel follows release maturity unless explicitly overridden.
EXPECTED_CHANNEL="${FLYOS_DEFAULT_CHANNEL:-}"
if [[ -z "$EXPECTED_CHANNEL" ]]; then
  case "${VERSION,,}" in
    *dev*|*alpha*) EXPECTED_CHANNEL=dev ;;
    *beta*|*rc*) EXPECTED_CHANNEL=beta ;;
    *) EXPECTED_CHANNEL=stable ;;
  esac
fi
rm -rf .build/repo-channel-check
mkdir -p .build/repo-channel-check
dpkg-deb -x ".packages/flyos-repo_${VERSION}_all.deb" .build/repo-channel-check
grep -q "^Suites: ${EXPECTED_CHANNEL}$" .build/repo-channel-check/etc/apt/sources.list.d/flyos.sources
grep -q '^Valid-Until:' dist/apt-repo/dists/dev/Release
grep -q '^Acquire-By-Hash: yes$' dist/apt-repo/dists/dev/Release
test -n "$(find dist/apt-repo/dists/dev/main/binary-amd64/by-hash/SHA256 -type f -print -quit)"
