from pathlib import Path
import json,hashlib
root=Path('/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1')
suite=root/'research_outputs/m32_20261118_suite_01'; recovery=suite/'resume_04'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(suite/'suite.json'); audit=read(recovery/'final_scientific_audit.json')
complete={};items={i['condition']:i for i in plan['conditions']};states={r['condition']:r for r in audit['conditions']}
for c,i in items.items():
    if c=='B1':continue
    location=suite/'resume_03/C2_audit/analysis' if c=='C2' else Path(i['output'])/'analysis'
    complete[c]=read(location/'summary.json')
stats=read(recovery/'C_comparison/comparison.json')['mean_l2_distribution']
def table(headers,rows):
    return '|'+ '|'.join(headers)+'|\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('|'+ '|'.join(map(str,row))+'|\n' for row in rows)+'\n'
text='''# M3.2 Registration Parameter Experiment：七條件最終研究驗收

最終驗收整理：2026-11-19（臺灣）；原suite與workspace命名沿用20261118。**七個預先固定條件已全部各嘗試一次：6個完整191張重建、1個真實配準失敗，沒有未執行條件。** C3／C4在正式核准的ps權限環境完成；C2以獨立補充審計確認科學完整性，原finalize停止仍保留。此文件供人工驗收M3.2與決定Phase 1是否結束，不代表Phase 1已獲核准結束。

沒有重跑B0、B1、B2、C1或C2，沒有因C4誤差較高而重試；沒有新增候選、跳幀、GT補正、修改核心、D、Phase 2、Bonus或最終英文報告。B0與C組seed0共用同一run，不重複計為獨立實驗。B1沒有完整Mean L2，不能填0或以部分影格平均替代。

## 1. 七條件正式結果與完成率

'''
rows=[]
for c,i in items.items():
    status='Failed Registration：70→71 RANSAC零對應' if c=='B1' else '完整重建；補充科學審計通過†' if c=='C2' else '正式成功（完整重建）'
    rows.append([c,i['voxel'],i['seed'],status,'無完整值' if c=='B1' else f"{complete[c]['mean_l2_m']:.12f}"])
text+=table(['條件','Registration Voxel (m)','Seed','實際狀態','完整191張Mean L2 (m)'],rows)
text+='''† C2狀態：`Reconstruction Completed / Scientific Integrity Verified / Historical Metadata Guard Stop Preserved`。原`finalize`沒有成功，不補造原成功receipt；新審計終態存於`resume_03/status/C2.json`，明列`original_finalize_succeeded=False`。

- 全研究：6／7＝85.7143%完整重建，1／7配準失敗。這是本次候選內完成比例，不是未見資料的成功機率。
- B組：B0、B2完成，B1失敗，2／3完整重建。
- C組：固定v=0.05的seed0、1、2、3、4全完成，5／5；「能完成」不保證姿態正確。
- M3.1的190張Selected=4.200397987245927 m保留作歷史脈絡，不混入本次191張排名。原M2／M3.1兩種正式run仍完整保留；新參數條件各有自己的首次FullBatch Baseline，不捏造Selected。

## 2. 固定變因、實際參數與GT界線

'''
text+=table(['條件','v (m)','Normal radius (m)','FPFH radius (m)','RANSAC／Distance Checker／ICP distance (m)','Seed'],[
['B0',.05,.10,.25,.075,0],['B1',.03,.06,.15,.045,0],['B2',.08,.16,.40,.120,0],['C1–C4',.05,.10,.25,.075,'1、2、3、4']])
text+='''全部固定：完整191張一樓原始RGB-D（精確1..191）與190對原相鄰影格；Open3D Point-to-Plane ICP；map down_voxel=0.05 m、build_cloud=True、ceiling margin=1 m；normal max_nn=30、FPFH max_nn=100；RANSAC mutual=True、edge checker=0.9、n=3、不估尺度、max_iteration=100000、confidence=0.999；ICP max_iteration=100、fitness／RMSE容差各1e-6。Seed依既有核心每對重設。法向量正常由2v前處理取得，3v回退不是本次正常路徑。

Python3.9.23、Open3D0.18.0、NumPy1.26.4、OpenCV4.8.0.76、RDFLib7.1.4、SciPy1.13.1、Panel1.4.5、Bokeh3.4.3、Habitat-Lab0.3.3與鎖定環境一致；OMP_NUM_THREADS=1，不安裝或升級依賴。教師核心、CLI、API、Ontology、load／plot、pixi.toml與pixi.lock均未修改。

各新workspace經官方Declare→原生First-Pass Reconstruction→Explore→Query；同次CLI以唯讀return觀測保存位姿、矩陣、因素與實際引數，不替換配準函式、不改返回矩陣。GT只在重建返回後用於官方評估及離線誤差分析，不提供GT初值、不選幀、不回寫地圖，不做SE(3)／Sim(3)最佳擬合。此為針對既有失敗案例的探索，未證明未見資料泛化。

## 3. 103→104局部姿態誤差及全序列錯解

'''
rows=[]
for c in items:
    if c=='B1':rows.append([c]+['未到達']*4);continue
    p=complete[c]['pair103_104'];rows.append([c]+[f'{p[k]:.9f}' for k in ['coarse_rotation_error_deg','relative_rotation_error_deg','coarse_translation_error_m','relative_translation_error_m']])
