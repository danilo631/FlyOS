# Fly OS 0.6 Alpha 5

Fly OS is an open-source desktop operating-system project focused on a coherent, fast and recoverable desktop experience. It uses Ubuntu 26.04 LTS archives as a **compatibility, security and hardware-enablement substrate**, while the session, shell, settings, update/recovery flow, Windows integration and visual identity are Fly-owned.

The native desktop is **KWin Wayland + Fly Session + Fly Shell**. `plasmashell` is not required to start Fly OS; a Plasma session can still be installed as a fallback.

> **Alpha status:** 0.6.0-alpha5 is for development/testing. Do not treat it as a production OS until installation, upgrade, Secure Boot, suspend/resume, recovery and the hardware matrix in `docs/RELEASE_CHECKLIST.md` pass on real machines.

## 0.6 highlights

- modular Debian packages: core, shell, center, search, update, recovery, Wine, branding and a base metapackage;
- native Fly Shell on KWin/Wayland with top bar, dock, launcher, Quick Settings, audio-output switching, media controls, OSD and Fly-native notifications;
- Fly Search with a local SQLite FTS filename/path index and no content upload;
- Fly Apps with APT/PackageKit and optional Flatpak support;
- staged offline system updates with transaction locking, cached-package hashes, systemd `system-update.target` and optional Btrfs/Snapper pre-update snapshots;
- Fly Rescue UI when the shell reaches its restart limit;
- Safe UI login mode with reduced motion/transparency;
- zram, workload-aware systemd user slices, power profiles and scoped gaming optimizations;
- AppArmor/UFW/PolicyKit/KScreenLocker reuse for security without reimplementing mature upstream infrastructure;
- Wine integration so Windows shortcuts appear in the same launcher/search model;
- no Fly-owned telemetry by default.

## Latest alpha5 fixes

- robust PipeWire/Pulse audio output switching: stale sinks are rejected and the current default is tracked in Quick Settings;
- Quick Settings now surfaces prepared offline updates, failed-update state and recovery/snapshot availability;
- multimedia and brightness shortcuts work without requiring PowerDevil;
- rapid shell commands use an append queue instead of a single overwritten command file;
- the native session no longer registers Fly services into unrelated desktop sessions;
- package QA verifies unique payload ownership across all Fly Debian packages.

## Build and QA

```bash
make package
make lint
make release-bundle
make sbom
```

Fly Base ISO:

```bash
sudo apt update
make deps
make package
make iso-flybase
```

The Fly Base builder starts from an Ubuntu 26.04 minimal rootfs and does not pull Plasma Workspace by default. It remains a developer pipeline until signed boot media and real-hardware install/upgrade/recovery testing are complete.

## Architecture

```text
Linux kernel / hardware enablement
        ↓
systemd + Mesa + NetworkManager + PipeWire
        ↓
KWin / Wayland
        ↓
Fly Session
        ↓
Fly Shell
 ├─ Fly Search
 ├─ Fly Connect
 ├─ Fly Center
 ├─ Fly Apps
 ├─ Fly Update
 ├─ Fly Recovery
 └─ Fly Wine
```

Fly OS owns the product layer while reusing mature upstream infrastructure where a private fork would reduce stability and security.

## Status

Fly OS is **not yet 1.0 stable**. Stable status requires signed release boot media, installer/upgrade/recovery validation and a real hardware matrix.

Fly OS project-specific code is GPL-3.0-or-later unless stated otherwise.
