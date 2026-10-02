# Fly OS release checklist

Before publishing an ISO:

- `make lint` passes.
- Base ISO SHA-256 matches Canonical's published checksum.
- Boot tested in UEFI VM.
- Live session starts and shows Fly branding.
- Calamares starts as Install Fly OS and completes an installation.
- Installed system boots twice successfully.
- `apt update && apt full-upgrade` completes without removing Fly packages unexpectedly.
- Fly Center launches.
- `fly-glass balanced`, `glass` and `performance` do not break KWin.
- Wine can initialize a prefix and start `winecfg`.
- Network, audio, Bluetooth, suspend and display scaling are tested on representative hardware.
- NVIDIA path is tested separately if proprietary drivers are offered.
- Secure Boot is tested with the stock Ubuntu kernel.
- Release source archive, licenses, checksums and known issues are published with the binary ISO.

## 0.9 hardware integration gates
- [ ] Bluetooth power/scan/pair/connect/disconnect/trust/remove on at least Intel and Realtek adapters.
- [ ] Bluetooth audio reconnect and input/output switching after suspend.
- [ ] Battery percentage/state on UPower laptops; health/cycle values only where firmware exposes them.
- [ ] Battery Care threshold set/reset on at least two supported laptop vendors; unsupported hardware must clearly report no support.
- [ ] Hybrid Intel/AMD and Intel/NVIDIA machines enumerate with switcheroo-control and launch an application on the discrete GPU.
- [ ] Single-GPU machines show a safe no-discrete-GPU path.
- [ ] Night Light fixed schedule survives logout/reboot and does not require location permission.
- [ ] Support report redacts home path, hostname, IPv4 and MAC addresses before manual user review.
