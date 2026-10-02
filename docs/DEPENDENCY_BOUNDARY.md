# Fly OS dependency boundary — 0.11

Fly OS deliberately owns the **product layer** while reusing mature Linux hardware/security infrastructure.

## Fly-owned

- Fly Session and Fly Shell
- Fly Platform integration API
- Fly Center, Apps, Search, Files, Audio, Connect and Bluetooth UI
- Fly Privacy and Performance
- Fly Update and Recovery UI/transaction coordination
- Fly Wine integration
- Fly branding and first-run experience
- Fly APT repository configuration, channel selection and publication tooling

## Upstream substrate kept intentionally

- Linux kernel and Ubuntu hardware enablement
- systemd/logind/udev
- Mesa/DRM and vendor GPU drivers
- KWin/Wayland and XWayland compatibility
- NetworkManager
- BlueZ
- PipeWire/WirePlumber
- UPower/power-profiles-daemon
- AppArmor/UFW/PolicyKit
- APT/dpkg and Debian package format

These components are not retained because Fly OS is unable to replace them; they are retained because forking them would create a large security/driver maintenance burden without improving the normal desktop experience.

## Removed from the normal Fly path in 0.11

The native desktop no longer requires command-output parsing or separate UX utilities for common actions such as `nmcli`, the BlueZ CLI client, `playerctl`, `pactl`, `brightnessctl`, `wl-clipboard`, `notify-send`, PackageKit, pavucontrol or Spectacle. Fly Platform talks to D-Bus/logind/portals or WirePlumber directly.

Dolphin, Konsole, Plasma System Settings and Plasma Workspace remain optional compatibility/advanced tools rather than requirements for the native Fly session.

## Security rule

Privileged Fly helpers must expose a finite command vocabulary. They must never become a generic root shell or accept arbitrary command strings.
