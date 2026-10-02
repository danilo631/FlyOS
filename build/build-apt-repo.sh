#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

for cmd in dpkg-scanpackages gzip sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || die "Missing $cmd (run make deps)"
done

CHANNEL="${FLYOS_CHANNEL:-dev}"
REPO="$DIST_DIR/apt-repo"
POOL="$REPO/pool/main/f/flyos"
BIN="$REPO/dists/$CHANNEL/main/binary-amd64"
ALL="$REPO/dists/$CHANNEL/main/binary-all"
rm -rf "$REPO"
mkdir -p "$POOL" "$BIN" "$ALL"
shopt -s nullglob
if [[ "${FLYOS_REPO_ALL_VERSIONS:-0}" == 1 ]]; then
  REPO_DEBS=("$PKG_DIR"/flyos-*.deb)
else
  REPO_DEBS=("$PKG_DIR"/flyos-*_${VERSION}_all.deb)
fi
shopt -u nullglob
(( ${#REPO_DEBS[@]} > 0 )) || die "No Fly OS packages found; run make package"
cp -a "${REPO_DEBS[@]}" "$POOL/"

(
  cd "$REPO"
  dpkg-scanpackages --multiversion --arch all pool /dev/null > "dists/$CHANNEL/main/binary-all/Packages"
  gzip -9c "dists/$CHANNEL/main/binary-all/Packages" > "dists/$CHANNEL/main/binary-all/Packages.gz"
  # The amd64 index must include Architecture: all packages as well as future
  # native amd64 payloads. dpkg-scanpackages --arch amd64 excludes all-only
  # packages on some dpkg versions, so generate the client index unfiltered.
  dpkg-scanpackages --multiversion pool /dev/null > "dists/$CHANNEL/main/binary-amd64/Packages"
  gzip -9c "dists/$CHANNEL/main/binary-amd64/Packages" > "dists/$CHANNEL/main/binary-amd64/Packages.gz"
  if command -v apt-ftparchive >/dev/null 2>&1; then
    apt-ftparchive \
      -o APT::FTPArchive::Release::Origin="Fly OS" \
      -o APT::FTPArchive::Release::Label="Fly OS" \
      -o APT::FTPArchive::Release::Suite="$CHANNEL" \
      -o APT::FTPArchive::Release::Codename="$CHANNEL" \
      -o APT::FTPArchive::Release::Architectures="amd64 all" \
      -o APT::FTPArchive::Release::Components="main" \
      release "dists/$CHANNEL" > "dists/$CHANNEL/Release"
  else
    python3 - "$REPO/dists/$CHANNEL" "$CHANNEL" <<'PYREL'
from pathlib import Path
from email.utils import formatdate
import hashlib, sys
root=Path(sys.argv[1]); channel=sys.argv[2]
files=[]
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name not in {'Release','Release.gpg','InRelease'}:
        data=p.read_bytes(); files.append((hashlib.sha256(data).hexdigest(),len(data),p.relative_to(root).as_posix()))
lines=[
    'Origin: Fly OS','Label: Fly OS',f'Suite: {channel}',f'Codename: {channel}',
    'Architectures: amd64 all','Components: main',f'Date: {formatdate(usegmt=True)}','SHA256:'
]
lines += [f' {h} {size:16d} {name}' for h,size,name in files]
(root/'Release').write_text('\n'.join(lines)+'\n')
PYREL
  fi
)

# Protect clients from stale/replayed metadata and index races.
case "$CHANNEL" in
  dev) VALID_DAYS=30 ;;
  beta) VALID_DAYS=90 ;;
  stable) VALID_DAYS=370 ;;
  *) die "Unsupported Fly OS channel: $CHANNEL" ;;
esac
python3 - "$REPO/dists/$CHANNEL/Release" "$VALID_DAYS" <<'PYMETA'
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
import sys
p=Path(sys.argv[1]); days=int(sys.argv[2]); lines=p.read_text().splitlines()
lines=[line for line in lines if not line.startswith(('Valid-Until:', 'Acquire-By-Hash:'))]
insert_at=next((i+1 for i,line in enumerate(lines) if line.startswith('Date:')), 0)
extra=[f'Valid-Until: {format_datetime(datetime.now(timezone.utc)+timedelta(days=days), usegmt=True)}','Acquire-By-Hash: yes']
lines[insert_at:insert_at]=extra
p.write_text('\n'.join(lines)+'\n')
PYMETA

for index in "$BIN/Packages" "$BIN/Packages.gz" "$ALL/Packages" "$ALL/Packages.gz"; do
  hash=$(sha256sum "$index" | awk '{print $1}')
  mkdir -p "$(dirname "$index")/by-hash/SHA256"
  cp -f "$index" "$(dirname "$index")/by-hash/SHA256/$hash"
done

if [[ -n "${FLYOS_GPG_KEY:-}" ]] && command -v gpg >/dev/null 2>&1; then
  gpg --batch --yes --local-user "$FLYOS_GPG_KEY" --armor --detach-sign -o "$REPO/dists/$CHANNEL/Release.gpg" "$REPO/dists/$CHANNEL/Release"
  gpg --batch --yes --local-user "$FLYOS_GPG_KEY" --clearsign -o "$REPO/dists/$CHANNEL/InRelease" "$REPO/dists/$CHANNEL/Release"
else
  warn "APT repo is unsigned. Set FLYOS_GPG_KEY=<fingerprint> for release publication."
fi
log "Fly OS APT repository generated: $REPO"
