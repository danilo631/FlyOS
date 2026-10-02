# Fly OS architecture — 0.8 developer alpha

## Principle

Fly OS owns the user experience and operating-system integration layer while
reusing mature upstream infrastructure. Reducing Ubuntu/KDE dependency means
removing user-facing coupling, not rewriting drivers, the compositor,
networking or audio only for branding.

## Stack

```text
Linux kernel / firmware / Mesa
        ↓
systemd + udev + NetworkManager + PipeWire/WirePlumber
        ↓
KWin Wayland + XWayland + portals + PolicyKit
        ↓
Fly Session
        ↓
Fly Shell ─ Fly Search ─ Fly Center/Apps/Connect
    │          │              │
    │          └──── local index / calculator / app ranking
    ├──── Fly Privacy
    ├──── Fly Performance / Activity
    └──── Fly Update / Recovery / Wine
```

Ubuntu 26.04 archives provide the current compatibility/security/hardware base.
Fly Base starts from a minimal `debootstrap` rootfs instead of a full Kubuntu
desktop. Plasma Workspace is an optional fallback, not a native-session
requirement.

## Failure domains

- KWin owns compositor/display/input and remains running if Fly Shell restarts;
- Fly Shell has restart limits and a separate Rescue UI;
- search indexing runs in a low-priority background slice;
- privacy and performance monitors are independent user services;
- notification ownership is separate from shell rendering through the standard
  freedesktop D-Bus interface;
- update/recovery are separate from the shell and APT system transactions run in
  the systemd offline-update environment;
- Safe UI reduces effects without switching graphics stacks.

## Performance boundary

Fly Performance reads procfs/sysfs/PSI and publishes session-local state. Fly
Shell can reduce visual work under real pressure, but the monitor does not
select a CPU governor, replace the kernel scheduler, kill processes or alter OOM
thresholds. Hardware-facing power policy remains delegated to
`power-profiles-daemon` and scoped tools such as GameMode.

## Data and privacy boundaries

- Fly Search indexes names/paths, never document contents.
- Search application-frequency/recency metadata remains local in user state.
- Calculator expressions are evaluated locally with a bounded arithmetic AST.
- Clipboard history is opt-in and session-only.
- Privacy/performance monitor state is written under `$XDG_RUNTIME_DIR` and
  disappears at logout.
- Fly settings live under `~/.config/flyos` with atomic writes.
- No Fly telemetry service is enabled by default.

## Upstream boundaries we intentionally keep

Fly OS does not plan to fork Linux DRM, Mesa, NetworkManager, PipeWire, systemd
or KWin without a concrete user problem that cannot be solved upstream. These
are replaceable infrastructure interfaces, not Fly branding.

## Notification ownership

Fly Notifications owns `org.freedesktop.Notifications` in the native session.
Fly Shell renders toasts/history/actions directly, while notification history
remains session-local.
