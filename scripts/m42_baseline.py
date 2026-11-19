"""One Terminal command: mandatory preflight -> one official P2-A pass -> validate.

No automatic reconstruction retries. Existing formal output is an irreversible
attempt lock, even if declaration or registration fails. No historical verifier
is patched, and no existing scientific file is overwritten.
"""
import argparse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import importlib.metadata as md
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import uuid
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import m42_integrity as integrity
from scripts.m42_integrity import read, verify
from scripts.m4_capture_check import sha, no_links
from scripts.m42_monitor import write, run as guarded, process_table

NAME='p2_114753116_a01_baseline_01'
CAPTURE=ROOT/'eval/_data/second_floor/114753116/P2_A_01'
EXPERIMENT=ROOT/'experiments'/NAME
FORMAL=ROOT/'research_outputs/m42_p2_a01_baseline_01'
ENGINEERING=ROOT/'research_outputs/m42_engineering_01'
READINESS=ROOT/'research_outputs/m42_monitor_cleanup_fix_01/readiness.json'
SNAPSHOT='291209750bd8ecf84f337112c9b92307e6be192a'
TESTS=['tests/test_m42_monitor.py','tests/test_m42_observer.py','tests/test_m42_integrity.py',
       'tests/test_m42_baseline.py']


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def source_inventory():
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    return {n:sha(no_links(ROOT/n)) for n in names if n and (ROOT/n).is_file()}


def clean_git():
    if git('branch','--show-current')!='main' or git('status','--porcelain','--untracked-files=all'):
        raise RuntimeError('Require clean main; never stash/reset/delete to obtain it')
    if git('rev-parse','snapshot/pre-implementation')!=SNAPSHOT: raise RuntimeError('Snapshot mismatch')
    ready=read(READINESS)
    if git('rev-parse','HEAD')!=ready['git_commit']: raise RuntimeError('Prepared commit changed')
    verify(ready['tracked_sources'])
    if sha(ENGINEERING/'authorization.txt')!=ready['authorization_sha256']:
        raise RuntimeError('Authorization bytes changed')
    return dict(commit=git('rev-parse','HEAD'),branch='main',snapshot=SNAPSHOT,clean=True)


def resource_check():
    free=shutil.disk_usage(ROOT).free
    result=subprocess.run(['/usr/bin/vm_stat'],capture_output=True,text=True,check=True)
    import re
    page=int(re.search(r'page size of (\d+) bytes',result.stdout).group(1))
    entries={key:int(value) for key,value in re.findall(r'^([^:\n]+):\s+(\d+)\.',result.stdout,re.M)}
    available=sum(entries.get(key,0) for key in ['Pages free','Pages inactive','Pages speculative'])*page
    if free<4*2**30 or available<2*2**30:
        raise RuntimeError('Require >=4 GiB free disk and >=2 GiB free+inactive+speculative RAM')
    return dict(disk_free_bytes=free,reclaimable_memory_bytes=available,vm_stat=result.stdout,
        limitation='Reclaimable memory is a snapshot and not reserved; live RSS guard remains mandatory')


def environment():
    expected={'numpy':'1.26.4','open3d':'0.18.0','opencv-python':'4.8.0.76',
              'scipy':'1.13.1','rdflib':'7.1.4','panel':'1.4.5','bokeh':'3.4.3'}
    actual={n:md.version(n) for n in expected}
    if actual!=expected or sys.version_info[:3]!=(3,9,23) or os.environ.get('OMP_NUM_THREADS')!='1':
        raise RuntimeError('Version/thread environment mismatch: '+repr(actual))
    return dict(versions=actual,python=sys.version,executable=sys.executable,OMP_NUM_THREADS='1')


def workspace_absent():
    for path in [EXPERIMENT,FORMAL]:
        no_links(path)
        if path.exists(): raise FileExistsError('Single-attempt lock/workspace already exists: '+str(path))
    return dict(experiment=str(EXPERIMENT),output=str(FORMAL),absent=True)


