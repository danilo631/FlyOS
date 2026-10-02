#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the modular Fly OS Debian packages from the shared source rootfs.

The source tree stays easy to review while installed ownership is split into
small components.  Every payload file has exactly one owner; flyos-base is a
pure metapackage.  This also makes individual Fly components replaceable and
updatable without rebuilding the entire desktop layer.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

def inferred_channel(version: str) -> str:
    value = version.casefold()
    if "dev" in value or "alpha" in value:
        return "dev"
    if "beta" in value or "rc" in value:
        return "beta"
    return "stable"

DEFAULT_CHANNEL = os.environ.get("FLYOS_DEFAULT_CHANNEL", inferred_channel(VERSION))
if DEFAULT_CHANNEL not in {"dev", "beta", "stable"}:
    raise SystemExit(f"invalid FLYOS_DEFAULT_CHANNEL: {DEFAULT_CHANNEL}")
SOURCE = ROOT / "packages/flyos-base/rootfs"
COMP = ROOT / "packages/components"
BUILD = ROOT / ".build/modular-packages"
OUT = ROOT / ".packages"
PACKAGES = ("flyos-core", "flyos-shell", "flyos-center", "flyos-search", "flyos-update", "flyos-recovery", "flyos-privacy", "flyos-performance", "flyos-wine", "flyos-branding", "flyos-repo")


def starts(path: str, *prefixes: str) -> bool:
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes)


