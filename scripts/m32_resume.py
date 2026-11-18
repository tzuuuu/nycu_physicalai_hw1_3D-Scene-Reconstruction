"""明確核准後恢復M3.2：B0只做後置作業，剩餘六條件各執行一次。"""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import m32_experiments as x
from scripts import m32_analysis as analysis
from scripts import record_command
from scripts import m3_diagnose as m
from scripts.m31_ablation import snapshot
from scripts.m31_analysis import cumulative, read_jsonl
import numpy as np

SUITE=ROOT/'research_outputs/m32_20261118_suite_01'
RESUME=SUITE/'resume_01'


def recover():
    if (SUITE/'resume_authorization.json').exists() or RESUME.exists():
        raise FileExistsError('Resume already registered; do not repeat')
    plan=x.read(SUITE/'suite.json'); b0=plan['conditions'][0]
    source=Path(b0['output']); exp_path=Path(b0['experiment']); ttl=exp_path/(exp_path.name+'.ttl')
    x.verify_hashes(x.read(SUITE/'protected.before.json'))
    x.verify_hashes(x.read(source/'protected.before.json'))
    x.verify_hashes(plan['core_sha256'])
    if m.capture_digest()!=plan['capture_sha256']:
        raise RuntimeError('Capture changed')
    exp,rows,l2=x.validate_evidence(ttl,source/'observation',list(range(1,192)))
    execution=x.read(source/'command/execution.json')
    if execution['exit_code'] or execution['resource_guard']['reason']:
        raise RuntimeError('Original B0 execution failed')
    RESUME.mkdir()
    protected=[p for root in [ROOT/'research_outputs',ROOT/'experiments',m.DATA]
               for p in root.rglob('*') if p.is_file() and RESUME not in p.parents]
    protected += [ROOT/n for n in x.CORE]
    m.dump(RESUME/'protected.before.json',m.fingerprint(protected))
    target=RESUME/'B0_postprocess'; target.mkdir()
    auth={'user_instruction':'核准繼續，恢復後置作業與剩餘六組',
        'remaining_conditions':['B1','B2','C1','C2','C3','C4'],
        'original_stop_sha256':x.sha(SUITE/'suite_stopped.json'),
        'original_suite_sha256':x.sha(SUITE/'suite.json'),
        'B0_postprocess_output':str(target),'B0_reconstruction_repeated':False,
        'resumed_unix':time.time(),'resume_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'scope':'Only missing B0 postprocessing and remaining six original conditions; preserve failed evidence'}
    m.dump(SUITE/'resume_authorization.json',auth)
    with (m.BASE/'factor_occurrences.csv').open() as f:
        comparison=m.compare_factors(read_jsonl(source/'observation/events.jsonl'),list(csv.DictReader(f)))
    old=cumulative(read_jsonl(ROOT/'research_outputs/m3_20261118_diagnostic_02/transforms.jsonl'))
    result=x.historical_comparison(l2,x.read(m.BASE/'validation.json')['mean_l2_raw_m'],comparison,
                                   old,np.load(source/'observation/camera_poses.npy'))
    m.dump(target/'historical_comparison.json',result)
    if not result['matched']:
        raise RuntimeError('B0 differs from historical M2')
    before=x.sha(ttl)
    x.run_logged([sys.executable,str(ROOT/'api.py'),'explore',str(exp_path)],target,'explore')
    stdout=x.run_logged([sys.executable,str(ROOT/'api.py'),'query',str(exp_path),'--query-file',
                         str(exp_path/'queries/audit.rq'),'--format','csv'],target,'query')
    if [int(r['frameIndex']) for r in csv.DictReader(io.StringIO(stdout))]!=list(range(1,192)) or x.sha(ttl)!=before:
        raise RuntimeError('B0 official postprocess validation failed')
    plots=sorted(str(p.relative_to(exp_path)) for p in (exp_path/'plots').glob('*.html'))
    if len(plots)!=4:
        raise RuntimeError('Missing official Explore outputs')
    count=x.verify_hashes(x.read(RESUME/'protected.before.json'))
    if snapshot(m.EXP/(m.EXP.name+'.ttl'))!=x.read(SUITE/'original_experiment.json'):
        raise RuntimeError('Original formal workspace changed')
    shutil.copytree(exp_path,target/'official_after')
    m.dump(target/'integrity.after.json',{'passed':True,'complete':exp['completion'],'frames':191,'pairs':190,
        'factor_count':len(rows),'seal_valid':True,'baseline_only':True,'retained_fraction':1.,
        'mean_l2_m':l2,'protected_files_unchanged':count,'plots':plots,'ttl_sha256':x.sha(ttl),
        'capture_sha256':m.capture_digest(),'B0_reconstruction_repeated':False,
        'original_execution_commit':x.read(source/'preregistration.json')['git_commit'],
        'postprocess_commit':auth['resume_git_commit']})
    analysis.analyze(source)
    m.dump(target/'manifest.json',m.fingerprint([p for p in target.rglob('*') if p.is_file()]))
    print('B0 postprocessing completed; original failed JSON and stop marker preserved.',flush=True)


def run(condition):
    x.resume_authorization(SUITE)
    if condition not in ['B1','B2','C1','C2','C3','C4']:
        raise ValueError('Only remaining six conditions authorized')
    if condition=='C1' and not (RESUME/'B_comparison/comparison.json').is_file():
        raise RuntimeError('B comparison must complete before C')
    if shutil.disk_usage(ROOT).free<2*2**30:
        raise RuntimeError('Insufficient disk; preserve evidence and stop')
    record_command._rss_bytes(os.getpid())  # 先驗證監測，不先啟動配準。
    x.condition_prepare(SUITE,condition)
    item=next(i for i in x.read(SUITE/'suite.json')['conditions'] if i['condition']==condition)
    output=Path(item['output'])
    result=record_command.run([sys.executable,str(ROOT/'scripts/m32_experiments.py'),
                               'observe','--output',str(output)],output/'command',3)
    if result['exit_code'] or result['resource_guard']['reason']:
        raise RuntimeError('Formal execution/resource guard failed; no retry')
    x.finalize(output)
    analysis.analyze(output)
    print('Completed '+condition,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['recover','run']); p.add_argument('--condition',choices=['B1','B2','C1','C2','C3','C4'])
    a=p.parse_args()
    try:
        if a.mode=='recover': recover()
        else: run(a.condition)
    except BaseException:
        if not (SUITE/'resume_failed.json').exists():
            m.dump(SUITE/'resume_failed.json',{'mode':a.mode,'condition':a.condition,
                'traceback':traceback.format_exc(),'unix':time.time(),'action':'STOP; no automatic retry'})
        raise
