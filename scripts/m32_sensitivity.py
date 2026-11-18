"""M3.2剩餘五條件排程：保存真實配準失敗後繼續，系統異常仍停止。"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import m32_experiments as x
from scripts import m32_analysis as analysis
from scripts import m3_diagnose as m
from scripts import record_command
from scripts.m31_ablation import snapshot
from scripts.m31_analysis import read_jsonl, cumulative
from scripts.m32_failure_audit import classify
import numpy as np

SUITE=ROOT/'research_outputs/m32_20261118_suite_01'
RECOVERY=SUITE/'resume_02'
REMAINING=['B2','C1','C2','C3','C4']
HISTORICAL=['suite_stopped.json','resume_failed.json','resume_authorization.json']


def environment(plan):
    x.verify_hashes(plan['core_sha256'])
    x.validate_frames(m.DATA)
    if m.capture_digest()!=plan['capture_sha256'] or os.environ.get('OMP_NUM_THREADS')!='1':
        raise RuntimeError('Capture/thread mismatch')
    if {n:importlib.metadata.version(n) for n in plan['versions']}!=plan['versions']:
        raise RuntimeError('Environment version mismatch')
    if snapshot(m.EXP/(m.EXP.name+'.ttl'))!=x.read(SUITE/'original_experiment.json'):
        raise RuntimeError('Original Baseline/Selected workspace changed')


def receipt(condition,status,evidence,**details):
    value={'condition':condition,'status':status,'integrity_verified':True,
           'evidence_sha256':m.fingerprint([Path(p) for p in evidence]),**details}
    m.dump(RECOVERY/'status'/(condition+'.json'),value)
    return value


def registration_failure(trace,execution,observer,transforms):
    """只有與核心回傳證據相符的明確失敗才能繼續；未知例外不可分類為演算法失敗。"""
    if execution['exit_code']!=1 or execution['resource_guard']['reason'] or observer['status']!='failed' or observer['reconstruct_calls']!=1:
        raise RuntimeError('Not a verified registration failure')
    accepted,failed=classify(transforms)
    match=re.fullmatch(r'RuntimeError: (RANSAC|ICP) failed for (\d+)->(\d+): fitness=(\S+), RMSE=(\S+), correspondences=(\d+)',trace.strip().splitlines()[-1])
    if not match or len(failed)!=1 or failed[0] is not transforms[-1]:
        raise RuntimeError('Unexpected exception or failure evidence')
    stage,left,right,fitness,rmse,count=match.groups(); failed=failed[0]
    prefix='coarse' if stage=='RANSAC' else 'icp'
    if (int(left),int(right))!=(failed['prev_stem'],failed['stem']):
        raise RuntimeError('Failure pair mismatch')
    if (float(fitness),float(rmse),int(count))!=(failed[prefix+'_fitness'],failed[prefix+'_rmse'],failed[prefix+'_correspondences']):
        raise RuntimeError('Failure values mismatch')
    return {'stage':stage,'previous':int(left),'current':int(right),'accepted_pairs':len(accepted),'message':match[0]}


def preserve_failure(item,target):
    output=Path(item['output']); exp=Path(item['experiment']); ttl=exp/(exp.name+'.ttl')
    target=Path(target); target.mkdir(exist_ok=False)
    execution=x.read(output/'command/execution.json'); obs=x.read(output/'observation/observer_summary.json')
    transforms=read_jsonl(output/'observation/transforms.jsonl')
    failure=registration_failure((output/'observation/failure.traceback.txt').read_text(),execution,obs,transforms)
    events=read_jsonl(output/'observation/events.jsonl')
    frames=[e for e in events if e['kind']=='frame']; end=failure['current']
    if [e['stem'] for e in frames]!=list(range(1,end+1)) or [(t['prev_stem'],t['stem']) for t in transforms]!=list(zip(range(1,end),range(2,end+1))):
        raise RuntimeError('Incomplete partial identity evidence')
    if obs['frame_events']!=len(frames) or obs['pair_events']!=len(transforms):
        raise RuntimeError('Incomplete observer counts')
    if m.api.is_assessed(str(ttl)) or ttl.read_bytes()!=(output/'declaration.before.ttl').read_bytes():
        raise RuntimeError('Failed run was sealed or declaration changed')
    if (output/'observation/official_evaluation.json').exists():
        raise RuntimeError('Failed run cannot have official full evaluation')
    x.verify_hashes(x.read(output/'protected.before.json'))
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    environment(x.read(SUITE/'suite.json'))
    factors=[{'factor':name,'previous':e.get('prev_stem'),'current':e['stem'],'value':e[field]}
             for e in events for field,name in m.FIELDS.items() if field in e]
    m.write_csv(target/'partial_factors.csv',factors)
    accepted,_=classify(transforms)
    np.save(target/'offline_accepted_prefix_poses.npy',cumulative(accepted))
    summary={'condition':item['condition'],'status':'Failed Registration','failure':failure,
             'full191_mean_l2_m':None,'preprocessed_frames':len(frames),'accepted_prefix_frames':len(accepted)+1,
             'observed_pair_count':len(transforms),'partial_factor_values':len(factors),
             'execution':execution,'observer':obs,'declaration_unsealed':True,'no_baseline_run':True,
             'capture_sha256':m.capture_digest(),'integrity_verified':True}
    m.dump(target/'summary.json',summary)
    evidence=[p for root in [output,exp,target] for p in root.rglob('*') if p.is_file()]
    return summary,evidence


def initialize():
    if RECOVERY.exists(): raise FileExistsError('Recovery already registered')
    plan=x.read(SUITE/'suite.json'); environment(plan)
    x.verify_hashes(x.read(SUITE/'protected.before.json'))
    b0,b1=plan['conditions'][:2]
    x.validate_evidence(Path(b0['experiment'])/(b0['name']+'.ttl'),Path(b0['output'])/'observation',list(range(1,192)))
    if not x.read(SUITE/'resume_01/B0_postprocess/integrity.after.json')['passed']:
        raise RuntimeError('B0 official workflow incomplete')
    for item in plan['conditions'][2:]:
        if Path(item['experiment']).exists() or Path(item['output']).exists():
            raise FileExistsError('Cannot confirm unused condition: '+item['condition'])
    if shutil.disk_usage(ROOT).free<2*2**30: raise RuntimeError('Insufficient disk')
    protected=[p for root in [ROOT/'research_outputs',ROOT/'experiments',m.DATA] for p in root.rglob('*') if p.is_file()]
    protected += [ROOT/n for n in x.CORE]
    RECOVERY.mkdir(); (RECOVERY/'status').mkdir()
    m.dump(RECOVERY/'protected.before.json',m.fingerprint(protected))
    auth={'user_instruction':'正式核准恢復執行剩餘五個條件：B2、C1、C2、C3、C4；真實配準失敗保存且驗證後可繼續，系統異常仍停止',
          'remaining_conditions':REMAINING,'registration_failure_policy':'preserve_verify_then_continue',
          'B0_B1_rerun_authorized':False,'suite_sha256':x.sha(SUITE/'suite.json'),
          'historical_links':{name:x.sha(SUITE/name) for name in HISTORICAL},
          'B0_postprocess_output':str(SUITE/'resume_01/B0_postprocess'),
          'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'created_unix':time.time(),'rss_limit_gib':3}
    m.dump(RECOVERY/'authorization.json',auth)
    receipt('B0','Success',[p for root in [Path(b0['output']),Path(b0['experiment']),SUITE/'resume_01/B0_postprocess'] for p in root.rglob('*') if p.is_file()],mean_l2_m=3.174055104788137,full_frames=191)
    summary,evidence=preserve_failure(b1,RECOVERY/'B1_failure_validation')
    receipt('B1','Failed Registration',evidence,failure=summary['failure'],mean_l2_m=None)
    print('Policy initialized; B0 and B1 audited without rerunning. Five conditions remain.',flush=True)


def run(condition):
    auth=x.sensitivity_authorization(SUITE)
    if condition not in REMAINING: raise ValueError('B0/B1 repetition or extra condition forbidden')
    if git_commit()!=auth['git_commit']: raise RuntimeError('Execution commit changed')
    plan=x.read(SUITE/'suite.json'); environment(plan)
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    if shutil.disk_usage(ROOT).free<2*2**30: raise RuntimeError('Insufficient disk')
    record_command._rss_bytes(os.getpid())
    x.condition_prepare(SUITE,condition)
    item=next(i for i in plan['conditions'] if i['condition']==condition); output=Path(item['output'])
    result=record_command.run([sys.executable,str(ROOT/'scripts/m32_experiments.py'),'observe','--output',str(output)],output/'command',3)
    if result['resource_guard']['reason']: raise RuntimeError('Resource/monitoring failure')
    if result['exit_code']!=0:
        summary,evidence=preserve_failure(item,output/'failed_registration')
        receipt(condition,'Failed Registration',evidence,failure=summary['failure'],mean_l2_m=None)
        print('Failed Registration preserved; next preregistered condition allowed: '+condition,flush=True)
        return
    x.finalize(output); analysis.analyze(output)
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    summary=x.read(output/'analysis/summary.json')
    receipt(condition,'Success',[p for root in [output,Path(item['experiment'])] for p in root.rglob('*') if p.is_file()],mean_l2_m=summary['mean_l2_m'],full_frames=191)
    print('Success: '+condition,flush=True)


def git_commit():
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('mode',choices=['initialize','run']); p.add_argument('--condition',choices=REMAINING)
    a=p.parse_args()
    try:
        if a.mode=='initialize': initialize()
        else: run(a.condition)
    except BaseException:
        if RECOVERY.exists() and not (RECOVERY/'system_stopped.json').exists():
            m.dump(RECOVERY/'system_stopped.json',{'mode':a.mode,'condition':a.condition,'traceback':traceback.format_exc(),'unix':time.time(),'action':'STOP SYSTEM/INTEGRITY; no automatic retry'})
        raise