def test_suite(out):
    env=dict(os.environ,M42_REQUIRE_NATIVE='1'); env.pop('M42_SKIP_NATIVE',None)
    result=subprocess.run([sys.executable,'-m','pytest','-q',*TESTS,'--junitxml='+str(out/'selftests.xml')],
        cwd=ROOT,env=env,capture_output=True,text=True)
    (out/'selftests.stdout.log').write_text(result.stdout)
    (out/'selftests.stderr.log').write_text(result.stderr)
    if not (out/'selftests.xml').exists(): raise RuntimeError('Selftest report missing')
    suites=list(ET.parse(out/'selftests.xml').getroot().iter('testsuite'))
    counts={k:sum(int(s.get(k,'0')) for s in suites) for k in ['tests','failures','errors','skipped']}
    if result.returncode or counts['failures'] or counts['errors'] or counts['skipped'] or counts['tests']==0:
        raise RuntimeError('Mandatory selftests must all pass with zero skips: '+repr(counts))
    return dict(passed=True,counts=counts)


def preflight(native_required=True):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=ROOT/'research_outputs'/('m42_preflight_'+stamp)
    out.mkdir(exist_ok=False)
    items=[]
    def check(name,function):
        try:
            value=function(); items.append(dict(name=name,passed=True,details=value)); return value
        except BaseException:
            items.append(dict(name=name,passed=False,error=traceback.format_exc())); return None
    state=check('git_snapshot_and_prepared_sources',clean_git)
    check('workspace_and_single_attempt',workspace_absent)
    check('frozen_capture_642',lambda:dict(files=len(integrity.frozen_capture())))
    check('accepted_core_ontology_pixi_and_m41_evidence',integrity.historical_sources)
    check('historical_2699_checkpoint',lambda:integrity.historical_preservation(out/'historical_preservation.json'))
    env=check('environment',environment)
    check('disk_and_available_memory',resource_check)
    # Permission is probed once; tests run only if it succeeds.
    def permissions():
        if not native_required:
            raise PermissionError('Known Codex sandbox ps denial; do not repeat probe. Native Terminal validation pending.')
        return dict(visible_pids=len(process_table()))
    permission=check('actual_process_tree_permission',permissions)
    tests=check('monitor_observer_map_selftests',lambda:test_suite(out)) if permission else None
    if permission is None:
        items.append(dict(name='monitor_observer_map_selftests',passed=False,
            error='Not run: actual process-table permission unavailable. No workload launched.'))
    from scripts.m42_capacity import capacity
    def map_capacity():
        value=capacity(CAPTURE)
        write(out/'map_capacity.json',value)
        if not value['passed']: raise RuntimeError('Full returned map capacity planning failed')
        return value
    check('full_return_map_capacity',map_capacity)
    def runtime():
        import utils
        from scripts.m42_observer import expected_counts
        intr,pairs,scale=utils._capture_inputs(str(CAPTURE),None)
        frames=[int(Path(d).stem) for r,d in pairs]
        if frames!=list(range(1,321)): raise RuntimeError('Exact original frames 1..320 required')
        p=subprocess.run([sys.executable,str(ROOT/'reconstruct.py'),'--help'],capture_output=True,text=True)
        (out/'official_cli_help.txt').write_text(p.stdout+p.stderr)
        if p.returncode or '--down-voxel' not in p.stdout: raise RuntimeError('Official CLI unavailable')
        return dict(counts=expected_counts(len(frames)),first_frame=frames[0],intrinsics=intr,depth_scale=scale,
            official_argv=official_argv())
    check('official_runtime_and_original_first_frame',runtime)
    protected=check('preservation_snapshot',lambda:integrity.inventory(
        [ROOT/'eval/_data',ROOT/'experiments',ROOT/'research_outputs'],exclude=[out]))
    if protected is not None: write(out/'protected.before.json',protected)
    # Recheck after tests/capacity; no declaration yet.
    check('final_capture_and_source_recheck',lambda:dict(files=len(integrity.frozen_capture()),git=clean_git()))
    value=dict(passed=all(r['passed'] for r in items),checks=items,unix=time.time(),
        declaration_created=False,formal_first_pass_started=False,output=str(out),environment=env,git=state)
    write(out/'preflight.json',value)
    print(json.dumps(value,ensure_ascii=False,indent=2),flush=True)
    return out,value


