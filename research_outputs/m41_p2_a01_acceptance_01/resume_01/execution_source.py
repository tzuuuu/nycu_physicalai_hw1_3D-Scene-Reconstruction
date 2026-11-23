"""本次明確授權的 M4.1 獨立恢復；不匯入模擬器、Open3D 或重建 API。"""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import shutil
import subprocess
import traceback
import sys
sys.path.insert(0, '/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1')
from scripts.m4_capture_check import ROOT, inventory, inspect_capture, sha, no_links
from scripts.m41_metadata_policy import EXACT_PATHS, RESUME, verify_hashes, inspect_metadata

out = ROOT / RESUME
no_links(out)
if out.exists():
    raise FileExistsError('恢復目錄已存在；停止，不重用或自動換版：' + str(out))
if subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).strip():
    raise RuntimeError('需要乾淨工作區')
old = ROOT / 'research_outputs/m41_p2_a01_acceptance_01'
cap_rel = 'eval/_data/second_floor/114753116/P2_A_01'
cap = ROOT / cap_rel
read = lambda p: json.loads(Path(p).read_text())
# 此前置快照只保護本次檢查期間，不取代歷史預期清單。
paths = {ROOT/p for p in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if p and (ROOT/p).is_file()}
for base in ['eval/_data','experiments','research_outputs']:
    paths.update(p for p in (ROOT/base).rglob('*') if p.is_file())
