#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fly OS platform integration layer.

This module keeps Fly applications on stable system APIs instead of parsing
human-facing CLI output wherever an API exists. It intentionally wraps mature
upstream services (KWin, NetworkManager, BlueZ, logind and MPRIS) rather than
forking them.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    import dbus
except Exception:  # pragma: no cover - lets tooling import without a bus
    dbus = None  # type: ignore

NM = "org.freedesktop.NetworkManager"
NM_PATH = "/org/freedesktop/NetworkManager"
NM_IFACE = "org.freedesktop.NetworkManager"
PROPS = "org.freedesktop.DBus.Properties"
BLUEZ = "org.bluez"
OBJMGR = "org.freedesktop.DBus.ObjectManager"
MPRIS_PLAYER = "org.mpris.MediaPlayer2.Player"


def _bus(system: bool = False):
    if dbus is None:
        raise RuntimeError("python3-dbus is unavailable")
    return dbus.SystemBus() if system else dbus.SessionBus()


def _props(bus, service: str, path: str):
    return dbus.Interface(bus.get_object(service, path), PROPS)


def notify(summary: str, body: str = "", *, urgency: int = 1, expire_ms: int = 4500) -> bool:
    try:
        bus = _bus(False)
        obj = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
        iface = dbus.Interface(obj, "org.freedesktop.Notifications")
        hints = {"urgency": dbus.Byte(max(0, min(2, urgency)))}
        iface.Notify("Fly OS", 0, "flyos", summary[:120], body[:600], [], hints, int(expire_ms))
        return True
    except Exception:
        return False


# ---- KWin / desktop -------------------------------------------------------

def kwin_call(path: str, interface: str, method: str, *args: Any) -> tuple[bool, Any | None]:
    """Call KWin and preserve success for D-Bus methods that return void.

    A successful void D-Bus method is represented by ``(True, None)``; this is
    intentionally distinct from ``(False, None)`` so UI actions do not report
    false failures after KWin already performed the action.
    """
    try:
        bus = _bus(False)
        obj = bus.get_object("org.kde.KWin", path)
        return True, getattr(dbus.Interface(obj, interface), method)(*args)
    except Exception:
        return False, None


def kwin_reconfigure() -> bool:
    ok, _value = kwin_call("/KWin", "org.kde.KWin", "reconfigure")
    return ok


def kwin_toggle_overview() -> bool:
    ok, _value = kwin_call("/Effects", "org.kde.kwin.Effects", "toggleEffect", "overview")
    return ok


def kwin_workspace(direction: str) -> bool:
    if direction not in {"next", "previous"}:
        return False
    method = "nextDesktop" if direction == "next" else "previousDesktop"
    ok, _value = kwin_call("/KWin", "org.kde.KWin", method)
    return ok


def kwin_current_desktop() -> int:
    ok, value = kwin_call("/KWin", "org.kde.KWin", "currentDesktop")
    if not ok:
        return 1
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 1


# ---- NetworkManager -------------------------------------------------------

def nm_radio(kind: str) -> bool:
    key = {"wifi": "WirelessEnabled", "wwan": "WwanEnabled"}.get(kind)
    if not key:
        return False
    try:
        bus = _bus(True)
        return bool(_props(bus, NM, NM_PATH).Get(NM_IFACE, key))
    except Exception:
        return False


def nm_set_radio(kind: str, enabled: bool) -> bool:
    key = {"wifi": "WirelessEnabled", "wwan": "WwanEnabled"}.get(kind)
    if not key:
        return False
    try:
        bus = _bus(True)
        _props(bus, NM, NM_PATH).Set(NM_IFACE, key, dbus.Boolean(bool(enabled)))
        return True
    except Exception:
        return False


def nm_primary_connection_name() -> str:
    try:
        bus = _bus(True)
        p = _props(bus, NM, NM_PATH)
        primary = str(p.Get(NM_IFACE, "PrimaryConnection"))
        if not primary or primary == "/":
            return "Offline"
        ac_props = _props(bus, NM, primary)
        ident = str(ac_props.Get("org.freedesktop.NetworkManager.Connection.Active", "Id"))
        return ident or "Conectado"
    except Exception:
        return "Offline"


# ---- BlueZ ----------------------------------------------------------------

def _bluez_objects() -> dict[str, dict[str, dict[str, Any]]]:
    try:
        bus = _bus(True)
        mgr = dbus.Interface(bus.get_object(BLUEZ, "/"), OBJMGR)
        return dict(mgr.GetManagedObjects())
    except Exception:
        return {}


def bluez_adapters() -> list[str]:
    return [p for p, ifaces in _bluez_objects().items() if "org.bluez.Adapter1" in ifaces]


