"""M3.2 ps正式權限恢復：沿用原監控器，C3→C4各一次；舊停止全保留。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import m32_experiments as x
from scripts import m32_sensitivity as s
from scripts import m32_final_recovery as prior
from scripts import m32_analysis as analysis
from scripts import m32_monitor_preflight as monitor
from scripts import m3_diagnose as m
from scripts import record_command
from scripts.m32_metadata_policy import metadata_policy, EXACT_PATHS

SUITE = s.SUITE
RECOVERY = SUITE/'resume_04'
HISTORY = prior.LINKS + ['resume_03/'+name for name in [
    'authorization.json','system_stopped.json','status/C2.json',
    'final_manifest.json','final_provenance.json','stop_preservation/summary.json']]
TOOLS = ['m32_permission_recovery.py','m32_monitor_preflight.py','m32_experiments.py',
         'm32_metadata_policy.py','m32_sensitivity.py','m32_analysis.py','record_command.py']


def authorization(suite):
    suite = Path(suite); recovery = suite/'resume_04'
    if (recovery/'system_stopped.json').exists():
        raise RuntimeError('Permission recovery stopped; no automatic retry')
    value = x.read(recovery/'authorization.json')
    if (value['remaining_conditions'] != ['C3','C4'] or value['rerun_B0_through_C2'] is not False
        or value['metadata_exclusion'] != list(EXACT_PATHS)
        or value['rss_limit_gib'] != 3 or value['monitor'] != 'unchanged record_command.py ps'
        or set(value['historical_links']) != set(HISTORY)):
        raise RuntimeError('Invalid permission recovery scope')
    for name,digest in value['historical_links'].items():
        if x.sha(suite/name) != digest: raise RuntimeError('Historical permission recovery link changed: '+name)
    x.verify_hashes(value['tool_sha256'])
    x.verify_hashes(value['permission_probe_sha256'])
    if not x.read(recovery/'authorized_monitor_probe/probe.json')['passed']:
        raise RuntimeError('No verified monitor permission evidence')
    return value


def terminal(suite, condition):
    suite = Path(suite); authorization(suite)
    directory = suite/('resume_04' if condition in ['C3','C4'] else 'resume_03' if condition == 'C2' else 'resume_02')
    record = x.read(directory/'status'/(condition+'.json'))
    allowed = [prior.C2_STATUS] if condition == 'C2' else ['Success','Failed Registration']
    if record['condition'] != condition or record['status'] not in allowed or not record['integrity_verified']:
        raise RuntimeError('Invalid terminal evidence: '+condition)
    x.verify_hashes(record['evidence_sha256'])
    return record


def initialize(probe):
    if RECOVERY.exists(): raise FileExistsError('Permission recovery already exists')
    probe = Path(probe).resolve()
    result = x.read(probe/'probe.json')
    required = ['shell_ps','python_subprocess_ps','recorder_self_rss','continuous_child_rss',
                'guard_termination','monitor_failure_termination']
    if not result['passed'] or any(not result['results'][k]['passed'] for k in required):
        raise RuntimeError('Permission/function probe incomplete')
    files = [p for root in [ROOT/'research_outputs',ROOT/'experiments',m.DATA]
             for p in root.rglob('*') if p.is_file()] + [ROOT/n for n in x.CORE]
    RECOVERY.mkdir(); (RECOVERY/'status').mkdir()
    m.dump(RECOVERY/'protected.before.json',m.fingerprint(files))
    s.environment(x.read(SUITE/'suite.json'))
    for path in [SUITE/'protected.before.json',SUITE/'resume_02/protected.before.json',
        SUITE/'resume_03/protected.before.json',SUITE/'resume_03/final_manifest.json',
        Path(prior.item_for('C2')['output'])/'protected.before.json']:
        x.verify_hashes(x.read(path))
    previous = x.read(SUITE/'resume_03/authorization.json')
    for name,digest in previous['historical_links'].items():
        if x.sha(SUITE/name) != digest: raise RuntimeError('Previous historical link changed')
    x.verify_hashes(previous['prior_recovery_links'])
    for c in ['B0','B1','B2','C1','C2']:
        directory = SUITE/('resume_03' if c == 'C2' else 'resume_02')
        record = x.read(directory/'status'/(c+'.json'))
        if not record['integrity_verified']: raise RuntimeError('Existing evidence not verified')
        x.verify_hashes(record['evidence_sha256'])
    if x.read(SUITE/'resume_03/status/C2.json')['status'] != prior.C2_STATUS:
        raise RuntimeError('C2 audit not complete')
    for c in ['C3','C4']:
        item = prior.item_for(c)
        if Path(item['output']).exists() or Path(item['experiment']).exists():
            raise FileExistsError('Condition already started: '+c)
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
        raise RuntimeError('Expected clean main before execution')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip() != 'main':
        raise RuntimeError('Expected main')
    shutil.copytree(probe,RECOVERY/'authorized_monitor_probe')
    shutil.copytree('/tmp/physicalai-m32-rss-sandbox-probe-01',RECOVERY/'sandbox_monitor_probe')
    for name in EXACT_PATHS:
        shutil.copyfile(ROOT/name,RECOVERY/(name.split('/')[0]+'_DS_Store_before.bin'))
    m.dump(RECOVERY/'authorization.json',dict(
        user_instruction='M3.2 C3／C4執行環境權限修復與恢復：正式權限機制、原ps監控與3GiB護欄、既有C2審計不重跑、C3後C4各一次',
        remaining_conditions=['C3','C4'],rerun_B0_through_C2=False,
        metadata_exclusion=list(EXACT_PATHS),rss_limit_gib=3,monitor='unchanged record_command.py ps',
        registration_failure_policy='preserve_verify_then_continue',
        historical_links={n:x.sha(SUITE/n) for n in HISTORY},
        prior_authorization_sha256=x.sha(SUITE/'resume_03/authorization.json'),
        B0_postprocess_output=previous['B0_postprocess_output'],
        permission_probe_sha256=m.fingerprint([p for p in (RECOVERY/'authorized_monitor_probe').rglob('*') if p.is_file()]),
        tool_sha256=m.fingerprint([ROOT/'scripts'/n for n in TOOLS]),
        git_commit=s.git_commit(),created_unix=time.time()))
    print('Permission recovery initialized; historical C2 audit and all stops preserved.',flush=True)


def receipt(condition,status,evidence,**details):
    target = RECOVERY/'status'/(condition+'.json')
    if target.exists(): raise FileExistsError('Existing terminal status')
    m.dump(target,dict(condition=condition,status=status,integrity_verified=True,
        evidence_sha256=m.fingerprint(evidence),**details))


def run(condition):
    value = authorization(SUITE)
    if condition not in ['C3','C4']: raise ValueError('Only fixed C3/C4 allowed')
    if s.git_commit() != value['git_commit']: raise RuntimeError('Execution commit changed')
    s.environment(x.read(SUITE/'suite.json'))
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    for c in ['B0','B1','B2','C1','C2'] + (['C3'] if condition == 'C4' else []): terminal(SUITE,c)
    if shutil.disk_usage(ROOT).free < 2*2**30: raise RuntimeError('Insufficient disk')
    # 在同一已核准的執行環境，先驗證實際子程序監控，之後才Declare。
    monitor.probe(RECOVERY/('monitor_before_'+condition))
    x.condition_prepare(SUITE,condition)
    item = prior.item_for(condition); out = Path(item['output'])
    os.environ['M32_PERMISSION_AUTH_SHA256'] = x.sha(RECOVERY/'authorization.json')
    execution = record_command.run([sys.executable,str(Path(__file__)), 'observe','--condition',condition],out/'command',3)
    if execution['resource_guard']['reason']: raise RuntimeError('Actual reconstruction monitor/resource failure')
    if execution['exit_code'] != 0:
        summary,evidence = s.preserve_failure(item,out/'failed_registration')
        x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
        receipt(condition,'Failed Registration',evidence,failure=summary['failure'],mean_l2_m=None)
        return
    samples = [x.json.loads(line) for line in (out/'command/memory_samples.jsonl').read_text().splitlines()]
    if len(samples) < 3 or any(row['rss_bytes'] <= 0 for row in samples):
        raise RuntimeError('Missing actual reconstruction RSS sampling')
    x.finalize(out); analysis.analyze(out)
    x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
    summary = x.read(out/'analysis/summary.json')
    receipt(condition,'Success',[p for root in [out,Path(item['experiment'])] for p in root.rglob('*') if p.is_file()],
        mean_l2_m=summary['mean_l2_m'],full_frames=191,rss_sample_count=len(samples))
    print('Success: '+condition,flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['initialize','run','observe','compare','verify'])
    parser.add_argument('--probe'); parser.add_argument('--condition',choices=['C3','C4'])
    args = parser.parse_args()
    journal = Path(tempfile.mkdtemp(prefix='m32-permission-metadata-'))/'checks.jsonl'
    try:
        with metadata_policy(journal):
            if args.mode == 'initialize': initialize(args.probe)
            elif args.mode == 'run': run(args.condition)
            elif args.mode == 'observe':
                authorization(SUITE)
                if os.environ.get('M32_PERMISSION_AUTH_SHA256') != x.sha(RECOVERY/'authorization.json'):
                    raise RuntimeError('Missing explicit permission recovery context')
                x.observe(prior.item_for(args.condition)['output'])
            elif args.mode == 'compare':
                authorization(SUITE)
                for group in ['B','C','all']: analysis.compare(SUITE,group,RECOVERY/(group+'_comparison'))
            else:
                authorization(SUITE); s.environment(x.read(SUITE/'suite.json'))
                count = x.verify_hashes(x.read(RECOVERY/'protected.before.json'))
                for c,_,_ in x.CONDITIONS: terminal(SUITE,c)
                m.dump(RECOVERY/'final_integrity.json',dict(scientific_integrity_verified=True,
                    protected_existing_files=count,original_stops_preserved=True,metadata_exclusion=list(EXACT_PATHS),
                    snapshot=subprocess.check_output(['git','rev-parse','snapshot/pre-implementation'],text=True).strip()))
    except BaseException:
        if RECOVERY.exists() and not (RECOVERY/'system_stopped.json').exists():
            m.dump(RECOVERY/'system_stopped.json',dict(mode=args.mode,condition=args.condition,
                traceback=traceback.format_exc(),unix=time.time(),action='STOP; no automatic retry'))
        raise
    finally:
        if RECOVERY.exists() and journal.exists():
            target = RECOVERY/'metadata_checks'; target.mkdir(exist_ok=True)
            shutil.copyfile(journal,target/(args.mode+'_'+str(args.condition)+'_'+str(time.time_ns())+'.jsonl'))
