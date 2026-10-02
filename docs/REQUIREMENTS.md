# Fly OS modern desktop requirements

This is the product checklist for turning Fly OS from a themed remix into a maintainable desktop operating system.

| Area | Fly OS 0.5 status | Design rule |
|---|---|---|
| Boot / hardware | Ubuntu 26.04 signed kernel by default; FlyKernel optional | Never trade Secure Boot/vendor compatibility for a benchmark claim |
| Display | KWin Wayland foundation; Fly Shell uses LayerShellQt | Reuse upstream HDR, color management, fractional scaling, VRR and multi-monitor work |
| Shell | Fly top bar, dock, launcher and quick settings | Fly owns UX; KWin owns compositor/input/display correctness |
| Accessibility | Reduced effects in power-saver/zero-animation mode; Plasma accessibility remains available | Motion and transparency must never be required to understand state |
| Apps | Fly Apps: APT + optional Flatpak; Discover optional | Native packages for system integration; sandboxed apps where useful |
| Sandboxing | XDG portals + Flatpak support | Least access by default for sandboxed apps |
| Windows apps | Wine prefix, helpers, NTSYNC-aware diagnostics | Compatibility is integrated but never masquerades as native security isolation |
| Gaming | GameMode, Gamescope, MangoHud wrappers | Temporary workload tuning, not permanent governor/scheduler hacks |
| Firmware | fwupd through Fly Update; Discover backend optional | Firmware updates belong in the same maintenance experience |
| Updates | APT security updates + Flatpak + firmware checks | Snapshot before risky system changes where supported |
| Recovery | Btrfs/Snapper helpers; package/initramfs/GRUB repair | Never call a feature a snapshot when the filesystem cannot provide one |
| Backups | Kup/bup/rsync | System snapshots are not user backups |
| Privacy | No Fly telemetry by default | Optional network services must be explicit |
| Security | AppArmor, UFW, Secure Boot diagnostics, unattended security updates | Keep Ubuntu hardening; add visibility rather than disabling mitigations |
| Private storage | Plasma Vault + gocryptfs | User-controlled encrypted folders without a Fly cloud dependency |
| Memory | zram + PSI/systemd-oomd availability | Preserve responsiveness under pressure; avoid arbitrary kill thresholds |
| Power | power-profiles-daemon + adaptive effects | Battery mode reduces compositor cost as well as CPU policy |
| CPU optimization | Optional checked amd64v3 APT variant | Optimize only after hardware capability is proven |
| Audio | PipeWire + WirePlumber | Modern graph-based audio/Bluetooth stack |
| Networking | NetworkManager/KDE integration + KDE Connect firewall allowance | Secure defaults without breaking expected LAN integration |
| Diagnostics | Fly Health + `fly-doctor` | A user should be able to explain the machine state before changing it |
| Fallback | KWin/TTY/recovery remain usable; Plasma can be installed as an optional fallback | A shell crash must not equal a dead desktop |
| Open source | GPL-3.0-or-later project code; third-party licenses preserved | No Apple proprietary code/assets; upstream changes stay attributable |
| Releases | CI + smoke tests + release checklist | “Stable” requires installer, upgrade, hardware and recovery testing |

## Product philosophies combined

Fly OS deliberately takes ideas rather than branding or proprietary implementation:

- **Apple-like coherence:** one visual language, strong defaults, low-friction setup, adaptive animation/power behavior and fewer duplicated controls.
- **Ubuntu/Debian maintainability:** signed kernel default, APT/dpkg, AppArmor, security updates and the existing hardware ecosystem.
- **KDE flexibility:** Wayland/KWin capabilities stay accessible underneath the curated Fly experience.
- **Fedora-style upstream-first memory strategy:** compressed zram and modern userspace/kernel interfaces instead of swap folklore.
- **SteamOS-style gaming isolation:** Gamescope/GameMode are invoked for gaming workloads rather than changing the entire machine permanently.
- **ChromeOS-like recovery thinking:** changes should be reversible and a broken UX layer should have a known fallback path.
- **Android-like pressure awareness:** react to memory/power pressure using kernel/system interfaces rather than killing background software on fixed timers.

These are product principles, not claims that Fly OS contains code from those operating systems.

## Requirements before 1.0

0.5 is not called production-ready until all of these are demonstrated on real hardware: encrypted install path, suspend/resume, multi-monitor hotplug, fractional scaling, Intel/AMD/NVIDIA graphics, Wi-Fi/Bluetooth, audio, webcam, printing, Secure Boot, upgrade rollback, low-disk behavior, low-memory behavior, laptop battery/sleep, installer failure recovery, accessibility keyboard-only navigation, and at least one clean upgrade from the previous Fly release.