text+=table(['條件','RANSAC旋轉 (°)','ICP旋轉 (°)','RANSAC平移 (m)','ICP平移 (m)'],rows)
text+='''重大錯解採計畫事先固定的局部旋轉誤差>150°，下表列current frame；本次>90°位置也相同。時間箭頭為previous→current；保存矩陣實際將current變換至previous。GT先轉float64及固定首相機／軸向座標，再計算`inv(P_GT,previous) @ P_GT,current`；旋轉誤差由旋轉差trace求角，平移誤差為兩平移向量L2。這些GT指標只用於事後描述。

'''
rows=[]
for c,s in complete.items():
    rows.append([c,s['severe_coarse_gt150_current_frames'],s['severe_icp_gt150_current_frames'],f"{s['max_l2_m']:.6f}",f"{s['final_l2_m']:.6f}",f"{s['final_orientation_error_deg']:.6f}",s['map']['ceiling_cropped_points']])
text+=table(['條件','RANSAC>150°','ICP>150°','最大L2 (m)','末張L2 (m)','末張全域旋轉 (°)','去天花板地圖點數'],rows)
text+='''B0／C2／C4皆僅103→104出現重大局部錯解，後續連乘傳播為近180°全域方向錯誤；B2／C1／C3沒有同級翻轉。C3的103→104由粗配準3.479170°修正至ICP0.193585°，仍有0.223344 m局部平移誤差。B2雖在該對僅0.018675 m平移誤差，104→105仍有0.543665 m局部平移誤差。不能只憑單一配對或Mean L2宣稱地圖完全正確。B1在70→71中止，沒有103→104或後續完整精度。

## 4. B組：Registration Pipeline Scale

B2相對B0，完整191張Mean L2由3.174055104788降至0.274959466593 m，降低91.3373%；103→104粗配準旋轉由176.074504°變為1.481140°，ICP後0.793845°。支持本次整套尺度改變會影響幾何匹配與錯解的假說。

但v同時改變保留點數、normal／FPFH鄰域與RANSAC／ICP距離，不能把改善單獨歸因於任一派生參數，也不能推論越粗越好。B1較細卻無法完成。B2只測seed0一次，沒有0.08的跨seed驗證或未見資料驗證，**不能宣稱已找到可泛化的最佳Voxel**。

## 5. C組：完整五Seed敏感度

固定v=0.05，seed0／1／2／3／4的完整Mean L2依序為3.174055104788、0.155696709607、3.165352438552、0.221466815796、3.366709232590 m；所有實際完成條件均納入，不只報告最低值。

'''
text+=table(['統計（五Seed，n=5）','數值 (m)'],[[k,f'{stats[k]:.12f}'] for k in ['mean_m','sample_std_m','median_m','min_m','max_m','range_m']])
text+='''樣本標準差ddof=1；B0只作為seed0計一次。五組皆完整重建，但seed0／2／4在103→104有>150°重大錯解（3／5），seed1／3沒有（2／5）。這是有限五seed的描述性頻率，不是全190對Registration Success Rate，也不是母體失敗機率的精確估計。

分布同時包含約0.16–0.22 m與約3.17–3.37 m結果，顯示固定尺度下的抽樣敏感性，且精度不穩定；不宜只用平均掩蓋兩群結果。Seed1雖為最小值，**不得將它宣稱為通用最佳seed、部署成GT選值策略，或自動換入B2再試**。本輪不追加尺度×seed網格或挑選性重跑。

## 6. 八項因素

六個完整重建各有1522筆同次正式因素，共9132筆（B0不因兼作C0而重複計算）。RawPointCount／VoxelizedPointYield各191，其他六項各190；全部逐筆以官方儲存精度核對同次觀測。B1只有562筆部分觀測，未封存，不冒充完整官方因素。

下表為官方因素序列平均；點數為count、RMSE為m、Fitness為比例：

'''
factors=['RawPointCount','VoxelizedPointYield','CoarseRANSACFitness','CoarseRANSACRMSE','CoarseRANSACCorrespondences','ICPInlierFitness','ICPInlierRMSE','ICPInlierCorrespondences']
text+=table(['因素']+list(complete),[[f]+[f"{complete[c]['factor_summary'][f]['mean']:.7f}" for c in complete] for f in factors])
text+='''RawPointCount各組相同。B2平均voxel點數約8303，v=0.05各組約19944；B2的內部RMSE較高但GT誤差較低，顯示不同點集與門檻下的內部殘差不能直接作真實精度排名。C組平均Fitness相近，仍有截然不同的災難配對與Mean L2；全序列因素平均會掩蓋單一配對錯解。完整逐幀／逐對CSV、因素摘要與官方時間序列HTML均保留。

## 7. Runtime、RSS與監控權限驗證

'''
rows=[]
for c,i in items.items():
    e=read(Path(i['output'])/'command/execution.json')
    if c=='B1':
        rows.append([c,f"{e['total_process_s']:.6f}",'無正常回傳','275.254486 / 3.035104',f"{e['child_peak_rss_bytes']/2**30:.6f}",e['child_peak_rss_bytes'],'1：配準失敗']);continue
    s=complete[c];rows.append([c,f"{s['total_process_s']:.6f}",f"{s['reconstruction_s']:.6f}",f"{s['cpu_user_s']:.6f} / {s['cpu_system_s']:.6f}",f"{s['peak_rss_bytes']/2**30:.6f}",s['peak_rss_bytes'],0])
