"""Read-only M4.3 audit/recovery. Never invokes a reconstruction entrypoint."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import numpy as np
from scripts import m43_analysis as a
from scripts.m42_integrity import ROOT,read,verify,inventory,compare,frozen_capture,historical_sources
from scripts.m42_monitor import write
from scripts.m4_capture_check import sha

CLOSE=ROOT/'research_outputs/m43_p2b_closeout_01'
DOC=ROOT/'docs/implementation/M4_Phase2_P2B_Selected_Acceptance.md'


def verify_aliases(hashes,aliases):
    for name,digest in hashes.items():
        path=aliases.get(name,ROOT/name)
        if not path.is_file() or sha(path)!=digest:raise RuntimeError('Historical artifact mismatch: '+name)
    return len(hashes)


def audit(label):
    src=a.OUT;config=read(src/'preregistration.json');pre=Path(config['preflight'])
    old=read(src/'manifest.json')['scientific']
    formal_count=verify_aliases(old,{str(DOC.relative_to(ROOT)):CLOSE/'terminal_generated_acceptance_original.md'})
    if sha(pre/'preflight.json')!=config['preflight_sha256']:raise RuntimeError('Preflight SHA mismatch')
    pf=read(pre/'preflight.json')
    if not pf['native'] or not pf['passed'] or not all(c['passed'] for c in pf['checks']):raise RuntimeError('Native preflight not passed')
    tests=next(c['details']['counts'] for c in pf['checks'] if c['name']=='monitor_observer_selected_export_tests')
    if tests!={'tests':40,'failures':0,'errors':0,'skipped':0}:raise RuntimeError('Native tests mismatch')
    aliases={str(a.TTL.relative_to(ROOT)):src/'baseline.before.ttl',
             str((a.EXP/'reconstruction.png').relative_to(ROOT)):src/'reconstruction.before.png'}
    baseline_close_count=verify_aliases(read(a.CLOSE/'manifest.json')['scientific'],aliases)
    aliases2=dict(aliases)
    aliases2['docs/implementation/M4_Phase2_P2A_Baseline_Acceptance.md']=a.CLOSE/'runner_generated_acceptance_original.md'
    baseline_count=verify_aliases(read(a.BASE/'manifest.json')['scientific'],aliases2)
    frozen_capture();core=historical_sources()
    verify(read(a.PREP/'manifest.json')['scientific'])
    if sha(a.SPEC)!=config['rule_sha256'] or sha(a.QUERY)!=config['query_sha256']:
        raise RuntimeError('Original frozen selection changed')
    modified=[]
    allowed={'scripts/m43_results.py','tests/test_m43_selected.py',str(DOC.relative_to(ROOT))}
    for name,digest in config['tracked_sources'].items():
        if sha(ROOT/name)!=digest:
            if name not in allowed:raise RuntimeError('Unexpected execution-source change: '+name)
            original=subprocess.check_output(['git','show',config['git_commit']+':'+name],cwd=ROOT)
            if hashlib.sha256(original).hexdigest()!=digest:raise RuntimeError('Execution source archive mismatch')
            saved=CLOSE/'execution_sources'/name;saved.parent.mkdir(parents=True,exist_ok=True)
            if saved.exists():
                if saved.read_bytes()!=original:raise RuntimeError('Execution source snapshot changed')
            else:saved.write_bytes(original)
            modified.append(dict(path=name,execution_sha256=digest,current_sha256=sha(ROOT/name),
                reason='Post-run offline precision fix/regression test/final document; never changed formal execution'))
    protected=read(pre/'protected.before.json')
    current=inventory([ROOT/'eval/_data',ROOT/'experiments',ROOT/'research_outputs'],exclude=[pre,src,a.EXP,CLOSE])
    protected_count=compare(protected,current,CLOSE/('os_metadata_'+label+'.jsonl'))
    from scripts.m43_selected import graph_delta
    delta=graph_delta(src/'baseline.before.ttl',a.TTL,config['rule']['selected_indices'])
    observation=read(src/'observation/observer_summary.json')
    if observation['reconstruct_calls']!=1 or observation['full_processed_frames']!=204:raise RuntimeError('Not exactly one complete selected call')
    monitors=[]
    for directory in ['command','postprocess_command']:
        run=read(src/directory/'execution.json');samples=a.lines(src/directory/'rss.jsonl')
        if directory=='command' and (not run['passed'] or run['exit_code']!=0 or run['reason'] is not None):raise RuntimeError('Reconstruction failed')
        if len(samples)!=run['samples'] or max(r['tree_rss_bytes'] for r in samples)!=run['peak_tree_rss_bytes']:raise RuntimeError('RSS aggregate mismatch')
        if any(r['tree_rss_bytes']!=sum(p['rss_bytes'] for p in r['pids']) for r in samples):raise RuntimeError('RSS tree sum mismatch')
        if run['peak_tree_rss_bytes']>=3*2**30:raise RuntimeError('RSS guard exceeded')
        if read(src/directory/'watchdog.json')['status']!='disarmed_after_workload_exit':raise RuntimeError('Watchdog not disarmed')
        monitors.append(dict(stage=directory,**run,max_sample_gap_s=float(np.diff([r['elapsed_s'] for r in samples]).max())))
    recovery_monitors=[]
    if label=='final':
        for name in ['analysis_command','details_command']:
            run=read(CLOSE/name/'execution.json');samples=a.lines(CLOSE/name/'rss.jsonl')
            if not run['passed'] or run['reason'] is not None or run['exit_code']!=0:
                raise RuntimeError('Offline recovery failed: '+name)
            if len(samples)!=run['samples'] or max(r['tree_rss_bytes'] for r in samples)!=run['peak_tree_rss_bytes']:
                raise RuntimeError('Offline recovery RSS count mismatch')
            if any(r['tree_rss_bytes']!=sum(p['rss_bytes'] for p in r['pids']) for r in samples):
                raise RuntimeError('Offline recovery RSS sum mismatch')
            if run['peak_tree_rss_bytes']>=3*2**30 or read(CLOSE/name/'watchdog.json')['status']!='disarmed_after_workload_exit':
                raise RuntimeError('Offline recovery guard failed')
            recovery_monitors.append(dict(stage=name,**run))
    output=dict(passed=True,formal_manifest_verified_items=formal_count,baseline_closeout_verified_items=baseline_close_count,
        baseline_manifest_verified_items=baseline_count,protected_scientific_files=protected_count,frozen_capture_files=642,
        execution_git_commit=config['git_commit'],native_tests=tests,rule_sha256=sha(a.SPEC),query_sha256=sha(a.QUERY),
        turtle=delta,original_execution_sources_preserved=modified,core_sha256=core,monitors=monitors,
        recovery_monitors=recovery_monitors,reconstruction_calls=1,hidden_reconstruction=False,scope='Only offline analysis repaired; formal attempt and failed postprocess history preserved')
    write(CLOSE/('audit_'+label+'.json'),output)
    return output


def analyze():
    audit('before_analysis')
    from scripts.m43_results import results
    out=CLOSE/'analysis';out.mkdir(exist_ok=False)
    results(out,source=a.OUT)
    audit('after_analysis')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['analyze','audit-final'])
    mode=parser.parse_args().mode
    if mode=='analyze':analyze()
    else:audit('final')