def bluez_powered() -> bool:
    objects = _bluez_objects()
    for ifaces in objects.values():
        adapter = ifaces.get("org.bluez.Adapter1")
        if adapter is not None:
            return bool(adapter.get("Powered", False))
    return False


def bluez_set_powered(enabled: bool) -> bool:
    ok = False
    try:
        bus = _bus(True)
        for path in bluez_adapters():
            _props(bus, BLUEZ, path).Set("org.bluez.Adapter1", "Powered", dbus.Boolean(bool(enabled)))
            ok = True
    except Exception:
        return False
    return ok


def bluez_devices() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path, ifaces in _bluez_objects().items():
        dev = ifaces.get("org.bluez.Device1")
        if dev is None:
            continue
        items.append({
            "path": path,
            "address": str(dev.get("Address", "")),
            "name": str(dev.get("Alias", dev.get("Name", dev.get("Address", "Dispositivo")))),
            "paired": bool(dev.get("Paired", False)),
            "trusted": bool(dev.get("Trusted", False)),
            "connected": bool(dev.get("Connected", False)),
            "rssi": int(dev.get("RSSI", -999)) if "RSSI" in dev else -999,
        })
    items.sort(key=lambda d: (not d["connected"], not d["paired"], -int(d["rssi"]), str(d["name"]).casefold()))
    return items


def bluez_adapter_action(action: str) -> bool:
    try:
        bus = _bus(True)
        paths = bluez_adapters()
        if not paths:
            return False
        adapter = dbus.Interface(bus.get_object(BLUEZ, paths[0]), "org.bluez.Adapter1")
        if action == "discover-start":
            adapter.StartDiscovery()
        elif action == "discover-stop":
            adapter.StopDiscovery()
        else:
            return False
        return True
    except Exception:
        return False


def bluez_device_action(path: str, action: str) -> bool:
    if not path.startswith("/org/bluez/"):
        return False
    try:
        bus = _bus(True)
        obj = bus.get_object(BLUEZ, path)
        dev = dbus.Interface(obj, "org.bluez.Device1")
        if action == "connect": dev.Connect()
        elif action == "disconnect": dev.Disconnect()
        elif action == "pair": dev.Pair()
        elif action in {"trust", "untrust"}:
            _props(bus, BLUEZ, path).Set("org.bluez.Device1", "Trusted", dbus.Boolean(action == "trust"))
        elif action == "remove":
            adapter_path = path.rsplit("/", 1)[0]
            dbus.Interface(bus.get_object(BLUEZ, adapter_path), "org.bluez.Adapter1").RemoveDevice(dbus.ObjectPath(path))
        else: return False
        return True
    except Exception:
        return False


# ---- MPRIS media -----------------------------------------------------------

def _mpris_players() -> list[str]:
    try:
        names = _bus(False).list_names()
        return sorted([str(n) for n in names if str(n).startswith("org.mpris.MediaPlayer2.")])
    except Exception:
        return []


def _mpris_snapshot(name: str) -> tuple[str, str, str] | None:
    try:
        bus = _bus(False)
        p = _props(bus, name, "/org/mpris/MediaPlayer2")
        status = str(p.Get(MPRIS_PLAYER, "PlaybackStatus"))
        meta = dict(p.Get(MPRIS_PLAYER, "Metadata"))
        title = str(meta.get("xesam:title", ""))
        artists = meta.get("xesam:artist", [])
        artist = ", ".join(str(x) for x in artists) if artists else ""
        return status, title, artist
    except Exception:
        return None


def _preferred_mpris_player() -> tuple[str, tuple[str, str, str]] | None:
    candidates: list[tuple[int, str, tuple[str, str, str]]] = []
    for name in _mpris_players():
        snap = _mpris_snapshot(name)
        if snap is None:
            continue
        status, title, _artist = snap
        rank = {"playing": 0, "paused": 1, "stopped": 2}.get(status.casefold(), 3)
        if not title and rank >= 2:
            rank += 2
        candidates.append((rank, name, snap))
    if not candidates:
        return None
    _rank, name, snap = min(candidates, key=lambda item: (item[0], item[1]))
    return name, snap


def media_state() -> tuple[str, str, bool, str]:
    preferred = _preferred_mpris_player()
    if preferred is None:
        return "", "", False, ""
    name, (status, title, artist) = preferred
    return title[:160], artist[:120], status.casefold() == "playing", name


def media_action(action: str) -> bool:
    method = {"play-pause": "PlayPause", "next": "Next", "previous": "Previous", "stop": "Stop"}.get(action)
    if not method:
        return False
    preferred = _preferred_mpris_player()
    names = [preferred[0]] if preferred else []
    names += [name for name in _mpris_players() if name not in names]
    for name in names:
        try:
            obj = _bus(False).get_object(name, "/org/mpris/MediaPlayer2")
            getattr(dbus.Interface(obj, MPRIS_PLAYER), method)()
            return True
        except Exception:
            continue
    return False


