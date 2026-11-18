"""最終有限恢復：C2只讀審計，C3→C4各一次；保留所有原停止紀錄。"""
import argparse
import csv
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import m32_experiments as x
from scripts import m32_sensitivity as s
from scripts import m32_analysis as a
from scripts import m32_status_review as review
from scripts import m3_diagnose as m
from scripts import record_command
from scripts.m32_metadata_policy import metadata_policy, EXACT_PATHS
from scripts.m31_analysis import read_jsonl, cumulative
from scripts.validate_baseline import summarize_rows
import numpy as np

SUITE = s.SUITE
RECOVERY = SUITE/'resume_03'
C2_STATUS = 'Reconstruction Completed / Scientific Integrity Verified / Historical Metadata Guard Stop Preserved'
LINKS = s.HISTORICAL + ['suite.json', 'resume_02/authorization.json', 'resume_02/system_stopped.json']
PRIOR_LINKS = ['research_outputs/m32_20261118_final_recovery_stop_01/'+n for n in
               ['system_stopped.json','manifest.json','final_provenance.json','final_manifest.json']]


def authorization(suite):
    suite = Path(suite); recovery = suite/'resume_03'
    if (recovery/'system_stopped.json').exists():
        raise RuntimeError('Final recovery system stopped; no automatic retry')
    auth = x.read(recovery/'authorization.json')
    if (auth['remaining_conditions'] != ['C3', 'C4'] or auth['C2_reconstruction_authorized'] is not False
            or auth['metadata_exclusion'] != list(EXACT_PATHS)
            or set(auth['historical_links']) != set(LINKS)
            or set(auth['prior_recovery_links']) != set(PRIOR_LINKS)):
        raise RuntimeError('Invalid final recovery scope')
    for name, digest in auth['historical_links'].items():
        if x.sha(suite/name) != digest:
            raise RuntimeError('Historical marker changed: '+name)
    x.verify_hashes(auth['prior_recovery_links'])
    x.verify_hashes(auth['tool_sha256'])
    return auth


def receipt(condition, status, evidence, **details):
    target = RECOVERY/'status'/(condition+'.json')
    if target.exists(): raise FileExistsError('Terminal record already exists')
    m.dump(target, dict(condition=condition, status=status, integrity_verified=True,
        evidence_sha256=m.fingerprint(evidence), **details))


def item_for(condition):
    return next(i for i in x.read(SUITE/'suite.json')['conditions'] if i['condition'] == condition)


def protected_files():
    return [p for root in [ROOT/'research_outputs', ROOT/'experiments', m.DATA]
            for p in root.rglob('*') if p.is_file() and RECOVERY not in p.parents] + [ROOT/n for n in x.CORE]


def initialize():
    if RECOVERY.exists(): raise FileExistsError('Final recovery already exists')
    files = protected_files()
    RECOVERY.mkdir(); (RECOVERY/'status').mkdir()
    m.dump(RECOVERY/'protected.before.json', m.fingerprint(files))
    plan = x.read(SUITE/'suite.json'); s.environment(plan)
    # 先審查全部既有清單；任何非核准差異都在建立恢復授權前停止。
    inventories = {}
    for label, path in [('initial', SUITE/'protected.before.json'),
                         ('resume02', SUITE/'resume_02/protected.before.json'),
                         ('C2', Path(item_for('C2')['output'])/'protected.before.json')]:
        hashes = x.read(path); delta = review.differences(hashes)
        if any(d['path'] not in EXACT_PATHS or d['after'] is None or (ROOT/d['path']).is_symlink() for d in delta):
            raise RuntimeError('Unauthorized prior file change: '+repr(delta))
        x.verify_hashes(hashes)
        inventories[label] = dict(count=len(hashes), differences=delta)
    for c in ['B0','B1','B2','C1']: x.terminal_receipt(SUITE, c)
    for c in ['C3','C4']:
        i = item_for(c)
        if Path(i['output']).exists() or Path(i['experiment']).exists():
            raise FileExistsError('Condition already used: '+c)
    if x.read(SUITE/'resume_02/system_stopped.json')['condition'] != 'C2':
        raise RuntimeError('Unexpected original stop')
    m.dump(RECOVERY/'historical_differences.json', inventories)
    for name in EXACT_PATHS:
        shutil.copyfile(ROOT/name, RECOVERY/(name.split('/')[0]+'_DS_Store_at_resume.bin'))
    previous = x.read(SUITE/'resume_02/authorization.json')
    for name, digest in previous['historical_links'].items():
        if x.sha(SUITE/name) != digest: raise RuntimeError('Historical authorization link changed')
    git_state = subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
    if git_state or subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip() != 'main':
        raise RuntimeError('Expected clean main branch')
    m.dump(RECOVERY/'authorization.json', dict(
        user_instruction='M3.2 最終恢復授權（OS Metadata 精確排除）：僅experiments/.DS_Store與research_outputs/.DS_Store；C2唯讀審計後C3再C4各一次',
        remaining_conditions=['C3','C4'], C2_reconstruction_authorized=False,
        metadata_exclusion=list(EXACT_PATHS), registration_failure_policy='preserve_verify_then_continue',
        historical_links={n:x.sha(SUITE/n) for n in LINKS},
        prior_recovery_links=m.fingerprint([ROOT/n for n in PRIOR_LINKS]),
        B0_postprocess_output=previous['B0_postprocess_output'],
        prior_authorization_sha256=x.sha(SUITE/'resume_02/authorization.json'),
        tool_sha256=m.fingerprint([ROOT/'scripts'/n for n in [
            'm32_final_recovery.py','m32_metadata_policy.py','m32_experiments.py',
            'm32_sensitivity.py','m32_analysis.py','record_command.py']]),
        git_commit=s.git_commit(), suite_sha256=x.sha(SUITE/'suite.json'), created_unix=time.time()))
    print('Final recovery initialized; C2 has not been reconstructed.', flush=True)