text+=table(['條件','總程序時間 (s)','reconstruct含觀測 (s)','CPU user/system (s)','峰值RSS (GiB)','峰值RSS (bytes)','退出碼'],rows)
text+='''全部正式嘗試保留3 GiB即時RSS護欄與0.5秒取樣，無超限。B1耗時是失敗前嘗試，不能與完整191張直接比較。總時間含子程序啟動、正式重建、評估／PNG／Seal／Run及觀測驗證；不含後續Explore／Query、離線分析及監控前置合成測試。CPU為CLI觀測區間；reconstruct含觀測時間與總程序時間分開。每條件只有一次量測，背景負載／快取不完全一致，不宣稱統計顯著的效能改善。

前次`resume_03`在C3正式Declare前，因沙箱拒絕`ps`而停止，沒有C3工作目錄或重建。此次先在沙箱重現，再經Codex正式權限核准機制，在具有必要權限的環境確認直接`ps`、Python subprocess、`record_command._rss_bytes()`及實際子程序持續取樣全部通過。原`record_command.py`完全未改；沒有sudo、替代取樣機制、關閉監控或只用結束後Peak RSS。

正常合成測試保留3 GiB護欄並得到4筆實際RSS；另以獨立合成低門檻案例驗證超限終止，以故障注入驗證監測失效終止，均保存SIGTERM退出碼-15及原因。這些是預期負面測試，不是正式重建失敗。C3與C4各自在Declare前再次通過相同前置測試，正式重建分別保存 **597／598筆**持續RSS，取樣峰值與程序Peak RSS另存於`final_scientific_audit.json`及各`command/execution.json`。外層核准執行console亦保留真正觀測／重建程序PID；同程序runpy執行原CLI，監測的是實際重建程序。

## 8. 地圖品質與比較圖

B2／C1／C3在同範圍俯視圖的後段紅色估計軌跡較接近黑色GT；B0／C2／C4的後段軌跡向相反方向偏移，地圖錯位與擴張較明顯。C4末張L2=6.262907 m、全域旋轉179.715064°，未因可完成而成為高精度結果。B2／C1／C3仍有殘餘位移、重影與缺口，不宣稱幾何完全正確。

各正式實驗保留原生去天花板PNG。比較圖用同一首相機座標與共同X/Z範圍、正式地圖固定上限取樣，沒有重新配準或GT校正。地圖點數也受累積位姿與天花板裁切影響，不作涵蓋率或品質分數；191張皆保留不代表實際樓層表面正確涵蓋100%。B1沒有完整地圖，不以部分輸出冒充完成。

'''
text+=f"![七條件Mean L2]({recovery/'seven_conditions_mean_l2.png'})\n\n"
for group in ['B','C']:
    base=recovery/(group+'_comparison')
    text+=f"### {group}組最終比較圖\n\n"
    text+=f"![{group}組逐幀誤差]({base/'frame_errors.png'})\n\n"
    text+=f"![{group}組同範圍地圖]({base/'map_trajectories.png'})\n\n"
    text+=f"另存 `{group}_comparison/local_errors.png`、`eight_factors.png`、`comparison.csv`、`comparison.json`與各自SHA manifest；B圖只畫完整B0／B2，B1失敗明列於表格，沒有假造全序列曲線。\n\n"