def official_argv():
    return [sys.executable,str(ROOT/'reconstruct.py'),'--experiment',str(EXPERIMENT),
        '--version','open3d','--voxel-size','0.05','--seed','0','--down-voxel','0.05','--no-vis']


def declare(out,preflight_out):
    import api
    workspace_absent()
    pre=read(preflight_out/'preflight.json')
    if not pre['passed']: raise RuntimeError('No formal declaration without all preflight checks')
    out.mkdir(exist_ok=False)  # Permanent single-attempt lock after preflight passes.
    config=dict(experiment=NAME,floor=2,capture=str(CAPTURE),frames=320,pairs=319,expected_factors=2554,
        registration_voxel_m=.05,seed=0,icp='Open3D Point-to-Plane',map_only_down_voxel_m=.05,
        rss_limit_bytes=3*2**30,OMP_NUM_THREADS='1',official_argv=official_argv(),
        preflight=str(preflight_out),preflight_sha256=sha(preflight_out/'preflight.json'),
        git_commit=git('rev-parse','HEAD'),tracked_source_sha256=source_inventory(),
        frozen_capture_sha256=integrity.frozen_capture(),authorization_sha256=sha(ENGINEERING/'authorization.txt'),
        hypothesis='Full capture may show weak support or ambiguous geometry near transitions; no outcome is preclassified.',
        prediction='No guaranteed Mean L2 improvement; retain the single outcome, including registration failure.')
    write(out/'preregistration.json',config)
    shutil.copyfile(ENGINEERING/'authorization.txt',out/'authorization.txt')
    result=subprocess.run([sys.executable,str(ROOT/'api.py'),'declare','--name',NAME,
        '--data-dir',str(CAPTURE),'--floor','2'],capture_output=True,text=True)
    (out/'declare.stdout.log').write_text(result.stdout); (out/'declare.stderr.log').write_text(result.stderr)
    if result.returncode: raise RuntimeError('Official Declaration failed')
    ttl=EXPERIMENT/(NAME+'.ttl')
    text=ttl.read_text().replace('TODO: one line naming the condition this experiment tests',
        'P2-A full-capture first-pass baseline; 320 frames; fixed voxel 0.05 and seed 0')
    text=text.replace('pipeline: TODO','pipeline: Unknown raw factor patterns; no qualification thresholds. Context:')
    text=text.replace('baseline: TODO','baseline: Unknown Mean L2; no improvement is guaranteed. Context:')
    text='# M4.2 preregistration_sha256: '+sha(out/'preregistration.json')+'\n'+text
    ttl.write_text(text)
    decl=api.read_declaration(str(ttl))
    if Path(decl['batch_path']).resolve()!=CAPTURE: raise RuntimeError('Declaration capture mismatch')
    (out/'declaration.before.ttl').write_bytes(ttl.read_bytes())
    return config


def worker(out):
    out=Path(out)
    config=read(out/'preregistration.json')
    verify(config['tracked_source_sha256']); integrity.frozen_capture()
    ttl=EXPERIMENT/(NAME+'.ttl')
    if ttl.read_bytes()!=(out/'declaration.before.ttl').read_bytes(): raise RuntimeError('Declaration bytes changed')
    write(out/'execution.started.json',dict(unix=time.time(),argv=official_argv(),single_attempt=True))
    from scripts.m42_observer import execute_cli
    execute_cli(EXPERIMENT,out/'observation')


def postprocess(out):
    from scripts.m42_results import results
    results(out,EXPERIMENT,CAPTURE)


