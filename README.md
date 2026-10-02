# Fly OS 0.11 Developer Alpha

Fly OS is an open-source desktop operating-system project focused on a coherent, fast and recoverable desktop experience. It uses Ubuntu 26.04 LTS archives as a **compatibility, security and hardware-enablement substrate**, while the session, shell, settings, update/recovery flow, Windows integration and visual identity are Fly-owned.

The native desktop is **KWin Wayland + Fly Session + Fly Shell**. `plasmashell` is not required to start Fly OS; a Plasma session can still be installed as a fallback.

> **Alpha status:** 0.11.0-dev is for development/testing. Do not treat it as a production OS until installation, upgrade, Secure Boot, suspend/resume, recovery and the hardware matrix in `docs/RELEASE_CHECKLIST.md` pass on real machines.

## Design principles

Fly OS borrows product principles—not proprietary Apple code or assets:

- one primary settings surface and predictable placement of controls;
- strong defaults with advanced controls available on demand;
- blur/transparency that backs off for power saving, accessibility and Safe UI mode;
- local-first search and no Fly-owned telemetry by default;
- recovery before risky system changes;
- Windows apps integrated into the same launcher/search model as Linux apps;
- workload-aware performance instead of permanent benchmark tweaks;
- mature upstream infrastructure is reused where a Fly fork would reduce reliability.



## 0.11 highlights — Fly Platform and dependency reduction

- **Fly Platform** (`flyplatform.py`) centralizes KWin, NetworkManager, BlueZ, MPRIS, logind brightness and WirePlumber integration so Fly apps stop spawning separate compatibility CLIs for common desktop actions.
- Fly Shell no longer requires `qdbus-qt6`, `brightnessctl`, `playerctl`, `wl-clipboard`, `pulseaudio-utils`, `libnotify-bin` or Spectacle for its core experience.
- **Fly Connect** uses NetworkManager D-Bus directly for Wi-Fi discovery/activation and WPA hotspot creation; **Fly Bluetooth** uses BlueZ ObjectManager/Device1 APIs directly.
- **Fly Media** talks to MPRIS directly; brightness is mediated by systemd-logind; screenshots use the XDG Desktop Portal; Fly notifications use `org.freedesktop.Notifications` directly.
- Clipboard history is captured by the persistent Qt/Wayland Fly Shell when enabled, removing the separate `wl-paste --watch` process.
- **Fly Audio** provides the common output/input/volume/mute surface using WirePlumber, so `pavucontrol` is no longer a base-image dependency.
- **Fly Files** covers common file-manager tasks (Home/folders/open/create/rename/trash), allowing Dolphin to remain optional rather than required by Fly Base.
- Fly Apps replaces PackageKit/pkcon with a narrow PolicyKit-authenticated Fly APT helper that accepts only install/remove of canonical package names.
- **Fly Recovery UI** and **Fly Firewall** replace terminal/System Settings entry points for routine recovery and UFW control, backed by command-specific privileged helpers.
- New **`flyos-repo` package** installs a deb822 source, archive public key and `fly-repo` channel selector for `dev`, `beta` and `stable`.
- The APT builder now ensures `binary-amd64/Packages` includes `Architecture: all` Fly packages and supports signed `Release.gpg`/`InRelease` publication.
- A GitHub Actions APT publisher is included for an `apt` branch; it requires signing-key secrets and never stores the private key in the repository.

The Fly Base package list no longer includes Dolphin, Spectacle, System Settings, PackageKit tools, pavucontrol, qdbus, brightnessctl, playerctl or wl-clipboard as mandatory desktop dependencies. Mature hardware/system services such as KWin, NetworkManager, BlueZ, PipeWire/WirePlumber and systemd remain upstream by design.


## 0.10 highlights

