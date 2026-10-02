# Fly OS modular packaging

Fly OS 0.8 keeps one reviewed rootfs source (`packages/flyos-base/rootfs`) and
produces independently replaceable Debian components through
`build/build-packages.py`. This makes ownership auditable while keeping the
source tree straightforward to review.

## Packages

| Package | Responsibility |
| --- | --- |
| `flyos-core` | identity, security defaults, system integration, health/tuning helpers |
| `flyos-shell` | KWin Wayland session, Fly Shell, OSD, shortcuts and session services |
| `flyos-center` | Fly Center, Apps, Connect, Defaults, Storage and onboarding |
| `flyos-search` | local-first filename/path index and search tooling |
| `flyos-update` | update discovery/staging and user-facing update state |
| `flyos-recovery` | snapshots, backup entry points, repair and offline-update engine |
| `flyos-privacy` | session-local camera/microphone indicators and privacy dashboard |
| `flyos-performance` | procfs/PSI monitor and Fly Activity resource/process UI |
| `flyos-wine` | Wine/Windows integration |
| `flyos-branding` | boot/login/installer/theme/icon/wallpaper assets |
| `flyos-base` | payload-free metapackage requiring the coordinated platform |

Fly packages share a coordinated version during the developer-alpha series.
Independent component ABI/API versioning should only happen after the updater
and repository can express safe compatibility constraints.

## Ownership rules

`build/build-packages.py` assigns every payload path to exactly one package.
Rules for narrow components such as search, privacy and performance appear
before the generic Fly Shell user-service rule so a new service cannot silently
be absorbed into the wrong package.

## Migration

Payload packages retain `Replaces/Breaks` metadata for files that were owned by
the old monolithic `flyos-base`. The current `flyos-base` contains no payload.

## QA guarantees

`make lint` verifies:

- Python and shell syntax;
- desktop/JSON metadata parsing;
- no Python bytecode in source or packages;
- every modular Debian package builds;
- representative files land in the expected component;
- no payload file is owned by two Fly packages;
- privacy/performance services are explicitly covered by package tests;
- the native session target does not leak into other desktop sessions;
- command-queue, offline-update and shell integration regression guards;
- ISO builders consume the complete local package set.