def preservation(preflight_out,out):
    integrity.frozen_capture(); integrity.historical_sources()
    config=read(out/'preregistration.json')
    verify(config['tracked_source_sha256'])
    before=read(preflight_out/'protected.before.json')
    after=integrity.inventory([ROOT/'eval/_data',ROOT/'experiments',ROOT/'research_outputs'],
        exclude=[preflight_out,out,EXPERIMENT])
    count=integrity.compare(before,after,out/'os_metadata.before_after.jsonl')
    write(out/'integrity.after.json',dict(passed=True,protected_scientific_files=count,
        frozen_capture_files=642,core_unchanged=True,tracked_sources_unchanged=True))


def acceptance(out,status,details):
    # Written only after post-run source verification; expected final document update.
    document=ROOT/'docs/implementation/M4_Phase2_P2A_Baseline_Acceptance.md'
    relative=str(out.relative_to(ROOT))
    content=f'''# M4.2 — P2-A First-Pass Baseline 驗收

日期：{datetime.now(ZoneInfo('Asia/Taipei')).date()}（臺灣；UTC時間見證據）。

狀態：**{status}**。

工程工具與授權：本次使用者已授權完整工程準備及 Preflight 全通過後的一次正式執行。未修改教師核心、Ontology、Pixi、Capture 或歷史 SHA 政策。

正式證據目錄：`{relative}`。逐項 Preflight 位置記於 `preregistration.json`；正式命令、來源 SHA、凍結 Capture 642項 SHA、Declaration、Observer、程序樹 RSS 與 watchdog 紀錄均在該目錄。

正式設定：Floor 2、320張、319對、2554筆預期因素、registration voxel=0.05m、seed=0、Open3D Point-to-Plane、map-only voxel=0.05m、OMP_NUM_THREADS=1、程序樹 RSS 3 GiB。

實際結果：

```json
{json.dumps(details,ensure_ascii=False,indent=2)}
```

程序樹監測使用 ps 的 PID／PPID／PGID／RSS，每0.5秒加總存活後代及保留群組；RSS 包含重複計算的共享頁，屬保守取樣指標，不能保證瞬間峰值不超限。獨立 watchdog 在監測程序失聯後最多約8秒內終止本次群組。監測器與 watchdog 自身不計入科學工作負載 RSS。

成功產物完整地圖為同次正式 Pipeline 回傳、經逐影格0.05m地圖降採樣及官方去天花板後的全部點／色，分開串流儲存為 NPY；繪圖另用明列 stride 的取樣，沒有以15萬點樣本替代正式地圖。首相機座標與 float64 shape／SHA 見 map_summary.json。GT 僅於重建完成後評估；無最佳擬合。

成功時見 validation.json、baseline_comparison.csv、per_frame_l2.csv、factors.csv、factor_statistics.json、figure_manifest.json、figures/、candidate_questions.md 與官方 Explore。影像為英文報告素材，並非最終英文報告。空間分區是地圖範圍象限，不冒稱真實房間；缺少逐段路線註記與完整場景表面 GT，不能宣稱全樓層絕對完整率。失敗時只保留真實完成前綴、部分回傳及停止原因，不建立假成功 Seal、完整 Mean L2 或因素。

歷史 Phase 1／M4.1 的中繼資料停止及自我雜湊缺陷原樣保留。新 M4.2 採雙層保全；經檔名、一般檔案與 Finder 檔頭／file 類型確認的 .DS_Store 獨立記錄前後 SHA，其餘科學來源嚴格比對。

至此停止；未啟動 P2-B、P2-C、新參數／seed、Experiment D、Bonus、最終英文報告或 Submission ZIP。
'''
    document.write_text(content)