- **shared Fly settings schema** (`flyconfig`) now validates and writes shell/center preferences atomically with per-user locks, private permissions and forward-compatible preservation of unknown keys;
- **Fly Airplane Mode** remembers which Wi-Fi/WWAN/Bluetooth radios were enabled, disables them together and restores only the prior radio state when leaving airplane mode;
- **native low-battery safety alerts** warn at 20%, 10% and 5% without depending on a Plasma/PowerDevil session; critical alerts can bypass Do Not Disturb;
- **battery/pressure-aware Fly Search indexing** skips background scans on low battery or under recent memory/I/O pressure and uses a non-blocking process lock to prevent duplicate crawls;
- notification expiration now follows the freedesktop timeout contract, including persistent, server-policy and explicit millisecond timeouts plus correct close reasons;
- fixed a real session bug where the Fly Center was referenced as `fly-center` but no stable `/usr/bin/fly-center` launcher existed; GUI-to-GUI actions now detach instead of freezing Fly Center until the child app exits;
- fixed the invalid systemd `ConditionPathIsExecutable=` directive in the idle service and added unit syntax regression checks;
- Fly Shell polling is now adaptive: slower while idle, faster while Quick Settings is open, and status signals are emitted only when tracked state changed;
- the privacy monitor sleeps until its next real microphone/camera/device deadline instead of waking twice per second;
- power-profile state writes are atomic/private, and airplane-mode reconciliation no longer tries to order a user service against the system NetworkManager service.

## 0.9 highlights

- **Fly Bluetooth** is now a dedicated native device manager over BlueZ: power, discovery, pair/connect/disconnect, trust and removal are integrated without requiring Blueman for common flows. Discovery is asynchronous so the UI does not freeze during scanning.
- **Fly Battery** adds a battery dashboard based on UPower/sysfs with charge state, energy rate, remaining time, cycle count and health estimate when the firmware exposes reliable design/full capacity data. Battery Care exposes 80%/100% charge limits only on supported hardware.
- **Fly GPU** integrates `switcheroo-control` for hybrid-graphics notebooks. Apps can be launched on a discrete GPU without forcing the whole session into a high-power GPU mode; `fly-gpu-run` provides the same flow from the terminal.
- **Night Light scheduling** now exposes a location-free fixed schedule and configurable color temperature using KWin's own Night Color implementation.
- **privacy-aware support reports** can be generated locally with `fly-support-report`; home paths, hostname, IPv4 addresses and MAC addresses are redacted best-effort and the user is told to review the archive before sharing.
- Fly Shell no longer emits status-change signals every polling cycle when interactive/hardware state is unchanged, reducing unnecessary QML repaint work while idle.
- Fly Center now links Bluetooth, battery, hybrid GPU and support-report tools directly into the existing Devices/System/Energy surfaces rather than presenting them as disconnected utilities.

## 0.8 highlights

- new `flyos-performance` package with a low-overhead procfs/PSI monitor and **Fly Activity** for CPU, RAM, swap, disk and per-user process activity;
- Fly Shell status collection is split into clock/interactive/slow cadences instead of spawning every hardware utility every ~1.8 seconds;
- shell command delivery is event-driven through `QFileSystemWatcher`, with an atomic rename before queue processing to prevent commands being lost during concurrent writes;
- adaptive effects use real memory PSI/resource pressure and remain visual-only: Fly OS does not force a kernel scheduler, kill policy or governor;
- **Fly Storage** adds safe cleanup for Trash, thumbnails and Fly cache plus an explicit privileged APT-cache action; personal folders are never selected for cleanup;
- **Itens de Inicialização** manages XDG autostart entries with per-user overrides, never editing packaged `/etc/xdg/autostart` files;
- Quick Settings can switch both audio **output and input** and move existing PipeWire/Pulse streams best-effort;
- Fly Search includes a bounded offline calculator, local app-frequency/recency ranking and keeps usage metadata private under the user state directory;
- privacy-camera scanning now uses a slower cadence than microphone state to reduce `/proc` traversal wakeups;
- Fly Connect correctly handles NetworkManager escaped SSIDs such as names containing colons and adds an integrated, reversible WPA hotspot flow.

## 0.7 highlights

- dedicated `flyos-privacy` package with local camera/microphone indicators and no persistent activity log by default;
- Focus Mode integrated into Fly Shell and Fly Center;
- Fly Defaults for XDG-compatible default applications;
- atomic, locked settings writes to prevent corruption when multiple Fly components change preferences;
- privacy state is shown directly in the top bar and Quick Settings;
- KWin remains responsible for HDR/ICC, fractional scaling and Wayland session infrastructure while Fly owns the user-facing shell; optional compositor features are feature-detected instead of assumed.

## 0.6 highlights

### Modular Fly platform

0.6 no longer ships the entire platform as one monolithic Debian payload. `make package` builds:

