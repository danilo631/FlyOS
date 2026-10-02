# Fly OS privacy

Fly OS does not add project-owned telemetry to the default image.

- **Fly Search** indexes file names and paths from normal user folders into `~/.cache/flyos/search.db`. It does not upload queries and does not index file contents.
- **Clipboard history** is disabled by default. When enabled it is stored in `$XDG_RUNTIME_DIR`, capped, text-only and disappears with the login session; disabling it clears the runtime history.
- **Flathub** is not silently enabled. Users explicitly opt in.
- Fly Health performs diagnostics locally.

Ubuntu/KDE infrastructure, browsers, firmware services, stores and installed applications may contact their own upstream services according to their own settings and privacy policies.

Any future Fly crash-upload or analytics service must be open, documented and opt-in before a stable release.

## Session-local notifications

Fly OS 0.6 Alpha 3 includes its own freedesktop notification daemon. Notification history is stored only under the current user's `$XDG_RUNTIME_DIR`, is capped, and disappears with the login session/reboot. Fly OS does not upload notification content. Do Not Disturb suppresses Fly toast interruptions while keeping local history available until the session ends or the user clears it.

## Local search and clipboard permissions

The Fly Search cache directory is forced to mode `0700` and its SQLite filename/path index to `0600`, reducing exposure to other local users. File contents are never indexed. Optional clipboard history is also written atomically with mode `0600` under `$XDG_RUNTIME_DIR` and remains disabled by default.