def failure_evidence(out,execution):
    def records(name):
        path=out/'observation'/name
        rows=[]; parse_errors=[]
        if path.exists():
            for index,line in enumerate(path.read_text().splitlines()):
                try: rows.append(json.loads(line))
                except json.JSONDecodeError: parse_errors.append(index+1)
        return rows,parse_errors
    progress,partial=records('progress.jsonl')
    events,event_partial=records('events.jsonl')
    coarse,coarse_partial=records('ransac_returns.jsonl')
    transforms,transform_partial=records('transforms.jsonl')
    summary=dict(execution=execution,complete_mean_l2_m=None,full_factors_verified=False,
        last_progress=progress[-1] if progress else None,
        preprocessed_frames=sum(r['kind']=='frame' for r in events),
        returned_ransac_pairs=len(coarse),returned_icp_pairs=len(transforms),
        finite_positive_support_transform_pairs=sum(r['accepted_by_core'] for r in transforms),
        partial_json_lines=dict(progress=partial,events=event_partial,ransac=coarse_partial,transforms=transform_partial),
        caveat='Raw returned values are partial observer evidence; not a fabricated full official factor set, full map, seal or Mean L2.')
    if (out/'observation/observer_summary.json').exists(): summary['observer']=read(out/'observation/observer_summary.json')
    write(out/'failure_summary.json',summary)
    return summary


def terminal_run():
    preflight_out,pre=preflight()
    if not pre['passed']:
        print('Preflight failed; formal workspace not created. Evidence: '+str(preflight_out),flush=True)
        return 2
    out=FORMAL
    status='M4.2 stopped before official reconstruction'; details={}
    try:
        declare(out,preflight_out)
        execution=guarded([sys.executable,str(Path(__file__).resolve()),'_worker',str(out)],out/'command')
        if not execution['passed']:
            status='M4.2 First-Pass failed — evidence preserved; no retry'
            details=failure_evidence(out,execution)
        else:
            status='M4.2 First-Pass returned — post-run validation pending'
            post=guarded([sys.executable,str(Path(__file__).resolve()),'_postprocess',str(out)],out/'postprocess_command')
            if not post['passed']: raise RuntimeError('First-Pass returned; result validation/postprocessing failed; no reconstruction retry')
            status='M4.2 scientific baseline accepted — visual interpretation pending'
            details=read(out/'validation.json')['baseline']
    except BaseException:
        details=dict(status=status,traceback=traceback.format_exc())
        if out.exists(): (out/'runner_failure.traceback.txt').write_text(details['traceback'])
        else: raise
    try:
        preservation(preflight_out,out)
    except BaseException:
        status='M4.2 scientific/source integrity stop — acceptance withheld'
        details['integrity_error']=traceback.format_exc()
        (out/'integrity_failure.traceback.txt').write_text(details['integrity_error'])
    write(out/'terminal_status.json',dict(status=status,details=details,unix=time.time(),
        first_pass_started=(out/'execution.started.json').exists(),
        first_pass_returned=(out/'command/execution.json').exists() and read(out/'command/execution.json')['passed']))
    acceptance(out,status,details)
    # Manifest never includes itself. Also bind final acceptance-document bytes.
    files=integrity.inventory([p for p in [out,EXPERIMENT] if p.exists()])
    files['scientific']['docs/implementation/M4_Phase2_P2A_Baseline_Acceptance.md']=sha(ROOT/'docs/implementation/M4_Phase2_P2A_Baseline_Acceptance.md')
    write(out/'manifest.json',files)
    print(status+'\nEvidence: '+str(out),flush=True)
    return 0 if status.startswith('M4.2 scientific baseline accepted') else 1


if __name__=='__main__':
    os.chdir(ROOT)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['run','check-sandbox','_worker','_postprocess'])
    parser.add_argument('output',nargs='?')
    args=parser.parse_args()
    if args.mode=='run': sys.exit(terminal_run())
    if args.mode=='check-sandbox':
        _,value=preflight(native_required=False)
        sys.exit(0 if value['passed'] else 2)
    if not args.output: parser.error('internal worker output required')
    if args.mode=='_worker': worker(Path(args.output))
    else: postprocess(Path(args.output))