- `flyos-core` — identity, security defaults, diagnostics, power/tuning and common helpers;
- `flyos-shell` — native Wayland session, Fly Shell, multimedia keys, OSD and session services;
- `flyos-center` — Fly Center, Fly Apps, Fly Connect and onboarding;
- `flyos-search` — private local filename/path index and search tooling;
- `flyos-update` — update discovery and user-facing staging;
- `flyos-recovery` — snapshots, repair, backup entry points and the offline-update engine;
- `flyos-privacy` — camera/microphone indicators and privacy dashboard with session-local state;
- `flyos-performance` — local PSI/procfs resource state and Fly Activity;
- `flyos-wine` — Windows/Wine integration and isolated prefix helpers;
- `flyos-branding` — SDDM, Plymouth, Calamares, icons, colors and wallpaper;
- `flyos-repo` — signed Fly OS APT source, archive key and release-channel selector;
- `flyos-base` — small metapackage that installs the complete set above.

The package builder verifies that each installed payload file has exactly one owner. Components can therefore evolve independently while keeping one coordinated version for alpha releases.

### Fly Shell 0.6

Fly Shell owns:

- desktop/wallpaper surfaces on every monitor;
- top bar and centered dock;
- universal launcher/search for apps, local files and Fly actions;
- quick settings for Wi-Fi, Bluetooth, volume, audio input/output switching, brightness, resource pressure and power profiles;
- media controls through MPRIS/playerctl;
- Fly-owned volume/brightness OSD;
- global multimedia/brightness shortcuts without requiring PowerDevil;
- Fly-native freedesktop notification daemon, toast history panel and Do Not Disturb;
- power/session controls;
- reduced-effects behavior and `Fly OS (Safe UI)` login session;
- independent reduced-motion, reduced-transparency, high-contrast and Fly text-scale controls;
- camera/microphone privacy indicators with local app attribution when exposed by the Linux media stack, plus prepared-update state in the top bar.

Rapid shortcut commands now use a per-user append queue instead of a single overwritten command file, preventing lost actions when shortcuts are pressed quickly.

If Fly Shell reaches its restart limit, a minimal Qt-based **Fly Rescue UI** is launched automatically so the user can restart the shell in Safe UI mode, restore Fly Shell settings from a safe default while preserving a timestamped backup, open diagnostics/settings or log out without a working QML shell.

Fly services also use workload-aware systemd user slices: interactive shell work receives a higher relative CPU/I/O weight while indexing and background maintenance yield under contention. This does not force a global CPU governor or experimental scheduler.

### Fly Search

`fly-indexer` builds a local SQLite FTS index of **names and paths only** from standard user folders. File content is not indexed and queries are not uploaded. App launchers, Wine-generated shortcuts, Fly actions and local files are merged into one search surface. 0.8 also adds a bounded arithmetic calculator and local recency/frequency ranking for applications; usage data stays in the user's private state directory.

### Fly Center

Fly Center is the primary settings surface. Fly Connect now includes a native Wi-Fi and Bluetooth device view over NetworkManager/BlueZ instead of requiring a separate Bluetooth manager for common operations. 0.6 groups appearance, energy, system maintenance, devices, privacy, gaming, Windows compatibility, backup/recovery and About in one app. The Devices page exposes network, PipeWire volume and common display/input paths; deep hardware settings can still delegate to KScreen/KDE modules where those are the mature hardware interface.

### Fly Apps

Fly Apps searches Ubuntu-compatible APT repositories directly and installs/removes packages inside the Fly UI using PackageKit/PolicyKit (or a privileged APT fallback), without opening a terminal. When Flatpak is installed, Flatpak search results appear as a separate source. Flathub remains opt-in. Discover stays optional as an advanced catalog.

### Fly Update and Recovery

System package updates use a staged offline flow. The normal session first verifies that dpkg/APT are healthy, resolves and records both the human-readable APT plan and an exact `Inst`/`Remv` transaction lock, rejects removal of protected Fly/session substrate packages, clears stale archives, downloads the transaction, hashes every staged `.deb`, and re-checks the exact resolver output before scheduling `/system-update`. On the next boot, `flyos-offline-update.service` verifies both hashes and the locked transaction before `dpkg` is touched; the marker is removed before package installation to prevent boot loops. Btrfs/Snapper systems get a best-effort pre-update snapshot. See `docs/OFFLINE_UPDATES.md`.