current_before = {str(p.relative_to(ROOT)):sha(no_links(p)) for p in sorted(paths)}
prior_files = inventory(old)
out.mkdir(exist_ok=False)
def dump(name, value):
    with (out/name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
shutil.copyfile(__file__, out/'execution_source.py')
dump('protected.before.json', current_before)
auth = {'scope':'M4.1 resume_01 only','authorized_paths':list(EXACT_PATHS),
    'm42_authorized':False,'user_instruction':'使用者正式核准以下兩個精確路徑的OS中繼資料SHA例外：eval/_data/second_floor/.DS_Store；eval/_data/second_floor/114753116/P2_A_01/.DS_Store。本次只授權恢復M4.1最終驗收，不授權M4.2重建。',
    'requirements':['只限既存一般Finder中繼資料檔案','不擴展Phase 1例外、不排除科學資料','不刪除／修改／復原中繼檔','不更新歷史SHA','保留原始外層保全失敗及所有停止紀錄','任何第三個差異立即停止'],
    'human_coverage_confirmation':'P2-A的320張影格已涵蓋二樓所有可到達的主要房間及通道，以及房間之間的連通區域。',
    'original_stop_references':{str(old.relative_to(ROOT))+'/'+n:h for n,h in prior_files.items()},
    'created_at_utc':datetime.now(timezone.utc).isoformat(),
    'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
dump('authorization.json',auth)
policy = {'authorization_file':out/'authorization.json','log':out/'metadata_checks.jsonl'}
try:
    # 停止目錄 manifest 的自我列項不可能驗證自身，獨立保存其完整bytes及SHA。
    old_manifest = read(old/'manifest.json')
    self_reference = old_manifest.get('manifest.json')
    if self_reference != 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855':
        raise RuntimeError('前次manifest自我列項與已知原始缺陷不同')
    previous_evidence = verify_hashes(ROOT, {str(old.relative_to(ROOT))+'/'+n:h for n,h in old_manifest.items() if n != 'manifest.json'})
    shutil.copyfile(old/'manifest.json',out/'prior_manifest.original.json')
    dump('prior_manifest_limit.json',{'self_entry':self_reference,'whole_original_manifest_sha256':sha(old/'manifest.json'),
        'other_entries_verification':previous_evidence,
        'limitation':'前次產製時誤將建立中的manifest本身以空檔SHA列入，非有效自我雜湊錨點；保留原始bytes，不更新／宣稱該自我列項通過。新紀錄獨立綁定舊manifest完整bytes及所有其餘可驗證項目。'})
    started = read(ROOT/'research_outputs/m4_capture_P2_A_01/start.json')
    finished = read(ROOT/'research_outputs/m4_capture_P2_A_01/finish.json')
    verified = read(ROOT/'research_outputs/m41_verify_P2_A_01/verification.json')
    protected = read(ROOT/'research_outputs/m4_capture_P2_A_01/protected.before.json')
    stopped = read(old/'acceptance_stopped.json')
    verify_hashes(ROOT,stopped['source_records_sha256'])
    sources = verify_hashes(ROOT,started['source_sha256'])
    capture_config = ROOT/'research_outputs/m4_capture_P2_A_01/capture.safe.yaml'
    verify_hashes(ROOT,{str(capture_config.relative_to(ROOT)):started['safe_config_sha256']})
    snapshot = subprocess.check_output(['git','rev-parse','snapshot/pre-implementation'],cwd=ROOT,text=True).strip()
    if snapshot != started['snapshot'] or snapshot != '291209750bd8ecf84f337112c9b92307e6be192a':
        raise RuntimeError('Snapshot不符')
    for n,h in started['source_sha256'].items():
        raw = subprocess.check_output(['git','show',started['git_commit']+':'+n],cwd=ROOT)
        import hashlib
        if hashlib.sha256(raw).hexdigest()!=h:
            raise RuntimeError('採集Git來源不符：'+n)
    import yaml
    original_config = yaml.safe_load((ROOT/'configs/second_floor.yaml').read_text())
    safe_config = yaml.safe_load(capture_config.read_text())
    expected_safe = json.loads(json.dumps(original_config))
    expected_safe['output'].update(root=str(cap),clear_existing=False)
    if safe_config != expected_safe or safe_config != started['effective_file_config']:
        raise RuntimeError('安全衍生設定不符')
    metadata=[]
    for name in EXACT_PATHS:
        row=inspect_metadata(ROOT,name)
        row['historical_sha256']={}
        if name in protected:row['historical_sha256']['capture_protected_before']=protected[name]
        if name.startswith(cap_rel+'/'):
            rel=name[len(cap_rel)+1:]
            row['historical_sha256']['capture_finish']=finished['capture_sha256'][rel]
            row['historical_sha256']['original_verification']=verified['sha256'][rel]
        row['authorization_sha256']=sha(out/'authorization.json')
        metadata.append(row)
        shutil.copyfile(ROOT/name,out/('parent_metadata.current.bin' if name==EXACT_PATHS[0] else 'capture_metadata.current.bin'))
    dump('metadata_history_and_type.json',metadata)
    protected_result=verify_hashes(ROOT,protected,**policy)
    capture_current=inventory(cap)
    if set(capture_current)!=set(finished['capture_sha256']) or set(capture_current)!=set(verified['sha256']):
        raise RuntimeError('Capture檔案集合改變')
    # 明確要求自既有verification以後沒有任何新差異，這一步連兩個例外也不放寬。
    verification_result=verify_hashes(ROOT,{cap_rel+'/'+n:h for n,h in verified['sha256'].items()})
    finish_result=verify_hashes(ROOT,{cap_rel+'/'+n:h for n,h in finished['capture_sha256'].items()},**policy)
    scientific_names=[f'{kind}/{i}.png' for kind in ['rgb','depth'] for i in range(1,321)]+['GT_pose.npy','intrinsics.json']
    if set(capture_current)!=set(scientific_names)|{'.DS_Store'}:
        raise RuntimeError('科學資料集合不符')
    scientific={cap_rel+'/'+n:finished['capture_sha256'][n] for n in sorted(scientific_names)}
    for name in scientific_names:
        if finished['capture_sha256'][name]!=verified['sha256'][name]:
            raise RuntimeError('歷史科學資料SHA不符：'+name)
    verify_hashes(ROOT,scientific)
    dump('scientific_data_frozen_sha256.json',scientific)
    dump('scientific_comparison.json',[{'path':n,'finish_sha256':h,'verification_sha256':verified['sha256'][n[len(cap_rel)+1:]],'current_sha256':sha(ROOT/n),'match':True} for n,h in scientific.items()])
    fresh=inspect_capture(cap)
    if fresh['frame_count']!=320 or fresh['warnings'] or fresh['indices']!=list(range(1,321)):
        raise RuntimeError('重新資料格式稽核不符')
    for key,value in fresh.items():
        if verified[key]!=value:
            raise RuntimeError('重新稽核與既有結果不同：'+key)
    if fresh['intrinsics']!={key:original_config['camera'][key] for key in ['width','height','hfov']}:
        raise RuntimeError('內參不符正式Config')
    dump('fresh_verification.json',fresh)
    # 只測目前程序的唯讀ps權限，未建立任何重建／實驗程序。
    ps=subprocess.run(['/bin/ps','-o','rss=','-p',str(os.getpid())],capture_output=True,text=True)
    dump('m42_preflight.json',{'rss_limit_bytes':3*2**30,'existing_monitor':'scripts/record_command.py: _rss_bytes(process.pid), 0.5s sampling, terminate only direct child',
        'tree_rss_guard_implemented':False,'self_ps_probe_returncode':ps.returncode,
        'self_ps_probe_stdout':ps.stdout.strip(),'self_ps_probe_stderr':ps.stderr.strip(),
        'blockers':['程序樹RSS加總與整組停止尚未實作／驗證','完整同次位姿保存方式需為320張泛化既有191張專用觀測與驗收','地圖來源需固定保存來源／取樣與SHA，不將map_sample宣稱為完整未取樣地圖','仍待人工核准M4.2'],
        'experiment_workspace_exists':(ROOT/'experiments/p2_114753116_a01_baseline_01').exists(),
        'reconstruction_started':False})
    if (ROOT/'experiments/p2_114753116_a01_baseline_01').exists():
        raise RuntimeError('不預期的M4.2 workspace已存在')
    during=verify_hashes(ROOT,current_before)  # 本次檢查期間不套例外
    result={'status':'M4.1 — P2-A Capture Accepted / Scientific Data Frozen / Ready for M4.2 Authorization',
        'm41_accepted':True,'scientific_data_frozen':True,'m42_execution_authorized':False,
        'capture':str(cap),'N':320,'scientific_file_count':642,'all_capture_files':643,
        'gt_specification':fresh['gt_layout'],'intrinsics':fresh['intrinsics'],'depth_encoding':fresh['depth_encoding'],
        'original_capture_outer_preservation_succeeded':False,'original_stop_preserved':True,
        'historical_fact':'原始採集流程曾因OS中繼資料SHA差異觸發停止；經人工核准精確中繼資料例外後，透過獨立後續驗證確認科學資料完整性。',
        'capture_finish':finish_result,'capture_verification_strict':verification_result,
        'capture_protected':protected_result,'source_programs':sources,'during_attempt_strict':during,
        'human_coverage_confirmation':auth['human_coverage_confirmation'],
        'human_coverage_scope':'人工採集涵蓋確認，不代表重建完成或地圖絕對涵蓋率',
        'detailed_route_notes':'尚缺逐段路線紀錄，未編造名稱或影格區間',
        'snapshot':snapshot,'capture_git_commit':started['git_commit'],'verification_git_commit':verified['git_commit'],
        'acceptance_git_commit':auth['git_commit'],'checked_at_utc':datetime.now(timezone.utc).isoformat(),
        'working_tree':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
        'limitations':['GT僅離線描述，未作配準初值／選取','未完成First-Pass Data Verification／Map Completeness','原停止manifest自我列項缺陷保留，見prior_manifest_limit.json']}
    dump('acceptance.json',result)
    shutil.copyfile('/private/tmp/m41_resume_tests.log',out/'tests.log')
    print(json.dumps({'status':result['status'],'scientific_files':642,'protected_files':len(protected),'during_attempt_files':len(current_before),'m42_executed':False},ensure_ascii=False))
except BaseException:
    dump('recovery_stopped.json',{'status':'stopped','m41_accepted':False,'traceback':traceback.format_exc(),'time_utc':datetime.now(timezone.utc).isoformat()})
    raise
