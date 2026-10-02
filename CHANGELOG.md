# Changelog

## 0.11.0-dev — Fly Platform / Repository Preview

### Added
- shared `flyplatform` API for KWin, MPRIS, NetworkManager, BlueZ, systemd-logind brightness and WirePlumber integration;
- Fly Files, Fly Audio, Fly Firewall and graphical Fly Recovery surfaces;
- narrow privileged Fly helpers for APT install/remove, firewall and recovery instead of generic root command execution;
- `flyos-repo` package with deb822 source, Ed25519 public archive key and `fly-repo` dev/beta/stable channel selection;
- signed APT-repository build path plus GitHub Actions publisher for an `apt` branch;
- XDG Desktop Portal screenshot helper and direct Fly notification client.

### Changed
- Wi-Fi/hotspot uses NetworkManager D-Bus instead of `nmcli`; Bluetooth uses BlueZ D-Bus instead of `bluetoothctl`; media uses MPRIS instead of `playerctl`;
- shell brightness uses logind/sysfs instead of `brightnessctl`; common audio uses WirePlumber instead of pactl/pavucontrol;
- clipboard history is captured by Fly Shell rather than a `wl-paste` watcher;
- PackageKit, Dolphin, Spectacle, System Settings, pavucontrol, qdbus, playerctl, brightnessctl and wl-clipboard are removed from the Fly Base mandatory package set;
- APT amd64 index generation now includes architecture-independent Fly packages;
- the `flyos-repo` package derives its default dev/beta/stable suite from release maturity, with an explicit build override for publication workflows;
- APT Release metadata now carries `Valid-Until` and `Acquire-By-Hash`, with SHA-256 by-hash indexes.

### Fixed
- KWin D-Bus methods that successfully return `void` are no longer misreported as failed actions by Fly Platform;
- MPRIS actions prefer the actively playing/paused player instead of whichever service name sorts first;
- Fly Recovery settings backups use unique timestamps instead of a single collision-prone backup name.

### Security
- Fly APT/recovery/firewall helpers validate a small fixed command grammar and are not generic root shells;
- the repository ships only the archive public key; private signing material stays external;
- APT publication requires a signed InRelease before the GitHub workflow publishes a channel.

### Known limitations
- the included archive key is a development key and should be rotated to an offline production signing key before 1.0;
- complex Bluetooth pairing/passkey flows still depend on a capable BlueZ session agent and need real-hardware validation;
- Fly Files intentionally implements common local-file tasks, not every advanced Dolphin/KIO workflow;
- Secure Boot release signing and the complete real-hardware matrix remain unfinished.

All notable Fly OS changes are tracked here.

## 0.10.0-dev — Reliability, Power and Session Audit

### Added
- Fly Airplane Mode with remembered Wi-Fi/WWAN/Bluetooth restore state and login-time reconciliation.
- native low-battery notifications for the Fly session at 20%, 10% and 5%, with critical warnings allowed through Do Not Disturb.
- shared `flyconfig` schema/atomic settings helper used by Fly Shell and Fly Center.
- battery/PSI-aware index deferral and non-blocking indexer locking.
- systemd unit syntax regression checks in the smoke-test suite.

### Changed
- Fly Shell uses adaptive polling cadences and accelerates interactive state only while Quick Settings is visible.
- privacy monitoring sleeps until the next actual microphone/camera/device probe deadline instead of spinning at a fixed 500 ms cadence.
- Fly Center launches long-running GUI tools detached, so opening Update, Storage, Bluetooth, GPU, system settings or other Fly utilities does not freeze the parent window.
- power-profile state is written atomically with private user permissions.
- notification timeout handling follows freedesktop server-policy/persistent/explicit-timeout semantics.

### Fixed
- added the missing `/usr/bin/fly-center` launcher used throughout Fly Shell and desktop entries.
- replaced invalid `ConditionPathIsExecutable=` with the valid systemd executable-file condition in the idle service.
- close reasons for expired, user-dismissed and API-closed notifications are no longer conflated.
- concurrent shortcut commands are consumed from an atomic queue handoff instead of risking deletion of newly appended commands.
- airplane-mode startup no longer contains a cross-manager ordering dependency on the system NetworkManager unit.

