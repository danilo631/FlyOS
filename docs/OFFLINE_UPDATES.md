# Fly OS offline updates

Fly Update separates **download** from **installation** for system packages and follows systemd's `/system-update` maintenance-boot model.

1. The normal desktop refreshes APT metadata and records a human-readable simulated `full-upgrade` plan.
2. Stale APT archives are removed so the staging cache represents only this transaction.
3. The complete transaction is downloaded while networking and the normal desktop are available.
4. Fly Update re-solves the transaction with `--no-download` and writes SHA-256 hashes for every staged `.deb`.
5. Fly Recovery optionally creates a pre-update Snapper snapshot on supported Btrfs installations and stores the snapshot number.
6. `/system-update` is created only after planning, download and validation succeed.
7. On reboot, systemd redirects that boot to `system-update.target`.
8. `flyos-offline-update.service` removes `/system-update` **before** touching packages to prevent reboot loops, verifies the staged SHA-256 manifest, then runs `dpkg --configure -a` and APT with `--no-download`.
9. `dpkg --audit` must pass before the transaction is marked complete.
10. State, the APT plan and the local log remain under `/var/lib/flyos/offline-update/`, and the machine returns to the normal boot path.

`flock` serializes privileged update operations so two prepare/apply/cancel transactions cannot modify the state directory at the same time.

Flatpak user applications are updated in the user session. Firmware remains a separate fwupd flow because firmware update semantics vary by device and, on TPM/FDE systems, may require recovery-key handling before reboot.

## Recovery semantics

Btrfs + Snapper provides a useful pre-update snapshot, but Fly OS does **not** call this atomic rollback yet. ext4 remains supported without snapshot rollback. A failed archive-integrity check aborts before package installation. A failure after `dpkg` begins is logged, the system returns to normal boot, and Fly Recovery exposes package repair and any recorded Snapper snapshot.

A future stable release must test rollback/bootloader semantics on every supported installer layout before stronger guarantees are made.

## Transaction lock (0.6 alpha4)

Fly Update stores a normalized `Inst`/`Remv` resolver transaction beside the full APT simulation. After packages are downloaded, and again in `system-update.target` before any dpkg mutation, the resolver must produce the same transaction with `--no-download`. If package state or metadata changed after staging, Fly aborts the offline apply and returns to a normal boot. Staging also refuses plans that remove the Fly/session/package-management substrate and refuses to proceed when `dpkg --audit` or `apt-get check` report an unhealthy starting state.