text+='''## 9. 正式Turtle、Seal、來源與科學完整性

恢復前899個既有保護項目與全部歷史停止證據均核對；最後`final_integrity.json`及`final_scientific_audit.json`再次確認。六個完成條件各有唯一191張FullBatch Baseline、有效Seal及1522因素；Turtle儲存數值依API七位有效數字與原始float64評估核對。B1宣告bytes不變、未Seal、無完整Baseline。每個條件的執行標記SHA、正式CLI退出紀錄、位姿、矩陣、PNG、preregistration、Turtle與Seal摘要均另存最終審計。

'''
text+=table(['條件','Turtle SHA-256','Seal declaration digest'],[[c,states[c]['ttl_sha256'],states[c].get('seal_digest','未封存（配準失敗）')] for c in items])
text+='教師核心及鎖定環境SHA全部與原suite一致：\n\n'
text+=table(['檔案','SHA-256'],[[name,digest] for name,digest in audit['core_sha256'].items()])
text+=f"Capture SHA-256：`{audit['capture_sha256']}`。原M2／M3.1正式workspace Turtle SHA：`{audit['original_M2_M31']['turtle_sha256']}`，Seal、baseline／selected子圖與原suite保存內容完全相同。\n\n"
text+='''新權限授權只允許C3／C4，綁定執行commit `146c9d5`、12個歷史suite／停止／授權／C2審計紀錄SHA、前次授權SHA、當前工具SHA及權限測試產物SHA。C3／C4的preregistration與封存宣告註解引用此次授權及真實參數；CLI實際引數、190對的v／seed與宣告逐筆核對。參數註解不是新的Ontology Parameter，未修改Ontology或偽稱正式API已提供每run獨立參數模型。

### 精確OS Metadata Exclusion Policy與歷史停止

例外仍僅`experiments/.DS_Store`及`research_outputs/.DS_Store`，限定既存一般檔案；符號連結（即使內容SHA相同）、缺檔、目錄或第三路徑仍停止。預設驗證器不啟用例外；本次有授權的恢復範圍才啟用。每次另存實際路徑、歷史／目前SHA、存在狀態、檔案類型與差異，日誌完成後獨立凍結；不改寫或刪除任何中繼檔，不排除任何科學資料、研究產物或程式碼。

'''
historical=read(suite/'protected.before.json')
text+=table(['精確路徑','原始歷史SHA-256','resume_04開始時SHA-256'],[[name,historical[name],sha(recovery/(name.split('/')[0]+'_DS_Store_before.bin'))] for name in ['experiments/.DS_Store','research_outputs/.DS_Store']])
text+='''前後SHA差異與可取得的中繼檔bytes均保留；最早變更前bytes未保存，不能由SHA還原，也不假稱已取得最早逐位元差異或確定OS寫入來源。兩路徑之外未發現未授權檔案異動；不能將這句誤寫為所有歷史SHA（含中繼檔）完全未變。

歷史鏈完整保留：

1. B0最初序列化停止與後置恢復，見原suite停止與`resume_01`，未重跑B0。
2. B1在70→71真實RANSAC失敗，見`resume_failed.json`、失敗保全及原B1停止文件，未重跑B1。
3. `resume_02/system_stopped.json`：C2已重建，但原finalize因`experiments/.DS_Store`差異停止。
4. `research_outputs/m32_20261118_final_recovery_stop_01/`：前次精確排除僅一個路徑，發現第二個`research_outputs/.DS_Store`差異，依原規則停止。
5. `resume_03/C2_audit/`：新增兩路徑授權後完成C2唯讀科學審計；`resume_03/system_stopped.json`保留C3啟動前`PermissionError: Operation not permitted: ps`。
6. `resume_04/`：本次正式權限修復、沙箱／核准環境監控測試、C3／C4各一次成功receipt、最終比較與第一次最終完整性驗證均完成；收尾重複驗證的寫入一次護欄停止另列如下。

### 收尾重複驗證的寫入一次護欄停止（不覆寫已成功審計）

完成C3／C4、全部比較與第一次`verify`後，收尾不必要地再次呼叫同一`verify`入口。科學SHA與終態核對通過後，入口嘗試以`open('x')`再次建立既有`final_integrity.json`，觸發`FileExistsError`。原成功審計檔沒有覆寫，所有正式重建與比較產物保持完整；此為重複收尾入口的檔案建立衝突，不是新配準失敗或3 GiB超限。

`resume_04/system_stopped.json`保留原始Traceback與停止時間，不刪除、不改寫；因此不能宣稱本次沒有新停止。後續保全不重新執行`verify`／`finalize`，只直接核對凍結證據SHA並另存`closing_preservation.json`及最終provenance／manifest，明列`closing_guard_stop_preserved=True`。第一次`final_integrity.json`仍是先前真正成功的結果，不把重複呼叫說成成功。已完成的七條件與五seed分析可供人工審查，研究維持停止。

原B0／B1停止版驗收另保留於`M3_Parameter_Experiment_B0_Stop_Record.md`與`M3_Parameter_Experiment_B1_Stop_Record.md`；本次改寫前完整驗收文件另存`resume_04/acceptance.before.md`，Git亦保留所有歷史。未修改舊停止JSON、Traceback或歷史SHA清單。

'''
old=(recovery/'acceptance.before.md').read_text()
discussion=old.split('## Discussion and Future Work Candidates',1)[1].split('## 11. 產物、比較圖與可追溯性',1)[0]
discussion=discussion.replace('不能把系統未啟動C3／C4算作低配準穩健性。','本次C3／C4已完成；先前系統未啟動的時段不能算作低配準穩健性。')
start=discussion.index('目前建議先人工驗收系統停止與已完成結果')
discussion=discussion[:start]+'''本次原訂B／C研究已完成，應先人工驗收完整結果與歷史停止鏈，再決定Phase 1是否結束。兩個OS中繼檔例外已由使用者精確核准，不是本研究自行擴張政策。D仍只作未來受控假說；沒有修改confidence、增加預算、搜尋seed或執行額外候選。本輪完成後停止，Phase 2、Bonus與最終英文報告仍須另外授權。

'''
text+='## Discussion and Future Work Candidates'+discussion
text+='''## 10. 產物索引與Git

共同根目錄為`research_outputs/m32_20261118_suite_01/resume_04/`：

'''
text+=table(['位置','內容'],[
['authorization.json、protected.before.json','本次有限授權、歷史SHA鏈與899項前置保護清單'],
['sandbox_monitor_probe/、authorized_monitor_probe/','無Capture／無重建的沙箱失敗及正式權限功能測試'],
['monitor_before_C3/、monitor_before_C4/','各次Declare前的原監控器即時取樣與負面測試'],
['status/C3.json、status/C4.json','各一次完整成功終態與證據SHA'],
['B_comparison/、C_comparison/、all_comparison/','全部候選CSV／MD／JSON、逐幀／局部誤差、八因素與同範圍地圖'],
['seven_conditions_mean_l2.png','七個預定條件摘要，B1保留失敗無完整值'],
['final_integrity.json、final_scientific_audit.json','既有保全、七條件Turtle／Seal、因素、位姿／矩陣／PNG／執行標記來源SHA及取樣筆數'],
['metadata_checks/、closing_metadata_checks.jsonl','兩個精確中繼檔的逐次存在狀態與SHA差異'],
['C3_authorized_entrypoint.console.log、C4_authorized_entrypoint.console.log','正式權限入口、子程序PID、原CLI及後置作業console'],
['final_provenance.json、final_manifest.json','最終Git／Snapshot、驗收文件SHA及研究產物SHA索引']])
text+='''C3正式成果在`experiments/p1_m32_20261118_c_v005_s3_01/`及`research_outputs/m32_p1_m32_20261118_c_v005_s3_01/`；C4對應`s4_01`。每組保留preregistration、原宣告、執行標記、官方CLI／資源、191位姿／190對矩陣、1522因素、Explore四份HTML／Query、正式PNG、完整性、`official_after/`快照及SHA manifest。C2新增審計仍在`resume_03/C2_audit/`；其原正式成果沒有覆寫。

本次Git小步提交：

- `7387aec`：原ps即時監控前置工具與監測失效停止測試，`record_command.py`未改。
- `146c9d5`：權限恢復入口、有限授權與歷史保全銜接；C3／C4真正執行commit。
- 前次`945aa7a`／`d91dfa3`保存兩路徑政策與C2審計恢復工具，`e3f00b1`保存原ps權限停止驗收；更早執行與停止commit均保留。
- 正式執行前完整 **235 passed in 6.82s**，正式重建期間不並行跑測試；文件及query以`git diff --check`與實際產物／SHA核對。後續文件／query提交由Git紀錄識別。
- 保持main、無remote、不改寫歷史；`snapshot/pre-implementation`維持`291209750bd8ecf84f337112c9b92307e6be192a`。只追蹤工具、測試、MD與可重現query原始碼，Turtle／PNG／HTML／NPY／JSON／研究產物不加入Git。

**M3.2七條件研究與必要後置分析已完成；立即停止，等待人工驗收Phase 1。未自行開始Experiment D、Phase 2、Bonus或最終英文報告。**
'''
(root/'docs/implementation/M3_Parameter_Experiment_Acceptance.md').write_text(text)
print('Wrote final acceptance:',len(text.splitlines()),'lines')