def owner(path: str) -> str:
    # Visual identity and installer assets.
    if starts(path,
        "etc/default/grub.d", "etc/sddm.conf.d",
        "usr/share/color-schemes", "usr/share/konsole", "usr/share/icons",
        "usr/share/pixmaps", "usr/share/plasma", "usr/share/plymouth",
        "usr/share/sddm", "usr/share/wallpapers", "usr/share/flyos/calamares"):
        return "flyos-branding"

    # Local-first search index is independently replaceable. This rule must
    # precede the generic user-service rule below.
    if path in {
        "usr/bin/fly-indexer", "usr/bin/fly-search",
        "usr/lib/systemd/user/fly-indexer.service",
        "usr/lib/systemd/user/fly-indexer.timer",
        "usr/lib/systemd/user/fly-background.slice",
    }:
        return "flyos-search"

    # Session-local privacy indicators and dashboard.
    if path in {
        "usr/bin/fly-privacy",
        "usr/lib/flyos/fly-privacy.py",
        "usr/lib/flyos/fly-privacy-monitor",
        "usr/lib/systemd/user/fly-privacy-monitor.service",
        "usr/share/applications/fly-privacy.desktop",
    }:
        return "flyos-privacy"

    # Lightweight procfs/PSI performance telemetry stays local to the session.
    if path in {
        "usr/bin/fly-activity",
        "usr/lib/flyos/fly-performance-monitor",
        "usr/lib/systemd/user/fly-performance-monitor.service",
        "usr/share/applications/fly-activity.desktop",
    }:
        return "flyos-performance"

    # Native session + shell runtime.  Services whose lifetime is the graphical
    # session belong here rather than in the system core.
    if starts(path,
        "etc/xdg/flyos", "usr/lib/environment.d",
        "usr/share/flyos/shell", "usr/share/wayland-sessions"):
        return "flyos-shell"
    if path.startswith("usr/lib/systemd/user/"):
        return "flyos-shell"
    if path.startswith("usr/share/applications/fly-volume-") or path.startswith("usr/share/applications/fly-brightness-") or path.startswith("usr/share/applications/fly-media-"):
        return "flyos-shell"
    if path in {
        "etc/xdg/autostart/fly-shell.desktop",
        "usr/bin/fly-session", "usr/bin/fly-shell", "usr/bin/fly-shellctl",
        "usr/bin/fly-lock", "usr/bin/fly-theme", "usr/bin/fly-nightlight",
        "usr/bin/fly-clipboard", "usr/bin/fly-volume", "usr/bin/fly-brightness", "usr/bin/fly-media",
        "usr/lib/flyos/fly-shell.py", "usr/lib/flyos/fly-session-inner",
        "usr/lib/flyos/fly-notifications", "usr/lib/flyos/fly-rescue-ui.py", "usr/lib/flyos/fly-first-login",
        "usr/lib/flyos/fly-clipboard-capture",
    }:
        return "flyos-shell"

    # Integrated UI surfaces and onboarding.
    if path in {
        "etc/xdg/autostart/flyos-first-login.desktop",
        "etc/xdg/autostart/flyos-welcome.desktop",
        "usr/bin/fly-center", "usr/bin/fly-apps", "usr/bin/fly-connect", "usr/bin/fly-defaults", "usr/bin/fly-storage", "usr/bin/fly-login-items",
        "usr/bin/fly-files", "usr/bin/fly-audio", "usr/bin/fly-firewall",
        "usr/bin/fly-bluetooth", "usr/bin/fly-battery-dashboard", "usr/bin/fly-gpu", "usr/bin/fly-gpu-run",
        "usr/lib/flyos/fly-apps.py", "usr/lib/flyos/fly-center.py",
        "usr/lib/flyos/fly-connect.py", "usr/lib/flyos/fly-defaults.py", "usr/lib/flyos/fly-welcome.py",
        "usr/lib/flyos/fly-files.py", "usr/lib/flyos/fly-audio.py", "usr/lib/flyos/fly-firewall.py", "usr/lib/flyos/fly-firewall-helper",
        "usr/lib/flyos/fly-package-helper",
        "usr/lib/flyos/fly-bluetooth.py", "usr/lib/flyos/fly-battery.py", "usr/lib/flyos/fly-gpu.py",
        "usr/share/applications/fly-apps.desktop",
        "usr/share/applications/fly-storage.desktop",
        "usr/share/applications/fly-login-items.desktop",
        "usr/share/applications/fly-center.desktop",
        "usr/share/applications/fly-defaults.desktop",
        "usr/share/applications/fly-launcher.desktop",
        "usr/share/applications/fly-quick.desktop",
        "usr/share/applications/fly-notification-center.desktop",
        "usr/share/applications/fly-welcome.desktop",
        "usr/share/applications/fly-bluetooth.desktop",
        "usr/share/applications/fly-battery.desktop",
        "usr/share/applications/fly-gpu.desktop",
        "usr/share/applications/fly-files.desktop", "usr/share/applications/fly-audio.desktop", "usr/share/applications/fly-firewall.desktop",
    }:
        return "flyos-center"

    # Local-first search index is independently replaceable.
    if path in {
        "usr/bin/fly-indexer", "usr/bin/fly-search",
        "usr/lib/systemd/user/fly-indexer.service",
        "usr/lib/systemd/user/fly-indexer.timer",
        "usr/lib/systemd/user/fly-background.slice",
    }:
        return "flyos-search"

    # Update UI/channel selection. Recovery owns privileged/offline transactions.
    if path in {
        "usr/bin/fly-update", "usr/bin/fly-channel",
        "usr/lib/flyos/fly-updater.py",
        "usr/share/applications/fly-update.desktop",
    }:
        return "flyos-update"

    if path in {
        "usr/bin/fly-recovery", "usr/bin/fly-recovery-ui", "usr/bin/fly-snapshot", "usr/bin/fly-backup",
        "usr/lib/flyos/fly-recovery-ui.py", "usr/lib/flyos/fly-recovery-helper", "usr/share/applications/fly-recovery.desktop",
        "usr/bin/fly-offline-update", "usr/lib/flyos/fly-offline-update-helper",
        "usr/lib/systemd/system/flyos-offline-update.service",
        "usr/share/applications/fly-backup.desktop",
    } or path.startswith("usr/lib/systemd/system/system-update.target.wants/"):
        return "flyos-recovery"


    # Fly OS archive configuration and signing key.
    if path in {
        "etc/apt/sources.list.d/flyos.sources",
        "etc/apt/sources.list.d/flyos.sources.in",
        "usr/bin/fly-repo",
        "usr/lib/flyos/fly-repo-helper",
        "usr/share/keyrings/flyos-archive-keyring.gpg",
    }:
        return "flyos-repo"

    # Windows compatibility is independently replaceable.
    if path.startswith("usr/bin/fly-wine") or path in {
        "usr/share/applications/fly-wine.desktop",
        "usr/share/applications/fly-wine-run.desktop",
    }:
        return "flyos-wine"

    # Everything else is core system integration/diagnostics.
    return "flyos-core"


