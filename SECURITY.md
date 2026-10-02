# Security policy

Fly OS 0.x is a developer preview. Fly-owned code must not disable upstream security features merely for performance.

The normal path retains AppArmor, UFW policy, PolicyKit, unattended security updates and the upstream signed kernel. The native KWin session prefers KScreenLocker/PAM for secure locking. Experimental FlyKernel/KWin changes are isolated and optional.

The Fly Base ISO builder currently produces developer media and is **not** the final signed Secure-Boot/shim publishing path. Stable releases are blocked on that work plus the installation/upgrade/recovery matrix in `docs/RELEASE_CHECKLIST.md`.

See `docs/SECURITY_MODEL.md` for the platform threat model.

## Shell failure containment

`fly-shell.service` is supervised independently from KWin. If repeated shell crashes exhaust its restart burst, systemd starts a minimal Qt-based Fly Rescue UI. The compositor/session remains alive, allowing a Safe UI restart, diagnostics/settings access or a controlled logout. This reduces the chance that a UI regression turns into an unusable blank session.

## Offline update integrity

Prepared APT updates are serialized with `flock`. The staging phase records the simulated transaction, clears stale archives, downloads the required packages and writes SHA-256 hashes. The maintenance boot verifies those hashes before invoking `dpkg`; archive-integrity failure therefore aborts before package state changes. This is integrity/recoverability hardening, not a claim of filesystem-atomic updates on ext4.