### Known developer limitations
- the native lock/suspend path still requires hostile-path and real-hardware validation before a stable security claim.
- Secure Boot release signing and real-hardware install/upgrade/recovery certification remain incomplete.
- Bluetooth PIN/passkey edge cases and firmware-specific battery charge thresholds still need broad hardware testing.

## 0.9.0-dev — Hardware Integration and Product Polish

### Added
- Fly Bluetooth native manager for BlueZ power, discovery, pairing, connection, trust and removal flows.
- Fly Battery dashboard using UPower/sysfs, including health/cycle information when firmware exposes it and Battery Care shortcuts on supported laptops.
- Fly GPU and `fly-gpu-run` based on switcheroo-control render offload for hybrid graphics.
- configurable location-free KWin Night Light schedule and temperature through `fly-nightlight`.
- privacy-aware `fly-support-report` archive for diagnostics with best-effort redaction before sharing.

### Changed
- Fly Center integrates Bluetooth, battery, GPU and support reporting directly into Devices/Energy/System.
- Bluetooth discovery runs asynchronously instead of blocking the UI for the scan window.
- Fly Shell emits general status changes only when tracked interactive/slow state actually changes, reducing idle QML repaint churn.
- Fly Base explicitly includes UPower, switcheroo-control and pciutils so the native hardware dashboards have a known substrate.

### Fixed
- Night Light configuration no longer needs geolocation for users who prefer fixed schedules.
- hybrid-GPU UX no longer implies a system-wide mux switch; Fly only promises per-application render offload where switcheroo-control detects a discrete GPU.

### Known developer limitations
- advanced Bluetooth PIN/passkey-agent and Bluetooth LE edge cases still require broader hardware certification.
- battery health/charge thresholds are firmware-dependent and intentionally omitted when the kernel does not expose trustworthy values.
- Secure Boot release signing and real-hardware install/upgrade/recovery certification remain incomplete.

## 0.8.0-dev — Adaptive Performance and Daily-Use Tools

### Added
- `flyos-performance`, with a session-local procfs/PSI monitor and Fly Activity GUI for CPU, memory, swap, disk and user processes.
- Fly Storage safe-cleanup UI for Trash, thumbnails, Fly cache and explicit package-cache cleanup.
- integrated Fly Connect hotspot creation/removal over NetworkManager with WPA password validation.
- Fly Login Items for XDG autostart management through safe per-user overrides.
- audio-input switching in Fly Quick Settings, including best-effort migration of active capture streams.
- offline arithmetic results in Fly Search and local application frequency/recency ranking.
- resource-pressure status in Quick Settings/top bar and an opt-out adaptive-performance setting in Fly Center.

### Changed
- Fly Shell status refresh is split into fast clock, interactive and 12-second hardware/update cadences instead of running the full hardware probe every ~1.8 seconds.
- shell command delivery uses `QFileSystemWatcher` plus a slow safety poll rather than polling the command file eight times per second.
- command queues are atomically renamed before processing, preventing a new shortcut command from being deleted while an older batch is being consumed.
- camera FD inspection runs less frequently than microphone state checks to reduce session idle overhead.
- adaptive visual reduction is driven by conservative PSI/memory thresholds and never changes the scheduler/governor by itself.

### Fixed
- NetworkManager SSIDs containing escaped separators such as `:` are parsed correctly in Fly Connect.
- the modular QA now explicitly verifies privacy and performance packages instead of allowing them to escape package-level regression checks.
- calculator copy feedback no longer reuses the volume OSD.

### Known developer limitations
- Fly Base Secure Boot/shim publication and real-hardware certification remain incomplete.
- complex Bluetooth PIN/passkey agent flows still require broader native-session testing.
- KWin capabilities depend on the Ubuntu 26.04 update pocket; Fly OS does not require an unsupported Plasma beta to provide its shell.

## 0.6.0-alpha5 — Native Desktop Integration Alpha

### Added
- workspace navigation and current-workspace status in Fly Quick Settings, using KWin's public D-Bus interface;
- Night Light toggle in Fly Quick Settings using KWin's `NightColor` configuration;
- microphone mute control alongside the existing local microphone-in-use privacy indicator.