def copy_payload(src: Path, dst_root: Path) -> None:
    rel = src.relative_to(SOURCE).as_posix()
    dst_rel = rel[:-3] if rel.endswith(".in") else rel
    dst = dst_root / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_symlink():
        dst.symlink_to(os.readlink(src))
        return
    data = src.read_bytes()
    if rel.endswith(".in"):
        data = data.replace(b"@VERSION@", VERSION.encode())
        data = data.replace(b"@CHANNEL@", DEFAULT_CHANNEL.encode())
    dst.write_bytes(data)
    shutil.copystat(src, dst, follow_symlinks=False)


def write_control(pkg: str, stage: Path) -> None:
    template = COMP / f"{pkg}.control"
    text = template.read_text(encoding="utf-8").replace("@VERSION@", VERSION)
    debian = stage / "DEBIAN"
    debian.mkdir(parents=True, exist_ok=True)
    (debian / "control").write_text(text, encoding="utf-8")
    os.chmod(debian, 0o755)
    scripts = COMP / pkg / "DEBIAN"
    if scripts.is_dir():
        for src in scripts.iterdir():
            if src.is_file():
                dst = debian / src.name
                shutil.copy2(src, dst)
                os.chmod(dst, 0o755)


def sanitize(stage: Path) -> None:
    for p in list(stage.rglob("__pycache__")):
        if p.is_dir():
            shutil.rmtree(p)
    for p in stage.rglob("*.pyc"):
        p.unlink(missing_ok=True)
    for p in stage.rglob("*"):
        if p.is_dir():
            p.chmod(p.stat().st_mode & ~stat.S_ISGID)


def build_deb(pkg: str, stage: Path) -> Path:
    out = OUT / f"{pkg}_{VERSION}_all.deb"
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(stage), str(out)], check=True)
    subprocess.run(["dpkg-deb", "--info", str(out)], check=True, stdout=subprocess.DEVNULL)
    return out


def main() -> int:
    if not SOURCE.is_dir():
        raise SystemExit(f"missing source rootfs: {SOURCE}")
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)

    stages = {pkg: BUILD / pkg for pkg in PACKAGES}
    for stage in stages.values():
        stage.mkdir(parents=True)

    counts = {pkg: 0 for pkg in PACKAGES}
    for src in sorted(SOURCE.rglob("*")):
        if not (src.is_file() or src.is_symlink()):
            continue
        rel = src.relative_to(SOURCE).as_posix()
        pkg = owner(rel)
        copy_payload(src, stages[pkg])
        counts[pkg] += 1

    built: list[Path] = []
    for pkg in PACKAGES:
        write_control(pkg, stages[pkg])
        sanitize(stages[pkg])
        built.append(build_deb(pkg, stages[pkg]))

    # Pure metapackage, intentionally no payload.
    meta = BUILD / "flyos-base"
    meta.mkdir(parents=True)
    write_control("flyos-base", meta)
    built.append(build_deb("flyos-base", meta))

    for pkg in PACKAGES:
        print(f"{pkg}: {counts[pkg]} payload files")
    print("Built:")
    for path in built:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
