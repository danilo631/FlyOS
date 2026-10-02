# Software bill of materials

`make sbom` generates `dist/FlyOS-<version>.spdx.json` in SPDX 2.3 JSON format.

The document covers Fly-owned repository files and lists the Fly Debian components. Ubuntu, KDE, Wine, systemd, Mesa, NetworkManager and other upstream packages are intentionally not copied into the project SBOM as if Fly authored them; their exact installed versions are resolved by the base archive and can be inventoried on a built image separately.

Release bundles include the SBOM and its SHA-256 checksum.
