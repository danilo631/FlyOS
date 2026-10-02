# Fly OS hardware integration

Fly OS owns the user-facing hardware experience but deliberately reuses established Linux services underneath.

- **Networking:** NetworkManager.
- **Bluetooth:** BlueZ; `fly-bluetooth` is the common-device UI.
- **Audio:** PipeWire/WirePlumber with PulseAudio compatibility tooling for device moves.
- **Battery:** UPower plus kernel power-supply sysfs. Health and charge limits are shown only when firmware exposes them.
- **Hybrid GPU:** switcheroo-control render offload. Fly OS does not claim to switch hardware muxes.
- **Displays/color:** KWin/KScreen, including Night Color, HDR/color management and fractional scaling where supported upstream.
- **Firmware:** fwupd.

This boundary is intentional: Fly can replace its UI without forking hardware daemons or drivers, while upstream security and device fixes remain consumable.
