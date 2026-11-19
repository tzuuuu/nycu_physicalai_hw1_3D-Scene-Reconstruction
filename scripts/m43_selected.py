"""Single-attempt official P2-B Selected CLI with inherited 3GiB RSS guard.

run: native Terminal mandatory preflight -> permanent lock -> exactly one CLI
-> read-only validation/plots. check-sandbox never launches reconstruction.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time
import traceback
import uuid
import xml.etree.ElementTree as ET
import numpy as np
from scripts import m43_analysis as a
from scripts.m42_integrity import ROOT, read, verify, inventory, compare, frozen_capture, historical_sources
from scripts.m42_monitor import write, run as guarded, process_table
from scripts.m4_capture_check import sha, no_links
from scripts.m42_baseline import environment, resource_check, source_inventory, git, SNAPSHOT

READY=ROOT/'docs/implementation/m43/readiness.json'
DOC=ROOT/'docs/implementation/M4_Phase2_P2B_Selected_Acceptance.md'
TESTS=['tests/test_m42_monitor.py','tests/test_m42_observer.py','tests/test_m42_integrity.py',
       'tests/test_m42_baseline.py','tests/test_m43_selected.py']


def argv(experiment=a.EXP,query=a.QUERY):
    return [str(ROOT/'reconstruct.py'),'--experiment',str(experiment),'--version','open3d',
        '--voxel-size','0.05','--seed','0','--down-voxel','0.05','--no-vis',
        '--selection-query',str(query),'--override-experiment']


def execute_selected(experiment,query,output):
    """Same Observer and call-to-return boundary as M4.2, new CLI arguments only."""
    from scripts.m42_observer import Observer
    output=Path(output);output.mkdir(exist_ok=False)
    if sys.getprofile() is not None: raise RuntimeError('Existing profiler')
    observer=Observer(output); prior=sys.argv;sys.argv=argv(experiment,query)
    status='failed'
    try:
        sys.setprofile(observer)
        runpy.run_path(str(ROOT/'reconstruct.py'),run_name='__main__')
        status='official_cli_returned'
    except BaseException:
        (output/'failure.traceback.txt').write_text(traceback.format_exc());raise
    finally:
        sys.setprofile(None);sys.argv=prior
        write(output/'observer_summary.json',dict(status=status,reconstruct_calls=observer.calls,
            frame_events=sum(e['kind']=='frame' for e in observer.events),pair_events=len(observer.transforms),
            valid_transform_pose_prefix_frames=len(observer.poses) if observer.events else 0,
            full_processed_frames=len(observer.poses) if status=='official_cli_returned' else None,
            reconstruction_s_with_observation=observer.elapsed,return_observer_overhead_s=observer.overhead_s,
            timing='Same M4.2 function timer; return export occurs after timer stops; total observer overhead includes export'))
    return observer


def frozen():
    ready=read(READY);verify(ready['sources']);verify(ready['historical_anchors'])
    if sha(a.PREP/'manifest.json')!=ready['preparation_manifest_sha256']:
        raise RuntimeError('Preparation manifest anchor changed')
    verify(read(a.PREP/'manifest.json')['scientific'])
    if sha(a.SPEC)!=ready['rule_sha256'] or sha(a.QUERY)!=ready['query_sha256']:
        raise RuntimeError('Frozen selection changed')
    spec=read(a.SPEC)
    with (a.BASE/'factors.csv').open() as f:
        import csv
        frames,_,_,_=a.selection(list(csv.DictReader(f)),a.lines(a.BASE/'observation/transforms.jsonl'))
    import api
    actual=api.frames_from_sparql_query(api.read_experiment(str(a.TTL)),str(a.QUERY))
    if actual!=spec['selected_indices'] or frames!=actual or actual!=sorted(set(actual)) or actual[0]!=1 or actual[-1]!=320:
        raise RuntimeError('Selection/index freeze mismatch')
    if git('rev-parse','snapshot/pre-implementation')!=SNAPSHOT: raise RuntimeError('Snapshot changed')
    if git('status','--porcelain','--untracked-files=all'): raise RuntimeError('Require clean committed source tree; never auto stash/reset')
    return dict(frames=len(actual),factors=8*len(actual)-6,rule_sha256=sha(a.SPEC),query_sha256=sha(a.QUERY),
        git_commit=git('rev-parse','HEAD'),snapshot=SNAPSHOT,branch=git('branch','--show-current'))


def absent():
    no_links(a.OUT)
    if a.OUT.exists(): raise FileExistsError('Single formal attempt lock exists; no automatic retry')
    import api
    exp=api.read_experiment(str(a.TTL))
    run=api.data_run_iri(exp['exp_name'],'selected')
    if (exp['exp_iri'],api.HW1.hasRun,run) in exp['graph']: raise RuntimeError('Selected Run already exists')
    if (a.EXP/'reconstruction_selected.png').exists(): raise FileExistsError('Selected image already exists')
    return dict(unique_output=str(a.OUT),absent=True)


def tests(out,native):
    env=dict(os.environ)
    env.pop('M42_SKIP_NATIVE',None)
    if native: env['M42_REQUIRE_NATIVE']='1'
    else: env['M42_SKIP_NATIVE']='1'
    result=subprocess.run([sys.executable,'-m','pytest','-q',*TESTS,'--junitxml='+str(out/'selftests.xml')],
        cwd=ROOT,env=env,capture_output=True,text=True)
    (out/'selftests.stdout.log').write_text(result.stdout);(out/'selftests.stderr.log').write_text(result.stderr)
    suites=list(ET.parse(out/'selftests.xml').getroot().iter('testsuite'))
    counts={k:sum(int(s.get(k,'0')) for s in suites) for k in ['tests','failures','errors','skipped']}
    if result.returncode or counts['failures'] or counts['errors'] or counts['tests']==0 or (native and counts['skipped']):
        raise RuntimeError('Required selftests failed: '+repr(counts))
    return dict(native=native,counts=counts,passed=True)


def preflight(native=True):
    out=ROOT/'research_outputs'/('m43_preflight_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    out.mkdir(exist_ok=False);checks=[]
    def check(name,fn):
        try: checks.append(dict(name=name,passed=True,details=fn()))
        except BaseException: checks.append(dict(name=name,passed=False,error=traceback.format_exc()))
    check('frozen_rule_sources_query_indices_git_snapshot',frozen)
    check('single_attempt_and_no_selected',absent)
    check('frozen_capture_baseline_manifests_seal_core_ontology_pixi',a.baseline_check)
    check('environment',environment)
    check('capacity_disk_memory',resource_check)
    def permission():
        if not native: raise PermissionError('Known Codex sandbox ps denial; native Mac Terminal required. No formal run.')
        return dict(pids=len(process_table()))
    check('actual_process_tree_permission',permission)
    check('monitor_observer_selected_export_tests',lambda:tests(out,native))
    from scripts.m42_capacity import capacity
    def cap():
        value=capacity(a.CAPTURE);write(out/'map_capacity.json',value)
        if not value['passed']: raise RuntimeError('Conservative fullbatch capacity bound failed')
        return value
    check('full_map_capacity_conservative_320_bound',cap)
    def query():
        command=[sys.executable,str(ROOT/'api.py'),'query',str(a.EXP),'--query-file',str(a.QUERY),'--format','csv']
        before=sha(a.TTL);p=subprocess.run(command,capture_output=True,text=True)
        (out/'official_query.csv').write_text(p.stdout);(out/'official_query.stderr.log').write_text(p.stderr)
        import csv,io
        indices=[int(r['frameIndex']) for r in csv.DictReader(io.StringIO(p.stdout))]
        if p.returncode or indices!=read(a.SPEC)['selected_indices'] or sha(a.TTL)!=before:
            raise RuntimeError('Official query/TTL invariance failed')
        return dict(argv=command,count=len(indices),ttl_unchanged=True)
    check('official_read_only_query',query)
    def protected():
        # Experiment checked separately by exact graph delta + immutable files.
        value=inventory([ROOT/'eval/_data',ROOT/'experiments',ROOT/'research_outputs'],exclude=[out,a.OUT,a.EXP])
        write(out/'protected.before.json',value)
        write(out/'experiment.before.json',inventory([a.EXP]))
        return dict(scientific_files=len(value['scientific']))
    check('preservation_snapshot',protected)
    check('final_frozen_capture_and_source_recheck',lambda:dict(capture=len(frozen_capture()),frozen=frozen()))
    value=dict(passed=all(c['passed'] for c in checks),checks=checks,native=native,formal_started=False,
               utc=datetime.now(timezone.utc).isoformat(),argv=[sys.executable,*argv()])
    write(out/'preflight.json',value);print(json.dumps(value,indent=2),flush=True)
    return out,value


def graph_delta(before,after,frames):
    """Allow only official Selected run triples, preserve every historical triple."""
    import api
    from rdflib import Graph, RDF
    old=Graph().parse(data=Path(before).read_text(),format='turtle')
    exp=api.read_experiment(str(after));new=exp['graph'];run=api.data_run_iri(exp['exp_name'],'selected')
    student_before,_=api._split_sections(Path(before).read_text())
    student_after,_=api._split_sections(Path(after).read_text())
    if student_before!=student_after or set(old)-set(new): raise RuntimeError('Historical declaration/graph removed or changed')
    added=set(new)-set(old)
    allowed={RDF.type,api.HW1.selectionMode,api.HW1.mapMeanL2,api.HW1.runFrameCount,
             api.HW1.usedFrame,api.HW1.spliceCount,api.HW1.maxGapLength}
    for s,p,o in added:
        if (s,p,o)==(exp['exp_iri'],api.HW1.hasRun,run):continue
        if s!=run or p not in allowed: raise RuntimeError('Unexpected Turtle mutation')
    g=new
    if set(g.objects(run,api.HW1.usedFrame))!={api.frame_iri(exp['batch_name'],i) for i in frames}:
        raise RuntimeError('UsedFrame mismatch')
    if int(g.value(run,api.HW1.runFrameCount))!=len(frames) or g.value(run,api.HW1.selectionMode)!=api.HW1.GoodSegments:
        raise RuntimeError('Selected Run count/mode mismatch')
    original_count=sum(api.read_experiment(str(before))['factor_counts'].values())
    if sum(exp['factor_counts'].values())!=original_count: raise RuntimeError('Historical factors modified')
    return dict(historical_triples=len(old),added_selected_triples=len(added),baseline_factors_retained=original_count,
        declaration_bytes_unchanged=True,seal_valid=True)


def preservation(preflight_out):
    frozen_capture();historical_sources();verify(read(READY)['sources'])
    verify(read(a.PREP/'manifest.json')['scientific'])
    before=read(preflight_out/'protected.before.json')
    after=inventory([ROOT/'eval/_data',ROOT/'experiments',ROOT/'research_outputs'],exclude=[preflight_out,a.OUT,a.EXP])
    count=compare(before,after,a.OUT/'os_metadata.before_after.jsonl')
    old=read(preflight_out/'experiment.before.json')
    new=inventory([a.EXP]); permitted=[str(p.relative_to(ROOT)) for p in [a.TTL,a.EXP/'reconstruction.png',a.EXP/'reconstruction_selected.png']]
    for item in permitted:
        old['scientific'].pop(item,None);new['scientific'].pop(item,None)
    compare(old,new,a.OUT/'experiment_os_metadata.jsonl')
    if sha(a.TTL)!=sha(a.OUT/'baseline.before.ttl'):
        graph_delta(a.OUT/'baseline.before.ttl',a.TTL,read(a.SPEC)['selected_indices'])
    write(a.OUT/'preservation.json',dict(passed=True,protected_scientific_files=count,
        permitted_official_mutations=permitted,all_other_experiment_files_unchanged=True))


def worker():
    pre=read(a.OUT/'preregistration.json')
    verify(pre['tracked_sources']); frozen_capture()
    if sha(a.TTL)!=pre['baseline_ttl_sha256']:raise RuntimeError('TTL changed before worker')
    write(a.OUT/'execution.started.json',dict(unix=time.time(),argv=[sys.executable,*argv()],single_attempt=True))
    execute_selected(a.EXP,a.QUERY,a.OUT/'observation')


def run():
    pre_out,pre=preflight(True)
    if not pre['passed']:return 2
    a.OUT.mkdir(exist_ok=False)  # Permanent lock even if worker startup fails.
    shutil.copyfile(a.TTL,a.OUT/'baseline.before.ttl')
    shutil.copyfile(a.EXP/'reconstruction.png',a.OUT/'reconstruction.before.png')
    write(a.OUT/'preregistration.json',dict(rule=read(a.SPEC),rule_sha256=sha(a.SPEC),
        query_sha256=sha(a.QUERY),preflight=str(pre_out),preflight_sha256=sha(pre_out/'preflight.json'),
        baseline_ttl_sha256=sha(a.TTL),tracked_sources=source_inventory(),git_commit=git('rev-parse','HEAD'),
        authorization='User M4.3: one official selected after all preflight passes; no retries; P2-C cancelled',
        frozen_capture_sha256=frozen_capture(),rss_limit_bytes=3*2**30))
    status='Selected attempt reserved; no retry';details={}
    try:
        execution=guarded([sys.executable,'-m','scripts.m43_selected','_worker'],a.OUT/'command')
        if not execution['passed']:
            from scripts.m42_baseline import failure_evidence
            details=failure_evidence(a.OUT,execution);status='Selected failed; real failure preserved; no retry'
        else:
            post=guarded([sys.executable,'-m','scripts.m43_selected','_postprocess'],a.OUT/'postprocess_command')
            if not post['passed']:raise RuntimeError('Selected returned; validation/postprocess failed; no reconstruction retry')
            details=read(a.OUT/'comparison.json');status='Selected complete; scientific checks passed; human visual acceptance pending'
    except BaseException:
        details['error']=traceback.format_exc();(a.OUT/'runner_failure.traceback.txt').write_text(details['error'])
        status='Selected stopped; acceptance withheld; no retry'
    try:preservation(pre_out)
    except BaseException:
        details['preservation_error']=traceback.format_exc();status='Source integrity stop; acceptance withheld'
    write(a.OUT/'terminal_status.json',dict(status=status,details=details,unix=time.time()))
    # Append a new outcome section; never rewrite old decision/history text.
    with DOC.open('a') as f:
        f.write('\n\n## Terminal 正式執行結果（自動新增）\n\n狀態：**'+status+'**。\n\n```json\n'+json.dumps(details,ensure_ascii=False,indent=2)+'\n```\n\n完整證據：`research_outputs/m43_p2b_selected_01/`。人工檢視圖表與最終驗收仍須完成；未提交最終作業。\n')
    manifest=inventory([a.OUT]);manifest['scientific'][str(DOC.relative_to(ROOT))]=sha(DOC)
    write(a.OUT/'manifest.json',manifest)
    print(status+'\nEvidence: '+str(a.OUT),flush=True)
    return 0 if status.startswith('Selected complete') else 1


if __name__=='__main__':
    os.chdir(ROOT)
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['run','check-sandbox','_worker','_postprocess'])
    mode=p.parse_args().mode
    if mode=='run':sys.exit(run())
    if mode=='check-sandbox':_,v=preflight(False);sys.exit(0 if v['passed'] else 2)
    if mode=='_worker':worker()
    if mode=='_postprocess':
        from scripts.m43_results import results
        results(a.OUT)