def audit_c2():
    authorization(SUITE); plan = x.read(SUITE/'suite.json'); s.environment(plan)
    out = Path(item_for('C2')['output']); exp = Path(item_for('C2')['experiment'])
    target = RECOVERY/'C2_audit'
    if target.exists(): raise FileExistsError('C2 audit already exists')
    target.mkdir()
    counts = {}
    for label, path in [('suite', SUITE/'protected.before.json'),
        ('resume02', SUITE/'resume_02/protected.before.json'), ('C2',out/'protected.before.json'),
        ('final_recovery',RECOVERY/'protected.before.json')]:
        counts[label] = x.verify_hashes(x.read(path))
    official, rows, l2 = x.validate_evidence(exp/(exp.name+'.ttl'), out/'observation', list(range(1,192)))
    if abs(l2-3.165352438552)>1e-12: raise RuntimeError('C2 value changed')
    p = x.read(out/'preregistration.json'); actual = x.read(out/'observation/actual_reconstruct_arguments.json')
    expected = dict(data_root=str(m.DATA), version='open3d',voxel_size=.05,build_cloud=True,
                    frames=list(range(1,192)),down_voxel=.05,registration_seed=2)
    if actual != expected: raise RuntimeError('C2 actual arguments mismatch')
    expected_algorithm = dict(plan['algorithm_control'])
    expected_algorithm.update(registration_voxel_m=.05,seed=2,normal_radius_m=.1,
        fpfh_radius_m=.25,ransac_distance_m=1.5*.05,icp_distance_m=1.5*.05)
    if p['algorithm'] != expected_algorithm or p['versions'] != plan['versions'] or p['OMP_NUM_THREADS'] != '1':
        raise RuntimeError('C2 preregistration controls mismatch')
    actual_pairs = x.read(out/'observation/actual_pairs.json')
    if actual_pairs != [dict(previous=i,current=i+1,voxel=.05,seed=2) for i in range(1,191)]:
        raise RuntimeError('C2 actual pair identity mismatch')
    transforms = read_jsonl(out/'observation/transforms.jsonl')
    np.testing.assert_allclose(cumulative(transforms),np.load(out/'observation/camera_poses.npy'),rtol=0,atol=1e-12)
    execution = x.read(out/'command/execution.json'); observer = x.read(out/'observation/observer_summary.json')
    if (execution['exit_code'] != 0 or execution['resource_guard']['reason'] or
        observer['reconstruct_calls'] != 1 or observer['frame_events'] != 191 or observer['pair_events'] != 190):
        raise RuntimeError('C2 execution evidence mismatch')
    for mode in ['declare','explore','query']:
        if x.read(out/(mode+'.json'))['exit_code'] != 0: raise RuntimeError('C2 official command failure')
    frames = [int(r['frameIndex']) for r in csv.DictReader(io.StringIO((out/'query.stdout.log').read_text()))]
    if frames != list(range(1,192)) or len(list((exp/'plots').glob('*.html'))) < 4:
        raise RuntimeError('C2 Explore/Query evidence missing')
    for name in ['reconstruction.png','reconstruction_baseline.png']:
        if not (exp/name).is_file(): raise RuntimeError('Missing C2 map')
    if summarize_rows(rows) != x.read(out/'factor_summary.json'): raise RuntimeError('C2 factor summary mismatch')
    if (out/'integrity.after.json').exists() or (SUITE/'resume_02/status/C2.json').exists():
        raise RuntimeError('Unexpected historical finalize receipt')
    a.analyze(out, target/'analysis')
    summary = dict(status=C2_STATUS, scientific_integrity_verified=True, original_finalize_succeeded=False,
        full_workflow_complete=False, original_stop_preserved=True, frames=191,pairs=190,factors=len(rows),
        mean_l2_m=l2, seal_valid=True, actual_arguments=actual, protected_counts=counts,
        original_stop_sha256=x.sha(SUITE/'resume_02/system_stopped.json'))
    m.dump(target/'summary.json', summary)
    # 原C2全目錄只讀；新增快照與SHA一律寫入恢復目錄。
    shutil.copytree(exp,target/'official_snapshot')
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    evidence = [p for root in [out,exp,target] for p in root.rglob('*') if p.is_file()]
    receipt('C2', C2_STATUS, evidence, mean_l2_m=l2, full_frames=191,
            analysis_directory=str(target/'analysis'), original_finalize_succeeded=False)
    print(C2_STATUS, flush=True)


