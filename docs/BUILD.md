# Building Fly OS 0.3

## Recommended host

Use an amd64 machine or VM running Ubuntu/Kubuntu 26.04 LTS with at least:

- 8 GB RAM (16 GB recommended for optional compositor/kernel builds)
- 35 GB free disk space for the normal ISO pipeline
- more free space if building FlyKernel
- working internet connection

## 1. Build the normal ISO

```bash
git clone <your FlyOS repository URL>
cd FlyOS
sudo apt update
make deps
make package
make iso
```

The ISO is written to:

```text
dist/FlyOS-0.3.0-dev-amd64.iso
```

The corresponding SHA-256 file is generated beside it.

## 2. Include the optional advanced glass effect

```bash
make glass-deps
make glass
make iso
```

Or use:

```bash
make iso-glass
```

The normal ISO does not require this effect; KDE's built-in blur is the fallback.

## 3. Test in QEMU

```bash
make test
```

UEFI testing uses OVMF when available. Test installation, reboot into the installed system, Wi-Fi/networking, audio, suspend/resume, Wine, Fly Center and system updates before trying physical hardware.

## 4. Write to USB

On Linux, identify the whole USB device carefully and use a graphical writer or `dd`. A wrong device path will destroy data.

Example only:

```bash
sudo dd if=dist/FlyOS-0.3.0-dev-amd64.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

Replace `/dev/sdX` with the whole USB device, not a partition.

## 5. FlyKernel

```bash
make kernel
```

The optional FlyKernel is a developer feature. A self-built kernel will not automatically be trusted by Secure Boot. Keep the Ubuntu signed kernel installed as a recovery option.

## Build reproducibility notes

The normal base ISO has a pinned SHA-256 in `build/download-base.sh`. Third-party source builds, such as KWin Glass, also record the exact Git revision in their generated package. For a formal release, pin all third-party refs and archive their corresponding source.
