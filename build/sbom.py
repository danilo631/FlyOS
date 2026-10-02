#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate a deterministic SPDX 2.3 JSON SBOM for Fly-owned project files."""
from __future__ import annotations
import hashlib, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text().strip()
OUT=ROOT/'dist'/f'FlyOS-{VERSION}.spdx.json'
EXCLUDED={'.git','.build','.cache','.packages','dist'}

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def created()->str:
    epoch=os.environ.get('SOURCE_DATE_EPOCH')
    if epoch and epoch.isdigit():
        dt=datetime.fromtimestamp(int(epoch),tz=timezone.utc)
    else:
        try:
            stamp=subprocess.check_output(["git","-C",str(ROOT),"show","-s","--format=%ct","HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
            dt=datetime.fromtimestamp(int(stamp),tz=timezone.utc)
        except (OSError, ValueError, subprocess.CalledProcessError):
            dt=datetime.fromtimestamp(int((ROOT/"VERSION").stat().st_mtime),tz=timezone.utc)
        dt=dt.replace(microsecond=0)
    return dt.isoformat().replace('+00:00','Z')

files=[]
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or p.is_symlink(): continue
    rel=p.relative_to(ROOT)
    if rel.parts and rel.parts[0] in EXCLUDED: continue
    if '__pycache__' in rel.parts or p.suffix=='.pyc': continue
    files.append({
        'fileName':'./'+rel.as_posix(),
        'SPDXID':'SPDXRef-File-'+hashlib.sha1(rel.as_posix().encode()).hexdigest()[:16],
        'checksums':[{'algorithm':'SHA256','checksumValue':sha256(p)}],
        'licenseConcluded':'NOASSERTION',
        'copyrightText':'NOASSERTION',
    })

package_names=[]
for control in sorted((ROOT/'packages/components').glob('*.control')):
    for line in control.read_text().splitlines():
        if line.startswith('Package:'):
            package_names.append(line.split(':',1)[1].strip()); break
packages=[{
    'name':name,'SPDXID':'SPDXRef-Package-'+name.replace('_','-'),
    'versionInfo':VERSION,'downloadLocation':'NOASSERTION','filesAnalyzed':False,
    'licenseConcluded':'GPL-3.0-or-later','licenseDeclared':'GPL-3.0-or-later',
    'copyrightText':'NOASSERTION',
} for name in package_names]

doc={
 'spdxVersion':'SPDX-2.3','dataLicense':'CC0-1.0','SPDXID':'SPDXRef-DOCUMENT',
 'name':f'Fly OS {VERSION}',
 'documentNamespace':f'https://github.com/danilo631/FlyOS/spdx/{VERSION}',
 'creationInfo':{'created':created(),'creators':['Organization: Fly OS Project','Tool: build/sbom.py']},
 'documentDescribes':[p['SPDXID'] for p in packages],
 'packages':packages,'files':files,
 'annotations':[{
   'annotationDate':created(),'annotationType':'OTHER','annotator':'Tool: build/sbom.py',
   'comment':'This SBOM covers Fly-owned repository files and Fly Debian package metadata. Ubuntu/KDE/system packages remain upstream dependencies and are resolved by the distribution package manager.'
 }]
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
print(OUT)