def run(condition):
    auth = authorization(SUITE)
    if condition not in ['C3','C4']: raise ValueError('Only fixed C3/C4 authorized')
    if s.git_commit() != auth['git_commit']: raise RuntimeError('Execution commit changed')
    s.environment(x.read(SUITE/'suite.json'))
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    if shutil.disk_usage(ROOT).free < 2*2**30: raise RuntimeError('Insufficient disk')
    record_command._rss_bytes(os.getpid())
    x.condition_prepare(SUITE,condition)
    item = item_for(condition); out = Path(item['output'])
    # 子程序只繼承固定政策日誌路徑；不改老師核心或正式CLI。
    argv = [sys.executable,str(ROOT/'scripts/m32_final_recovery.py'),'observe','--condition',condition]
    # record_command繼承環境，子程序由相同授權檢查限制。
    os.environ['M32_FINAL_METADATA_POLICY'] = x.sha(RECOVERY/'authorization.json')
    result = record_command.run(argv,out/'command',3)
    if result['resource_guard']['reason']: raise RuntimeError('Resource/monitoring failure')
    if result['exit_code'] != 0:
        # 沿用已核准的嚴格配準失敗分類，保全位置仍是該新條件。
        summary,evidence = s.preserve_failure(item,out/'failed_registration')
        x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
        receipt(condition,'Failed Registration',evidence,failure=summary['failure'],mean_l2_m=None)
        return
    x.finalize(out); a.analyze(out)
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    summary = x.read(out/'analysis/summary.json')
    receipt(condition,'Success',[p for root in [out,Path(item['experiment'])] for p in root.rglob('*') if p.is_file()],
        mean_l2_m=summary['mean_l2_m'],full_frames=191)
    print('Success: '+condition,flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['initialize','audit-c2','run','observe','compare','verify'])
    parser.add_argument('--condition',choices=['C3','C4'])
    args = parser.parse_args()
    # 活躍日誌在暫存目錄追加，結束後獨立保全；不將正在寫入的日誌當凍結產物。
    journal_dir = Path(tempfile.mkdtemp(prefix='physicalai-m32-metadata-'))
    journal = journal_dir/'checks.jsonl'
    try:
        with metadata_policy(journal):
            if args.mode == 'initialize': initialize()
            elif args.mode == 'audit-c2': audit_c2()
            elif args.mode == 'observe':
                authorization(SUITE)
                if os.environ.get('M32_FINAL_METADATA_POLICY') != x.sha(RECOVERY/'authorization.json'):
                    raise RuntimeError('Missing explicit metadata policy context')
                x.observe(item_for(args.condition)['output'])
            elif args.mode == 'run': run(args.condition)
            elif args.mode == 'compare':
                authorization(SUITE)
                for group in ['B','C','all']: a.compare(SUITE,group,RECOVERY/(group+'_comparison'))
            else:
                authorization(SUITE); s.environment(x.read(SUITE/'suite.json'))
                counts = x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
                for c,_,_ in x.CONDITIONS: x.terminal_receipt(SUITE,c)
                m.dump(RECOVERY/'final_integrity.json',dict(scientific_integrity_verified=True,
                    protected_existing_files=counts,original_stops_preserved=True,
                    snapshot_pre_implementation=subprocess.check_output(['git','rev-parse','snapshot/pre-implementation'],text=True).strip()))
    except BaseException:
        if RECOVERY.exists() and not (RECOVERY/'system_stopped.json').exists():
            m.dump(RECOVERY/'system_stopped.json',dict(mode=args.mode,condition=args.condition,
                traceback=traceback.format_exc(),unix=time.time(),action='STOP; no automatic retry'))
        raise

    finally:
        if RECOVERY.exists() and journal.exists():
            logs = RECOVERY/'metadata_checks'
            logs.mkdir(exist_ok=True)
            shutil.copyfile(journal,logs/(args.mode+'_'+str(args.condition)+'_'+str(time.time_ns())+'.jsonl'))