### Changed
- Overview now prefers KWin's public `org.kde.kwin.Effects.toggleEffect` D-Bus API and only falls back to KGlobalAccel;
- Fly Center applies preferences through a live shell settings reload instead of restarting Fly Shell;
- removed `sway-notification-center`, its old configuration, and the obsolete `swaync-client` launcher from the native Fly image;
- Discover and its Flatpak/fwupd backends are no longer base-image requirements; Fly Apps/Fly Update are primary and Discover remains an optional advanced catalog;
- reduced the minimal Fly Base package list by dropping legacy `network-manager-gnome`, Blueman and Swaylock defaults where Fly-owned/KScreenLocker paths exist; Blueman remains an optional advanced fallback.

### Fixed
- Focus / Do Not Disturb changes from Fly Center now take effect immediately in Fly Notifications;
- the Fly Notification Center desktop action now opens the Fly-owned notification panel instead of a removed third-party daemon;
- shell settings edited or restored outside Fly Shell are periodically reloaded, preventing stale accessibility/privacy state.

## 0.6.0-alpha4 — Transaction Safety and Interaction Alpha

### Added
- notification action buttons through the standard freedesktop `ActionInvoked` flow; apps can expose actions such as Open/Reply/Mark and Fly Shell renders up to three of them in Notification Center.
- default notification activation from Fly toast cards when the sender provides a `default` action.
- native audio-output switching in Fly Quick Settings using PipeWire's PulseAudio compatibility layer; existing sink streams are moved best-effort to the newly selected output.
- Fly Rescue configuration reset that preserves the previous `settings.json` as a timestamped backup and restarts the shell in Safe UI mode.
- exact APT transaction lock file for offline updates, separate from the human-readable simulation log.

### Changed
- offline updates now compare the resolved `Inst`/`Remv` transaction after download and again at maintenance boot; a transaction that changed since staging is rejected before `dpkg` is touched.
- update staging now runs `dpkg --audit` and `apt-get check` before repository refresh and directs broken package states to Fly Recovery instead of stacking an upgrade on top.
- staging refuses resolver plans that remove core Fly/session/package-management components such as `flyos-*`, `systemd`, `dpkg`, `apt`, NetworkManager, KWin Wayland or SDDM.
- Fly Update details now expose the locked package transaction and install/removal counts alongside the full APT simulation and offline log.

### Fixed
- shell rescue can recover from a corrupt or incompatible per-user Fly settings file without requiring a terminal.
- notification clients that depend on action capability discovery now receive `actions` from `GetCapabilities()`.
- switching the default audio sink now also moves already-running streams instead of affecting only newly started apps.

### Known alpha limitations
- Fly Base Secure Boot release signing/shim publication is not complete.
- notification inline reply semantics depend on each application's freedesktop notification implementation; Fly only dispatches the action key supplied by the application.
- offline APT updates are transaction-locked and recoverable but are not filesystem-atomic on ext4.
- real-hardware installation, suspend/resume, GPU, Bluetooth and recovery certification remains incomplete.

## 0.6.0-alpha3 — Integrated Desktop Alpha

### Added
- Fly-owned `org.freedesktop.Notifications` daemon with session-local history, Fly Shell toast rendering, notification center and Do Not Disturb integration.
- automatic Fly Rescue UI when `fly-shell.service` reaches its crash-loop limit; Safe UI restart, diagnostics, settings and logout remain available without the QML shell.
- native Bluetooth discovery/connect/pair/disconnect flows in Fly Connect over BlueZ, alongside the existing NetworkManager Wi-Fi surface.
- staged-update APT plan, SHA-256 archive manifest and pre-dpkg verification.
- Fly Update details view for transaction plan, snapshot number and offline-update log.

### Changed
- Fly Apps now performs PackageKit/PolicyKit and Flatpak install/remove operations inside its own window with progress/output instead of launching a terminal.
- notification rendering no longer recommends or depends on SwayNotificationCenter in the native session.
- Fly Shell notifications, launcher and Quick Settings are mutually exclusive overlays to reduce accidental stacking and focus conflicts.
- recovery package explicitly uses `flock`/`util-linux` to serialize offline update transactions.

### Fixed
- prepared offline updates now reject missing or modified cached `.deb` files before package installation begins.
- stale APT archives are removed before staging so the integrity manifest represents only the current transaction.
- a repeated Fly Shell failure no longer leaves the user with a compositor-only blank session and no recovery surface.

