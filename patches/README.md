# Source patches

Fly OS should patch upstream code only where configuration cannot express the product behavior.

Current experimental patches:

- `kwin/0001-flyos-blur-range-note.patch` is a reference patch documenting where a future Fly-specific KWin blur tuning patch belongs.
- kernel patches live under `kernel/patches/`.

For the 0.1 ISO, KWin behavior is configured through public KWin settings instead of replacing Ubuntu/KDE binaries. This keeps security updates compatible.
