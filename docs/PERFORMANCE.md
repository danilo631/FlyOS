# Fly OS performance policy

Fly OS optimizes for responsiveness **without** permanent benchmark-mode tuning.

1. Use Ubuntu's supported kernel as the stable default.
2. Use ZRAM for bounded compressed swap rather than excessive swappiness.
3. Let NVMe/SSD scheduler defaults stand; apply BFQ/read-ahead tuning only to rotational disks when supported.
4. Use power-profiles-daemon for user-visible energy modes.
5. Use GameMode only while a game requests it.
6. Expose Gamescope/MangoHud as optional tools, not mandatory wrappers.
7. Keep blur and animation profiles switchable; Performance mode can disable expensive blur.
8. Measure regressions with boot time, frame pacing, memory pressure/PSI and battery tests instead of synthetic scores alone.

## 0.4 adaptive policy

Fly OS distinguishes **system defaults** from **temporary workload boosts**:

- zram is high-priority compressed swap; `vm.swappiness=100` is intentionally neutral for this fast in-memory swap path while still behaving reasonably when disk swap also exists;
- `systemd-oomd` is installed so PSI-aware tooling is available, but Fly OS does **not** ship an aggressive custom kill policy in 0.4; distributions and workloads differ too much for a one-size-fits-all threshold;
- Fly Shell reduces translucency and animation when `power-profiles-daemon` enters `power-saver`, and also respects KDE's zero-animation preference;
- `fly-profile` coordinates power and visual profiles without replacing the kernel scheduler;
- `fly-game` delegates temporary per-game tuning to GameMode instead of permanently forcing a performance governor;
- FlyKernel is opt-in and remains separate from the signed Ubuntu kernel path.

Useful commands:

```bash
fly-profile auto
fly-profile battery
fly-profile balanced
fly-profile performance
fly-profile gaming
fly-doctor
```


## Architecture-aware packages

Ubuntu 26.04 exposes an `amd64v3` architecture variant. Fly OS never enables it blindly. `fly-arch-opt status` checks the dynamic loader/CPU capability and `sudo fly-arch-opt enable` writes the APT variant preference only on compatible amd64 systems. This follows the same principle used throughout Fly OS: select optimized code paths when hardware proves they are safe, rather than raising the minimum CPU requirement for everyone.

## Foreground-first service QoS

Fly-owned desktop work is separated with user cgroup slices instead of global scheduler tweaks:

- `fly-interactive.slice` gives the shell a higher relative CPU/I/O weight;
- `fly-background.slice` gives indexing/maintenance work a lower relative weight;
- the indexer also keeps `Nice=15`, batch CPU scheduling and idle I/O scheduling.

Weights are relative and only matter under contention. They do not pin CPUs, disable kernel schedulers or force the machine into a permanent performance governor. On systems where a cgroup controller is not delegated to the user manager, the unsupported controller may simply have no effect; the service itself remains usable.

## 0.8 adaptive pressure monitor

`fly-performance-monitor.service` replaces repeated shell-side utility spawning for
resource-pressure decisions. It reads `/proc/stat`, `/proc/meminfo`, Linux PSI,
`/proc/loadavg` and available thermal sysfs nodes, then publishes a small JSON
snapshot under `$XDG_RUNTIME_DIR/fly-performance.json`. The file is session-local
and contains no application content, filenames or network data.

Fly Shell uses three refresh cadences:

- 1 s: clock only, no external commands;
- ~2.8 s: interactive state such as volume, brightness, media and workspace;
- 12 s: network/Bluetooth/power profile, audio-device inventories, update state,
  Night Light, settings and resource-pressure policy.

If adaptive performance is enabled, only a conservative `pressure` state reduces
transparency/motion. `busy` is informational. Neither state changes the kernel
scheduler, CPU governor, process priority or OOM policy. Users can disable the
visual adaptation in Fly Center while keeping Fly Activity/resource monitoring.
