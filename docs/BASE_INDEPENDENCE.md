# Reducing base dependence

Fly OS is not trying to replace every mature Linux subsystem. The goal is to own the product experience and update/recovery policy while minimizing vendor-specific desktop coupling.

## Fly-owned

Shell/session, UX defaults, local search, settings surface, update orchestration, recovery tools, Wine integration, first-run experience, branding and release policy.

## Reused upstream infrastructure

Linux, systemd, KWin/Wayland, Mesa, PipeWire/WirePlumber, NetworkManager, BlueZ, AppArmor, UFW, fwupd, APT/dpkg and Qt/KDE Frameworks.

These pieces are intentionally reused because forking them would increase security and hardware-maintenance risk without producing useful user differentiation.

## Ubuntu relationship

Ubuntu 26.04 supplies the package archive, signed/default kernel path and much hardware enablement. Fly Base can be built from a minimal Ubuntu rootfs and does not need the Kubuntu desktop meta-package. Fly OS keeps `ID_LIKE=ubuntu debian` for ecosystem compatibility while presenting its own `/etc/os-release` identity.

## Migration path

1. Native Fly Session (0.5).
2. Split Fly components into independently versioned Debian packages.
3. Signed Fly APT repository with stable/beta/dev channels.
4. Reproducible Fly Base ISO CI and installer test matrix.
5. Signed Secure-Boot publishing path.
6. Evaluate transactional/immutable system mode only after recovery/update semantics are proven; do not add immutability merely as a marketing feature.


## 0.11 dependency boundary

Fly OS now owns a `flyplatform` integration layer and user-facing Files/Audio/Firewall/Recovery surfaces. The dependency goal is not to fork Linux infrastructure; it is to eliminate redundant UI/CLI adapters. KWin, NetworkManager, BlueZ, PipeWire/WirePlumber, systemd, Mesa and the kernel remain upstream replaceable layers because maintaining private forks of these projects would reduce security and hardware compatibility.