### Known alpha limitations
- Fly Base Secure Boot release signing/shim publication is not complete.
- native Bluetooth pairing that requires complex PIN/passkey interaction still depends on BlueZ agent capabilities and needs wider hardware testing.
- offline APT updates are recoverable/staged but are not filesystem-atomic on ext4.
- real-hardware install/upgrade/recovery coverage remains incomplete.

## 0.6.0-alpha2 — Reliability and UX Alpha

### Added
- `flyos-search` and `flyos-recovery` as independently updatable Debian components.
- systemd-compatible staged offline APT update engine with pre-download, boot-loop prevention, local status/logging and optional Snapper pre-update snapshot.
- Fly Search command-line query tool (`fly-search`) alongside the private filename indexer.
- independent reduced-motion, reduced-transparency, high-contrast and Fly Shell text-scale accessibility controls.
- top-bar microphone-use indicator when PipeWire/Pulse compatibility exposes active capture streams.
- top-bar indicator when an offline system update is prepared.
- Fly Health checks for TPM presence, conservative block-device encryption detection, offline-update state and failed system services.
- SPDX 2.3 JSON SBOM generation and release-bundle integration.
- foreground/background user slices with conservative cgroup CPU/I/O weights so maintenance and indexing yield to the interactive shell.

### Fixed
- removed `StopWhenUnneeded=yes` from `flyos-session.target`, which could allow systemd to tear down an explicitly started native Fly session.
- corrected modular ownership so Fly Search user services and indexer are actually shipped by `flyos-search`.
- fixed duplicate QML `color` assignment in Quick Settings.
- improved Fly Search keyboard navigation with Up/Down/Enter/Escape behavior and selected-row feedback.
- lock requests are de-duplicated so idle and manual lock events cannot spawn multiple PAM greeters simultaneously.

### Changed
- system package installation is no longer driven from an interactive terminal by the Fly Update GUI.
- update and recovery responsibilities are split: Fly Update owns discovery/staging UX; Fly Recovery owns privileged/offline transactions.
- transparency reduction no longer implicitly disables all animation; reduced motion is now a separate accessibility preference.

### Known alpha limitations
- Fly Base Secure Boot release signing/shim publication is not complete.
- native-session lock behavior still requires full hostile-path and suspend/resume validation before a stable claim.
- real-hardware install/upgrade/recovery coverage remains incomplete.
- advanced display/input configuration continues to reuse KWin/KScreen/KDE modules.

## 0.6.0-alpha1 — Modular Platform Alpha

### Added
- Split Fly OS into `flyos-core`, `flyos-shell`, `flyos-center`, `flyos-update`, `flyos-wine`, `flyos-branding` and the `flyos-base` metapackage.
- Modular package builder with duplicate-ownership regression checks.
- Fly-owned volume/brightness controls and OSD plus multimedia shortcuts independent of PowerDevil.
- MPRIS media controls in Fly Shell quick settings.
- `Fly OS (Safe UI)` Wayland session with reduced effects.
- Direct APT/Flatpak search in Fly Apps; Discover is now an optional advanced catalog.
- Devices section in Fly Center for connectivity, PipeWire volume and display/input entry points.
- Recovery menu for package repair, boot regeneration, Fly Shell reset and service logs.
- Component-status checks in Fly Health/Doctor.

### Fixed
- `flyos-session.target` can no longer be installed into `default.target`, preventing Fly session services from leaking into another desktop.
- Fly Shell shortcut commands are appended to a per-user queue instead of overwriting one command file.
- `fly-idle.service` no longer enters a restart loop when `swayidle` is absent.
- Snapper configuration detection now uses the selected root configuration directly.
- Source/package QA no longer leaves `__pycache__` artifacts in the tree.
- ISO and release builders now install/publish the complete modular package set.

### Changed
- First-login/welcome state moved to the v6 migration marker.
- Fly Apps becomes a first-class package front end for common APT/Flatpak searches.
- Native session handling is more isolated from Plasma fallback behavior.

### Known alpha limitations
- Signed Fly Secure-Boot/shim publication is not implemented yet.
- Full real-hardware install/upgrade/recovery certification is incomplete.
- Advanced display/input configuration still delegates to mature KWin/KScreen/KDE modules.
- Notification rendering still uses an interchangeable freedesktop notification backend; a Fly-owned daemon is a later milestone.

## 0.5.0-dev — Native Session Preview