# ---- Brightness ------------------------------------------------------------

def _backlights() -> list[Path]:
    base = Path("/sys/class/backlight")
    if not base.exists(): return []
    return sorted([p for p in base.iterdir() if (p / "brightness").exists() and (p / "max_brightness").exists()])


def brightness_percent() -> int:
    for dev in _backlights():
        try:
            cur = int((dev / "brightness").read_text().strip())
            maximum = int((dev / "max_brightness").read_text().strip())
            if maximum > 0:
                return max(0, min(100, round(cur * 100 / maximum)))
        except (OSError, ValueError):
            continue
    return -1


def set_brightness_percent(percent: int) -> bool:
    percent = max(1, min(100, int(percent)))
    devices = _backlights()
    if not devices:
        return False
    dev = devices[0]
    try:
        maximum = int((dev / "max_brightness").read_text().strip())
        raw = max(1, round(maximum * percent / 100))
    except (OSError, ValueError):
        return False
    # logind mediates brightness for desktop sessions without a setuid helper.
    try:
        bus = _bus(True)
        manager = dbus.Interface(bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1"), "org.freedesktop.login1.Manager")
        session_path = manager.GetSessionByPID(dbus.UInt32(os.getpid()))
        session = dbus.Interface(bus.get_object("org.freedesktop.login1", session_path), "org.freedesktop.login1.Session")
        session.SetBrightness("backlight", dev.name, dbus.UInt32(raw))
        return True
    except Exception:
        return False


# ---- WirePlumber -----------------------------------------------------------

def _run(argv: list[str], timeout: float = 2.0) -> str:
    try:
        return subprocess.run(argv, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def audio_volume(source: bool = False) -> tuple[int, bool]:
    target = "@DEFAULT_AUDIO_SOURCE@" if source else "@DEFAULT_AUDIO_SINK@"
    text = _run(["wpctl", "get-volume", target], 0.8)
    m = re.search(r"Volume:\s+([0-9.]+)", text)
    value = int(round(float(m.group(1)) * 100)) if m else 0
    return max(0, min(150, value)), "[MUTED]" in text


def audio_set_volume(percent: int, source: bool = False) -> bool:
    target = "@DEFAULT_AUDIO_SOURCE@" if source else "@DEFAULT_AUDIO_SINK@"
    try:
        return subprocess.run(["wpctl", "set-volume", target, f"{max(0,min(150,int(percent)))}%"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except OSError:
        return False


def audio_toggle_mute(source: bool = False) -> bool:
    target = "@DEFAULT_AUDIO_SOURCE@" if source else "@DEFAULT_AUDIO_SINK@"
    try:
        return subprocess.run(["wpctl", "set-mute", target, "toggle"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except OSError:
        return False


def audio_endpoints(source: bool = False) -> list[dict[str, Any]]:
    # wpctl is WirePlumber's native control surface. -n asks for stable names.
    text = _run(["wpctl", "status", "-n"], 1.2)
    section = "Sources:" if source else "Sinks:"
    other = "Sinks:" if source else "Sources:"
    active = False
    items: list[dict[str, Any]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.endswith(section):
            active = True; continue
        if active and stripped.endswith(other):
            break
        if active and re.match(r"^[│├└\s*]+\d+\.\s", raw):
            m = re.search(r"([*]?)\s*(\d+)\.\s+(.+?)(?:\s+\[.*)?$", stripped.replace("│", "").replace("├", "").replace("└", "").strip())
            if m:
                default = bool(m.group(1)); ident = m.group(2); name = m.group(3).strip()
                items.append({"id": ident, "name": ident, "label": ("✓ " if default else "") + name, "default": default})
    return items[:24]


def audio_set_default(identifier: str) -> bool:
    if not str(identifier).isdigit():
        return False
    try:
        return subprocess.run(["wpctl", "set-default", str(identifier)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except OSError:
        return False

# ---- NetworkManager Wi-Fi connections -------------------------------------
def _nm_wireless_device(bus=None) -> str:
    bus = bus or _bus(True)
    try:
        mgr = dbus.Interface(bus.get_object(NM, NM_PATH), NM_IFACE)
        for path in mgr.GetDevices():
            props = _props(bus, NM, str(path))
            if int(props.Get('org.freedesktop.NetworkManager.Device', 'DeviceType')) == 2:
                return str(path)
    except Exception:
        pass
    return ''


def nm_wifi_networks(rescan: bool = False) -> list[dict[str, Any]]:
    try:
        bus = _bus(True); dev_path = _nm_wireless_device(bus)
        if not dev_path: return []
        dev = dbus.Interface(bus.get_object(NM, dev_path), 'org.freedesktop.NetworkManager.Device.Wireless')
        if rescan:
            try: dev.RequestScan({})
            except Exception: pass
        active = str(_props(bus, NM, dev_path).Get('org.freedesktop.NetworkManager.Device.Wireless', 'ActiveAccessPoint'))
        items=[]; seen=set()
        for ap_path in dev.GetAccessPoints():
            p=_props(bus,NM,str(ap_path)); ssid_bytes=bytes(p.Get('org.freedesktop.NetworkManager.AccessPoint','Ssid'))
            ssid=ssid_bytes.decode('utf-8',errors='replace')
            if not ssid or ssid in seen: continue
            seen.add(ssid); strength=int(p.Get('org.freedesktop.NetworkManager.AccessPoint','Strength'))
            flags=int(p.Get('org.freedesktop.NetworkManager.AccessPoint','Flags')); wpa=int(p.Get('org.freedesktop.NetworkManager.AccessPoint','WpaFlags')); rsn=int(p.Get('org.freedesktop.NetworkManager.AccessPoint','RsnFlags'))
            secure=bool(flags or wpa or rsn)
            items.append({'ssid':ssid,'strength':strength,'secure':secure,'active':str(ap_path)==active,'path':str(ap_path)})
        items.sort(key=lambda n:(not n['active'],-n['strength'],n['ssid'].casefold())); return items
    except Exception:
        return []


def _nm_settings() -> tuple[Any, Any]:
    bus=_bus(True); return bus, dbus.Interface(bus.get_object(NM,'/org/freedesktop/NetworkManager/Settings'),'org.freedesktop.NetworkManager.Settings')


def nm_find_connection(connection_id: str) -> str:
    try:
        bus, settings=_nm_settings()
        for path in settings.ListConnections():
            conn=dbus.Interface(bus.get_object(NM,str(path)),'org.freedesktop.NetworkManager.Settings.Connection')
            data=conn.GetSettings(); section=dict(data.get('connection',{}))
            if str(section.get('id',''))==connection_id: return str(path)
    except Exception: pass
    return ''


def nm_delete_connection(connection_id: str) -> bool:
    try:
        bus, _settings=_nm_settings(); path=nm_find_connection(connection_id)
        if not path: return True
        dbus.Interface(bus.get_object(NM,path),'org.freedesktop.NetworkManager.Settings.Connection').Delete(); return True
    except Exception: return False


def nm_connect_wifi(ssid: str, password: str = '') -> bool:
    if not ssid or len(ssid.encode()) > 32: return False
    try:
        bus=_bus(True); dev_path=_nm_wireless_device(bus)
        if not dev_path: return False
        aps=nm_wifi_networks(False); match=next((a for a in aps if a['ssid']==ssid),None)
        if not match: return False
        settings={
            'connection': {'id': ssid, 'type':'802-11-wireless', 'autoconnect': dbus.Boolean(True)},
            '802-11-wireless': {'ssid': dbus.ByteArray(ssid.encode()), 'mode':'infrastructure'},
            'ipv4': {'method':'auto'}, 'ipv6': {'method':'auto'},
        }
        if match['secure']:
            if len(password)<8: return False
            settings['802-11-wireless-security']={'key-mgmt':'wpa-psk','psk':password}
        manager=dbus.Interface(bus.get_object(NM,NM_PATH),NM_IFACE)
        existing=nm_find_connection(ssid)
        if existing:
            manager.ActivateConnection(dbus.ObjectPath(existing), dbus.ObjectPath(dev_path), dbus.ObjectPath(match['path']))
        else:
            manager.AddAndActivateConnection(settings, dbus.ObjectPath(dev_path), dbus.ObjectPath(match['path']))
        return True
    except Exception: return False


def nm_hotspot(ssid: str, password: str) -> bool:
    if not ssid or len(ssid.encode())>32 or len(password)<8 or len(password)>63: return False
    try:
        bus=_bus(True); dev_path=_nm_wireless_device(bus)
        if not dev_path:return False
        nm_delete_connection('Fly Hotspot')
        settings={
            'connection': {'id':'Fly Hotspot','type':'802-11-wireless','autoconnect':dbus.Boolean(False)},
            '802-11-wireless': {'ssid':dbus.ByteArray(ssid.encode()),'mode':'ap'},
            '802-11-wireless-security': {'key-mgmt':'wpa-psk','psk':password},
            'ipv4': {'method':'shared'}, 'ipv6': {'method':'ignore'},
        }
        dbus.Interface(bus.get_object(NM,NM_PATH),NM_IFACE).AddAndActivateConnection(settings,dbus.ObjectPath(dev_path),dbus.ObjectPath('/'))
        return True
    except Exception:return False


def nm_hotspot_stop() -> bool:
    return nm_delete_connection('Fly Hotspot')
