#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared, versioned Fly OS per-user settings.

The shell and Fly Center use this module so settings validation, permissions and
atomic writes stay consistent. Unknown keys are preserved for forward
compatibility; known keys are normalized to safe types/ranges.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
SETTINGS_FILE = Path.home() / ".config/flyos/settings.json"

DEFAULTS: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "theme": "auto",
    "pinned": [],
    "dnd": False,
    "focus_mode": False,
    "reduce_transparency": False,
    "reduce_motion": False,
    "high_contrast": False,
    "text_scale": 1.0,
    "dock_magnification": True,
    "online_search": False,
    "clipboard_history": False,
    "adaptive_performance": True,
}

_BOOL_KEYS = {
    "dnd", "focus_mode", "reduce_transparency", "reduce_motion",
    "high_contrast", "dock_magnification", "online_search",
    "clipboard_history", "adaptive_performance",
}


def _normalize(values: dict[str, Any]) -> dict[str, Any]:
    out = dict(values)
    out["schema_version"] = SCHEMA_VERSION
    theme = str(out.get("theme", "auto")).casefold()
    out["theme"] = theme if theme in {"auto", "light", "dark"} else "auto"
    for key in _BOOL_KEYS:
        out[key] = bool(out.get(key, DEFAULTS[key]))
    try:
        out["text_scale"] = round(max(0.75, min(2.0, float(out.get("text_scale", 1.0)))), 2)
    except (TypeError, ValueError):
        out["text_scale"] = 1.0
    pinned = out.get("pinned", [])
    if not isinstance(pinned, list):
        pinned = []
    clean: list[str] = []
    for item in pinned:
        value = str(item).strip()
        if value and value not in clean:
            clean.append(value)
        if len(clean) >= 32:
            break
    out["pinned"] = clean
    return out


def load_settings() -> dict[str, Any]:
    values = dict(DEFAULTS)
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            values.update(raw)
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return _normalize(values)


def save_settings(values: dict[str, Any]) -> bool:
    """Atomically write settings with private permissions and a per-user lock."""
    data = _normalize(dict(values))
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            SETTINGS_FILE.parent.chmod(0o700)
        except OSError:
            pass
        lock_path = SETTINGS_FILE.with_suffix(".lock")
        with lock_path.open("a+", encoding="utf-8") as lock:
            try:
                lock_path.chmod(0o600)
            except OSError:
                pass
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            tmp = SETTINGS_FILE.with_suffix(f".tmp.{os.getpid()}")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            tmp.chmod(0o600)
            os.replace(tmp, SETTINGS_FILE)
            # Persist the directory entry on filesystems that support fsync on dirs.
            try:
                dfd = os.open(SETTINGS_FILE.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(dfd)
                finally:
                    os.close(dfd)
            except OSError:
                pass
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        return True
    except OSError:
        return False