### Added
- Native `KWin Wayland + Fly Session + Fly Shell` login path; Plasma Workspace is no longer required to start Fly OS.
- Fly Base ISO builder using an Ubuntu 26.04 minimal `debootstrap` rootfs.
- Fly Search local SQLite/FTS index of names and paths only.
- Fly-owned Apps and Update front ends.
- Session-only, opt-in clipboard history and integrated shortcut.
- Secure lock abstraction preferring KScreenLocker/PAM under KWin plus idle locking.
- Native session notification center, PolicyKit agent integration, XDG graphical-session startup and autostart compatibility.
- Battery Care helper gated by firmware-exposed charge thresholds.
- Theme auto/light/dark helper and hardware-aware profiles.
- Wine `.exe`/`.msi` MIME integration and Wine launchers in universal search.
- Fly release-channel abstraction and local APT-repository builder.

### Changed
- Plasma Workspace moved from recommended fallback to optional/suggested fallback.
- Fly Update now checks disk space, snapshots when possible and keeps local transaction logs.
- Distribution identity migration removes the old `dpkg-divert` approach and preserves upstream `/usr/lib/os-release`.
- Native user services are supervised through `flyos-session.target`; shell crashes no longer have to end the compositor session.

### Known developer-preview limitations
- Fly Base media does not yet implement the final signed Secure-Boot/shim publishing path.
- Hardware installation/upgrade/recovery matrix is not complete.
- 0.5 still ships Fly components together in one developer Debian package; package splitting is planned before 1.0.

## 0.4.0-dev — Developer Preview

### Added
- Fly Shell built with Qt/QML and KDE LayerShellQt over the KWin Wayland compositor.
- Fly Launcher, dock, top bar and quick settings.
- Adaptive low-power/reduced-effects behavior hooks.
- Fly Health diagnostics for Secure Boot, AppArmor, firewall, zram, Wine/NTSYNC, firmware and updates.
- Fly Recovery and Btrfs/Snapper snapshot helpers with safe fallback when Btrfs is unavailable.
- Fly Gaming launcher integrating GameMode, MangoHud and Gamescope when installed.
- Flatpak/portal and fwupd integration through KDE Discover.
- zram, automatic security updates, firewall initialization and device-aware storage tuning.
- First-login wizard, Fly Center, Wine helpers and branded Calamares/Plymouth/SDDM assets.
- GitHub CI, contribution/security/privacy documentation and publication helper.

### Changed
- Fly OS distribution identity is applied through `/etc/os-release` while Ubuntu's `/usr/lib/os-release` remains untouched for base-package compatibility; `flyos-identity.service` reapplies the derivative identity after base updates.
- Default `vm.swappiness` is 100 to match the use of high-priority compressed zram without aggressively preferring swap on mixed configurations.
- Plasma panels are omitted by the Fly look-and-feel because Fly Shell owns the primary top bar and dock; Plasma/KWin remain the recovery and compatibility foundation.

### Experimental
- FlyKernel profile and optional advanced KWin Glass effect.
- Full Btrfs snapshot recovery depends on an installation using Btrfs.

## 0.3.0-dev
- Added Fly Welcome, Fly Apps, Fly Update and initial GitHub project structure.

## 0.2.0-dev
- Added advanced Fly Glass option, Calamares branding and expanded FlyKernel configuration.

## 0.1.0-dev
- Initial Fly OS packaging, branding, Wine integration and ISO remaster pipeline.

## 0.7.0-dev — 2026-09-30

### Added
- `flyos-privacy`, a separate package for session-local camera/microphone indicators.
- Fly Privacy dashboard with per-session app attribution where the Linux audio/video stack exposes it.
- Camera indicator in Fly Shell and application attribution in privacy tooltips.
- Focus Mode in Quick Settings and Fly Center; it enables DND without persistent telemetry/history.
- Fly Defaults for browser, PDF, image, video, audio and text MIME defaults through XDG.

### Changed
- Fly Shell and Fly Center settings writes are now atomic and protected by a per-user advisory lock.
- Privacy monitoring is an explicit member of `flyos-session.target` and cannot leak into unrelated sessions.
- Fly Search exposes Privacy and Default Apps as first-class system actions.
- The Fly Center privacy page now links directly to real-time local privacy state.

### Fixed
- Prevented concurrent settings writes from leaving partially-written JSON.
- Fixed package ownership ordering so the privacy user service belongs to `flyos-privacy`, not `flyos-shell`.
