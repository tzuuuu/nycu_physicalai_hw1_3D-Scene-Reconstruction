"""保留已完成資料稽核與ps權限停止，另存M4.1補充完成驗收；不重建。"""
from pathlib import Path
import json,sys,subprocess,shutil
from datetime import datetime,timezone
sys.path.insert(0,'/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1')
from scripts.m4_capture_check import ROOT, inventory,sha
from scripts.m41_metadata_policy import RESUME,verify_hashes
out=ROOT/RESUME
completion=out/'completion_01'
completion.mkdir(exist_ok=False)
shutil.copyfile(__file__,completion/'execution_source.py')
def read(p):return json.loads(Path(p).read_text())
def dump(n,v):
 with (completion/n).open('x') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
auth=read(out/'authorization.json')
policy={'authorization_file':out/'authorization.json','log':out/'metadata_checks.jsonl'}
cap_rel='eval/_data/second_floor/114753116/P2_A_01'
start=read(ROOT/'research_outputs/m4_capture_P2_A_01/start.json')
finish=read(ROOT/'research_outputs/m4_capture_P2_A_01/finish.json')
old_verify=read(ROOT/'research_outputs/m41_verify_P2_A_01/verification.json')
protected=read(ROOT/'research_outputs/m4_capture_P2_A_01/protected.before.json')
fresh=read(out/'fresh_verification.json')
current=inventory(ROOT/cap_rel)
assert current==old_verify['sha256']==fresh['sha256']
assert fresh['frame_count']==320 and fresh['indices']==list(range(1,321)) and not fresh['warnings']
assert len(read(out/'scientific_data_frozen_sha256.json'))==642
for n,h in read(out/'scientific_data_frozen_sha256.json').items():
 assert h==finish['capture_sha256'][n[len(cap_rel)+1:]]==old_verify['sha256'][n[len(cap_rel)+1:]]
scientific_result=verify_hashes(ROOT,read(out/'scientific_data_frozen_sha256.json'))
protection_result=verify_hashes(ROOT,protected,**policy)
finish_result=verify_hashes(ROOT,{cap_rel+'/'+n:h for n,h in finish['capture_sha256'].items()},**policy)
verification_result=verify_hashes(ROOT,{cap_rel+'/'+n:h for n,h in old_verify['sha256'].items()})
sources_result=verify_hashes(ROOT,start['source_sha256'])
verify_hashes(ROOT,{'research_outputs/m4_capture_P2_A_01/capture.safe.yaml':start['safe_config_sha256']})
prior=read(ROOT/'research_outputs/m41_p2_a01_acceptance_01/acceptance_stopped.json')
verify_hashes(ROOT,prior['source_records_sha256'])
verify_hashes(ROOT,auth['original_stop_references'])
during_result=verify_hashes(ROOT,read(out/'protected.before.json'))
source_stop=read(out/'recovery_stopped.json')
if "Operation not permitted: '/bin/ps'" not in source_stop['traceback']:
 raise RuntimeError('不是已辨識的M4.2唯讀ps權限停止；不得繼續')
snapshot=subprocess.check_output(['git','rev-parse','snapshot/pre-implementation'],cwd=ROOT,text=True).strip()
assert snapshot==start['snapshot']=='291209750bd8ecf84f337112c9b92307e6be192a'
assert not (ROOT/'experiments/p2_114753116_a01_baseline_01').exists()
preflight={'experiment':'p2_114753116_a01_baseline_01','floor':2,'input':str(ROOT/cap_rel),'frames':320,'pairs':319,'factor_occurrences':2554,
 'registration_voxel_m':.05,'ransac_seed':0,'icp':'Open3D Point-to-Plane','map_only_down_voxel_m':.05,
 'rss_limit_bytes':3221225472,'tree_rss_guard_implemented':False,
 'ps_permission_verified':False,'ps_probe_traceback_sha256':sha(out/'recovery_stopped.json'),
 'blockers':['M4.2尚未獲人工授權','目前沙箱拒絕/bin/ps；正式環境須先驗證監測與失效停止','現有record_command只監測直接PID，須新增驗證程序樹總RSS與整組停止','既有191張專用驗收／觀測須泛化至320張／319對','同次地圖來源保存規格須固定並驗證，現有map_sample為至多150000點抽樣，非完整未取樣地圖'],
 'workspace_created':False,'declaration_executed':False,'reconstruction_executed':False}
dump('m42_preflight.json',preflight)
status='M4.1 — P2-A Capture Accepted / Scientific Data Frozen / Ready for M4.2 Authorization'
result={'status':status,'m41_accepted':True,'scientific_data_frozen':True,'m42_execution_authorized':False,
 'capture':str(ROOT/cap_rel),'N':320,'scientific_file_count':642,'capture_files':643,
 'gt_specification':fresh['gt_layout'],'intrinsics':fresh['intrinsics'],'depth_encoding':fresh['depth_encoding'],
 'scientific_comparison':scientific_result,'capture_finish':finish_result,'capture_verification_strict':verification_result,
 'capture_protected':protection_result,'source_programs':sources_result,'during_attempt_strict':during_result,
 'original_capture_outer_preservation_succeeded':False,'original_stop_preserved':True,
 'historical_fact':'原始採集流程曾因OS中繼資料SHA差異觸發停止；經人工核准精確中繼資料例外後，透過獨立後續驗證確認科學資料完整性。',
 'human_coverage_confirmation':auth['human_coverage_confirmation'],'human_coverage_scope':'人工採集涵蓋確認，不代表重建完成或地圖絕對涵蓋率',
 'detailed_route_notes':'尚缺逐段路線紀錄，未編造名稱或影格區間',
 'capture_git_commit':start['git_commit'],'verification_git_commit':old_verify['git_commit'],
 'acceptance_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'snapshot':snapshot,'checked_at_utc':datetime.now(timezone.utc).isoformat(),
 'working_tree':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
 'read_only_ps_probe_stop_preserved':True,'recovery_probe_stop_sha256':sha(out/'recovery_stopped.json'),
 'limitations':['原始外層採集保全失敗仍保留','恢復腳本在M4.2唯讀ps探測遇權限停止；本次獨立補充完成M4.1，沒有重跑擷取或重建','舊manifest無效自我列項原樣保留，以新紀錄獨立綁定完整bytes，未宣稱其自我雜湊通過','尚無First-Pass因素／重建涵蓋結果']}
dump('acceptance.json',result)
shutil.copyfile('/private/tmp/m41_resume_tests.log',completion/'tests.log')
print(json.dumps({'status':status,'scientific_files':642,'protected':protection_result['expected_count'],'protected_strict_matches':protection_result['strict_matches'],'capture_verification_strict':verification_result['strict_matches'],'during_attempt_strict':during_result['strict_matches'],'M4.2_executed':False},ensure_ascii=False,indent=2))
