# Fly OS 0.11 Developer Alpha

Fly OS is an open-source Wayland desktop operating-system project. Ubuntu 26.04 LTS remains the compatibility/security/hardware substrate, while the visible session, shell, settings, search, update/recovery, Windows integration and Fly package feed are owned by Fly OS.

## 0.11 highlights

- **Fly Platform** uses direct D-Bus integration for KWin, MPRIS, NetworkManager and BlueZ.
- Fly media no longer requires playerctl; Fly network/Bluetooth no longer parse nmcli/bluetoothctl.
- screenshot uses XDG Desktop Portal; brightness uses logind + kernel backlight; clipboard history uses Qt/Wayland directly.
- **Fly Files**, Fly Audio, Fly Display, Fly Firewall and Fly Recovery UI cover common tasks without requiring Dolphin, pavucontrol, Spectacle, PackageKit or Plasma System Settings in the default image.
- Fly Apps uses a narrow PolicyKit APT helper rather than PackageKit.
- **flyos-repo** installs the Fly OS archive key/source and manages dev/beta/stable channels.
- Signed APT bootstrap is published from the **apt** branch.

APT feed:

`https://raw.githubusercontent.com/danilo631/FlyOS/apt`

Development key fingerprint:

`18A2 C567 1234 3CC0 0D78 82A6 C90E B084 8627 75A3`

## Build

```bash
make deps
make package
make lint
make iso-flybase
```

Fly OS 0.11 is still a developer alpha. Real-hardware installation, Secure Boot signing, suspend/resume, recovery and broader GPU/Bluetooth testing remain release blockers.
