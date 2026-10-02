# Fly OS security model

## Baseline

Fly OS inherits Ubuntu's AppArmor, kernel hardening and package-signing model. Secure Boot should remain compatible on the standard Ubuntu-kernel edition.

## Network

UFW is initialized to deny unsolicited incoming traffic and allow outgoing traffic. KDE Connect TCP/UDP 1714–1764 are allowed for local-device integration.

## Application isolation

Flatpak is supported with XDG desktop portals. Apps should use the minimum permissions necessary; users can inspect/change Flatpak permissions with the KDE tooling available in the desktop.

## Updates

Security updates are enabled through unattended-upgrades. Full system upgrades remain user-visible through Fly Update; Discover is an optional advanced catalog. Firmware is surfaced through fwupd when available.

## Recovery

The update helper attempts a Btrfs/Snapper snapshot only when the underlying system supports it. A failed snapshot does not block security updates, but is reported by the recovery tooling.

## Telemetry

Fly OS adds no project-owned telemetry by default. Any future diagnostics upload must be separately documented and opt-in before a stable release.
