"""M4.2-only layered integrity policy. Historical verifiers are untouched."""
import json
from pathlib import Path
import stat
import subprocess
from scripts.m4_capture_check import sha, no_links
from scripts.m42_monitor import append, write

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'research_outputs/m41_p2_a01_acceptance_01/resume_01'
FROZEN_SHA='a626655acee213f67d7b759159fe7b5d658f90d89bb8edfd90a3c50c75634d60'
M41_COMMIT='0fceadc7f9bc054854322c39e40f09f51ff10fcf'
CORE=['utils.py','reconstruct.py','api.py','load.py','plot.py','ontology/hw1.ttl','pixi.toml','pixi.lock']


def read(path): return json.loads(Path(path).read_text())


def verify(hashes,root=ROOT):
    changed=[]
    for name,digest in hashes.items():
        path=no_links(Path(root)/name)
        if not path.is_file() or sha(path)!=digest: changed.append(name)
    if changed: raise RuntimeError('Scientific/source SHA mismatch: '+repr(changed))
    return len(hashes)


def metadata(path):
    path=no_links(path)
    if not path.exists(): return dict(path=str(path),exists=False,type=None,sha256=None)
    if path.name!='.DS_Store' or not stat.S_ISREG(path.lstat().st_mode):
        raise RuntimeError('Not regular Finder metadata: '+str(path))
    with path.open('rb') as f: header=f.read(8)
    kind=subprocess.check_output(['/usr/bin/file','-b',str(path)],text=True).strip()
    if header!=b'\x00\x00\x00\x01Bud1' or 'Apple Desktop Services Store' not in kind:
        raise RuntimeError('Invalid Finder metadata signature/type: '+str(path))
    return dict(path=str(path),exists=True,type=kind,header_hex=header.hex(),sha256=sha(path))


def inventory(bases,exclude=()):
    scientific={}; os_metadata={}
    for base in bases:
        base=no_links(base)
        for path in sorted(base.rglob('*')):
            if any(e==path or e in path.parents for e in exclude): continue
            no_links(path)
            if path.name=='.DS_Store':
                os_metadata[str(path.relative_to(ROOT))]=metadata(path)
            elif path.is_file(): scientific[str(path.relative_to(ROOT))]=sha(path)
            elif not path.is_dir(): raise RuntimeError('Unknown file type: '+str(path))
    return dict(policy='m42-layered-v1',scientific=scientific,os_metadata=os_metadata)


def compare(before,after,log):
    if before['scientific']!=after['scientific']:
        names=set(before['scientific'])|set(after['scientific'])
        changed=[n for n in sorted(names) if before['scientific'].get(n)!=after['scientific'].get(n)]
        raise RuntimeError('Preservation scientific inventory changed: '+repr(changed))
    for name in sorted(set(before['os_metadata'])|set(after['os_metadata'])):
        old=before['os_metadata'].get(name,dict(path=str(ROOT/name),exists=False,sha256=None,type=None))
        new=after['os_metadata'].get(name,metadata(ROOT/name))
        append(log,dict(path=name,before=old,after=new,changed=old!=new,
            scientific_exception=False,policy='m42-layered-v1'))
    return len(before['scientific'])


def frozen_capture():
    path=FROZEN/'scientific_data_frozen_sha256.json'
    if sha(path)!=FROZEN_SHA: raise RuntimeError('Frozen manifest anchor mismatch')
    hashes=read(path)
    if len(hashes)!=642: raise RuntimeError('Expected exactly 642 frozen scientific files')
    verify(hashes)
    capture=ROOT/'eval/_data/second_floor/114753116/P2_A_01'
    actual=inventory([capture])
    if actual['scientific']!=hashes: raise RuntimeError('Unexpected/missing capture scientific files')
    return hashes


def historical_sources():
    # Bind the entire accepted M4.1 handoff and its evidence, without editing old manifests.
    provenance=read(FROZEN/'provenance.json')
    committed=subprocess.check_output(['git','show',M41_COMMIT+':docs/implementation/M4_Phase2_P2A_Capture_Acceptance_Resume.md'],cwd=ROOT)
    if committed!=(ROOT/'docs/implementation/M4_Phase2_P2A_Capture_Acceptance_Resume.md').read_bytes():
        raise RuntimeError('M4.1 handoff differs from accepted commit')
    verify(provenance['source_sha256'])
    if sha(FROZEN/'completion_01/acceptance.json')!=provenance['acceptance_sha256']:
        raise RuntimeError('M4.1 acceptance changed')
    verify(read(FROZEN/'manifest.json'),FROZEN)
    for name in CORE:
        original=subprocess.check_output(['git','show',M41_COMMIT+':'+name],cwd=ROOT)
        if original!=(ROOT/name).read_bytes(): raise RuntimeError('Accepted source changed: '+name)
    start=read(ROOT/'research_outputs/m4_capture_P2_A_01/start.json')
    verify(start['source_sha256'])
    return {name:sha(ROOT/name) for name in CORE}


def historical_preservation(log):
    """Compare original 2699-entry checkpoint without changing its SHA expectations.

    The new M4.2 comparison records validated Finder differences separately;
    it never rewrites or overrides any old verification outcome.
    """
    original=read(FROZEN/'protected.before.json')
    scientific={}; tracking=[]
    for name,digest in original.items():
        if Path(name).name=='.DS_Store':
            current=metadata(ROOT/name)
            tracking.append(dict(path=name,historical_sha256=digest,current=current,
                differs=current['sha256']!=digest,policy='new-m42-comparison-only'))
        else: scientific[name]=digest
    verify(scientific)
    write(log,dict(original_manifest_sha256=sha(FROZEN/'protected.before.json'),
        scientific_files=len(scientific),scientific_all_match=True,os_metadata=tracking,
        historical_verifiers_modified=False))
    return dict(scientific_files=len(scientific),scientific_all_match=True,
        metadata_differences=sum(r['differs'] for r in tracking))