Flatpak apps remain user-session updates and firmware stays a separate fwupd flow because its reboot/staging rules vary by device. `fly-recovery` exposes the offline-update state/log alongside package repair, initramfs/GRUB regeneration, snapshots, shell reset and service logs. Snapshots are system recovery, not personal-file backup. Kup/bup/rsync remain separate backup options.

### Security and privacy

- AppArmor and UFW remain part of the platform;
- unattended security updates remain supported;
- PolicyKit agent is started in the native session;
- KScreenLocker/PAM is reused for locking under KWin, with duplicate lock launches prevented by a per-session lock;
- idle lock is delegated through `fly-lock`;
- clipboard history is off by default and, when enabled, is session-only under `$XDG_RUNTIME_DIR`;
- Fly Search stays local-first;
- no Fly-owned telemetry is enabled by default;
- Flatpak/Flathub is not silently enabled.

### Performance policy

- zram through `systemd-zram-generator`;
- PSI/systemd-oomd infrastructure without aggressive Fly-specific kill thresholds;
- `power-profiles-daemon` coordinated by `fly-profile`;
- GameMode/Gamescope/MangoHud are scoped to games rather than permanent system tweaks;
- Battery Care writes only hardware-exposed charge-threshold interfaces;
- optional `amd64v3` path only after CPU capability checks;
- FlyKernel remains experimental and separate from the default signed Ubuntu-compatible kernel path.
- `fly-performance-monitor` reads procfs/sysfs/PSI directly and writes only session-local runtime state; the shell can reduce visual effects during real pressure without changing system scheduling policy.
- monitoring cadences are staggered so idle desktops do not continuously spawn NetworkManager, BlueZ, PipeWire and KWin helper commands.

## Build

### Packages + QA

```bash
make package
make lint
make release-bundle
make sbom
```

Release bundles include an SPDX 2.3 JSON SBOM for Fly-owned files/components. Generated packages are placed in `.packages/` and release artifacts in `dist/release-<version>/`.

### Compatibility/remaster ISO

```bash
sudo apt update
make deps
make package
make iso
```

### Fly Base ISO

Fly Base starts from an Ubuntu 26.04 minimal `debootstrap` rootfs and installs the modular Fly packages without pulling Plasma Workspace by default:

```bash
sudo apt update
make deps
make package
make iso-flybase
```

Optional Plasma fallback inside the Fly Base image:

```bash
sudo FLYOS_INCLUDE_PLASMA_FALLBACK=1 ./build/build-flybase-iso.sh
```

The Fly Base builder is still a developer pipeline. Its current media is **not** the final signed Secure-Boot/shim publication path.

## Useful commands

```bash
flyctl status
fly-center
fly-shellctl launcher
fly-shellctl quick
fly-health
fly-activity
fly-storage
fly-doctor
fly-profile auto
fly-indexer
fly-search relatório
fly-apps
fly-update gui
fly-update prepare
fly-update status
fly-snapshot status
fly-recovery
fly-wine
fly-channel get
```

## Repository layout

- `packages/flyos-base/rootfs/` — reviewed Fly-owned rootfs payload source;
- `packages/components/` — Debian metadata/maintainer scripts for modular packages;
- `build/` — package, ISO, Fly Base, release and APT repository builders;
- `kernel/` — optional FlyKernel experiments;
- `patches/` — isolated upstream patch experiments;
- `config/` — package lists and image configuration;
- `docs/` — architecture, packaging, security, UX, offline-update design, SBOM, requirements and release gates;
- `.github/` — CI, release workflows and contribution templates.

## Project status

Fly OS is **not yet a 1.0 stable distribution**. The architecture, packages and developer image builders exist, but stable status requires real hardware validation, signed release boot media, installer/upgrade/recovery testing and a maintained package-signing/update infrastructure. See `docs/ROADMAP.md` and `docs/RELEASE_CHECKLIST.md`.

Fly OS project-specific code is GPL-3.0-or-later unless stated otherwise. Third-party components keep their original licenses; see `THIRD_PARTY.md`.


## Dependency boundary

The maintained boundary between Fly-owned product code and upstream Linux infrastructure is documented in [`docs/DEPENDENCY_BOUNDARY.md`](docs/DEPENDENCY_BOUNDARY.md). Fly OS reduces UX/coordination dependencies without forking security-critical hardware stacks merely for branding.

