# Fly OS APT repository

Fly-owned components are distributed separately from the Ubuntu archive.

**Base URL:** `https://raw.githubusercontent.com/danilo631/FlyOS/apt`

**Channels:** `dev`, `beta`, `stable`

Development signing-key fingerprint:

`18A2 C567 1234 3CC0 0D78 82A6 C90E B084 8627 75A3`

The public key is safe to publish. The private signing key must never be committed.
Configure it only as the GitHub Actions secret `FLYOS_APT_GPG_PRIVATE_KEY`.

Fly OS 0.11 includes a `flyos-repo` package with the public key, deb822 source,
and `fly-repo` channel manager.
