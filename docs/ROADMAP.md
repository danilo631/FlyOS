# Fly OS Roadmap

## 0.10.0-dev — current developer alpha
- reliability/session audit and stricter systemd regression checks;
- adaptive shell/privacy polling for fewer idle wakeups;
- shared atomic settings schema;
- native airplane mode and low-battery safety notifications;
- battery/pressure-aware local indexing;
- continued Bluetooth/battery/GPU/Night Light integration from 0.9.

## Next: Beta readiness
- hardware matrix for Intel/AMD/NVIDIA graphics and common Wi-Fi/Bluetooth chipsets;
- installer + encrypted install + Secure Boot validation;
- suspend/resume and docking/multi-monitor certification;
- rollback/recovery drills and offline-update fault injection;
- accessibility and touch/tablet testing;
- UI string/i18n extraction and translations.

# Fly OS roadmap

## 0.8 Developer Alpha — completed

- [x] Native KWin/Wayland Fly session without requiring `plasmashell`
- [x] Modular Debian packages with explicit ownership QA
- [x] Fly Shell bar/dock/launcher/Quick Settings/notifications/OSD
- [x] Local-first Fly Search with filename/path index
- [x] Local launcher calculator and private app-frequency/recency ranking
- [x] Fly Center / Apps / Connect / Defaults / Storage / Login Items
- [x] Wi-Fi, Bluetooth common operations and NetworkManager hotspot flow
- [x] PipeWire/Pulse output **and input** switching in Quick Settings
- [x] Session-local camera/microphone privacy indicators
- [x] Fly Performance procfs/PSI monitor and Fly Activity
- [x] Pressure-aware visual reduction without global scheduler/governor tweaks
- [x] Event-driven shell command queue with race-safe batch handoff
- [x] Safe UI + crash-loop Rescue UI
- [x] Offline transaction-locked APT update flow + recovery state
- [x] SPDX SBOM and APT repository generator
- [ ] Real-hardware matrix for install/upgrade/suspend/GPU/audio/Bluetooth

## 0.9 Stabilization — completed/integrated

- native Bluetooth PIN/passkey agent with accessibility review;
- deeper screen-reader/keyboard-only coverage of every Fly-owned surface;
- installer profiles for ext4 and Btrfs with tested recovery semantics;
- image-level SBOM/provenance and reproducible-build reporting;
- signed Fly APT repository infrastructure;
- local crash bundle creation with explicit opt-in submission only;
- per-monitor/workspace UX enhancements gated by compositor capability detection;
- comprehensive localization workflow.

## 1.0 release engineering

- signed Secure Boot/shim/GRUB/kernel publication path;
- automatic ISO CI on controlled builders;
- upgrade/rollback tests from prior Fly releases;
- package migration tests and interrupted-update tests;
- hardware certification matrix covering Intel/AMD/NVIDIA, Wi-Fi/Bluetooth,
  audio/webcam, multi-monitor, suspend/resume and low-memory/low-disk cases;
- release checklist fully green before the word “stable” is used.
