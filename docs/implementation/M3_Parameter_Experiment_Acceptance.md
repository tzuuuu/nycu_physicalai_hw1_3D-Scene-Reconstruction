# M3.2 Registration Parameter Experiment：七條件最終研究驗收

最終驗收整理：2026-11-19（臺灣）；原suite與workspace命名沿用20261118。**七個預先固定條件已全部各嘗試一次：6個完整191張重建、1個真實配準失敗，沒有未執行條件。** C3／C4在正式核准的ps權限環境完成；C2以獨立補充審計確認科學完整性，原finalize停止仍保留。此文件供人工驗收M3.2與決定Phase 1是否結束，不代表Phase 1已獲核准結束。

沒有重跑B0、B1、B2、C1或C2，沒有因C4誤差較高而重試；沒有新增候選、跳幀、GT補正、修改核心、D、Phase 2、Bonus或最終英文報告。B0與C組seed0共用同一run，不重複計為獨立實驗。B1沒有完整Mean L2，不能填0或以部分影格平均替代。

## 1. 七條件正式結果與完成率

|條件|Registration Voxel (m)|Seed|實際狀態|完整191張Mean L2 (m)|
|---|---|---|---|---|
|B0|0.05|0|正式成功（完整重建）|3.174055104788|
|B1|0.03|0|Failed Registration：70→71 RANSAC零對應|無完整值|
|B2|0.08|0|正式成功（完整重建）|0.274959466593|
|C1|0.05|1|正式成功（完整重建）|0.155696709607|
|C2|0.05|2|完整重建；補充科學審計通過†|3.165352438552|
|C3|0.05|3|正式成功（完整重建）|0.221466815796|
|C4|0.05|4|正式成功（完整重建）|3.366709232590|

† C2狀態：`Reconstruction Completed / Scientific Integrity Verified / Historical Metadata Guard Stop Preserved`。原`finalize`沒有成功，不補造原成功receipt；新審計終態存於`resume_03/status/C2.json`，明列`original_finalize_succeeded=False`。

- 全研究：6／7＝85.7143%完整重建，1／7配準失敗。這是本次候選內完成比例，不是未見資料的成功機率。
- B組：B0、B2完成，B1失敗，2／3完整重建。
- C組：固定v=0.05的seed0、1、2、3、4全完成，5／5；「能完成」不保證姿態正確。
- M3.1的190張Selected=4.200397987245927 m保留作歷史脈絡，不混入本次191張排名。原M2／M3.1兩種正式run仍完整保留；新參數條件各有自己的首次FullBatch Baseline，不捏造Selected。

## 2. 固定變因、實際參數與GT界線

|條件|v (m)|Normal radius (m)|FPFH radius (m)|RANSAC／Distance Checker／ICP distance (m)|Seed|
|---|---|---|---|---|---|
|B0|0.05|0.1|0.25|0.075|0|
|B1|0.03|0.06|0.15|0.045|0|
|B2|0.08|0.16|0.4|0.12|0|
|C1–C4|0.05|0.1|0.25|0.075|1、2、3、4|

全部固定：完整191張一樓原始RGB-D（精確1..191）與190對原相鄰影格；Open3D Point-to-Plane ICP；map down_voxel=0.05 m、build_cloud=True、ceiling margin=1 m；normal max_nn=30、FPFH max_nn=100；RANSAC mutual=True、edge checker=0.9、n=3、不估尺度、max_iteration=100000、confidence=0.999；ICP max_iteration=100、fitness／RMSE容差各1e-6。Seed依既有核心每對重設。法向量正常由2v前處理取得，3v回退不是本次正常路徑。

Python3.9.23、Open3D0.18.0、NumPy1.26.4、OpenCV4.8.0.76、RDFLib7.1.4、SciPy1.13.1、Panel1.4.5、Bokeh3.4.3、Habitat-Lab0.3.3與鎖定環境一致；OMP_NUM_THREADS=1，不安裝或升級依賴。教師核心、CLI、API、Ontology、load／plot、pixi.toml與pixi.lock均未修改。

各新workspace經官方Declare→原生First-Pass Reconstruction→Explore→Query；同次CLI以唯讀return觀測保存位姿、矩陣、因素與實際引數，不替換配準函式、不改返回矩陣。GT只在重建返回後用於官方評估及離線誤差分析，不提供GT初值、不選幀、不回寫地圖，不做SE(3)／Sim(3)最佳擬合。此為針對既有失敗案例的探索，未證明未見資料泛化。

## 3. 103→104局部姿態誤差及全序列錯解

|條件|RANSAC旋轉 (°)|ICP旋轉 (°)|RANSAC平移 (m)|ICP平移 (m)|
|---|---|---|---|---|
|B0|176.074504313|179.778159121|1.352138805|0.946959929|
|B1|未到達|未到達|未到達|未到達|
|B2|1.481139775|0.793844775|0.465103836|0.018675483|
|C1|0.539919085|0.171590394|0.348820685|0.265884493|
|C2|172.158898863|179.776546688|1.253175719|0.946915449|
|C3|3.479170341|0.193585131|0.122990304|0.223343948|
|C4|165.061042426|179.540822340|0.757825042|0.937376724|

重大錯解採計畫事先固定的局部旋轉誤差>150°，下表列current frame；本次>90°位置也相同。時間箭頭為previous→current；保存矩陣實際將current變換至previous。GT先轉float64及固定首相機／軸向座標，再計算`inv(P_GT,previous) @ P_GT,current`；旋轉誤差由旋轉差trace求角，平移誤差為兩平移向量L2。這些GT指標只用於事後描述。

|條件|RANSAC>150°|ICP>150°|最大L2 (m)|末張L2 (m)|末張全域旋轉 (°)|去天花板地圖點數|
|---|---|---|---|---|---|---|
|B0|[104]|[104]|10.697682|5.795983|179.829626|2725240|
|B2|[]|[]|0.622966|0.449369|1.796567|2553898|
|C1|[]|[]|0.347128|0.255761|0.682926|2559601|
|C2|[104]|[104]|10.677933|5.755900|179.851053|2725952|
|C3|[]|[]|0.496543|0.393521|0.680662|2551349|
|C4|[104]|[104]|11.154214|6.262907|179.715064|2724546|

B0／C2／C4皆僅103→104出現重大局部錯解，後續連乘傳播為近180°全域方向錯誤；B2／C1／C3沒有同級翻轉。C3的103→104由粗配準3.479170°修正至ICP0.193585°，仍有0.223344 m局部平移誤差。B2雖在該對僅0.018675 m平移誤差，104→105仍有0.543665 m局部平移誤差。不能只憑單一配對或Mean L2宣稱地圖完全正確。B1在70→71中止，沒有103→104或後續完整精度。

## 4. B組：Registration Pipeline Scale

B2相對B0，完整191張Mean L2由3.174055104788降至0.274959466593 m，降低91.3373%；103→104粗配準旋轉由176.074504°變為1.481140°，ICP後0.793845°。支持本次整套尺度改變會影響幾何匹配與錯解的假說。

但v同時改變保留點數、normal／FPFH鄰域與RANSAC／ICP距離，不能把改善單獨歸因於任一派生參數，也不能推論越粗越好。B1較細卻無法完成。B2只測seed0一次，沒有0.08的跨seed驗證或未見資料驗證，**不能宣稱已找到可泛化的最佳Voxel**。

## 5. C組：完整五Seed敏感度

固定v=0.05，seed0／1／2／3／4的完整Mean L2依序為3.174055104788、0.155696709607、3.165352438552、0.221466815796、3.366709232590 m；所有實際完成條件均納入，不只報告最低值。

|統計（五Seed，n=5）|數值 (m)|
|---|---|
|mean_m|2.016656060267|
|sample_std_m|1.670897484447|
|median_m|3.165352438552|
|min_m|0.155696709607|
|max_m|3.366709232590|
|range_m|3.211012522983|

樣本標準差ddof=1；B0只作為seed0計一次。五組皆完整重建，但seed0／2／4在103→104有>150°重大錯解（3／5），seed1／3沒有（2／5）。這是有限五seed的描述性頻率，不是全190對Registration Success Rate，也不是母體失敗機率的精確估計。

分布同時包含約0.16–0.22 m與約3.17–3.37 m結果，顯示固定尺度下的抽樣敏感性，且精度不穩定；不宜只用平均掩蓋兩群結果。Seed1雖為最小值，**不得將它宣稱為通用最佳seed、部署成GT選值策略，或自動換入B2再試**。本輪不追加尺度×seed網格或挑選性重跑。

## 6. 八項因素

六個完整重建各有1522筆同次正式因素，共9132筆（B0不因兼作C0而重複計算）。RawPointCount／VoxelizedPointYield各191，其他六項各190；全部逐筆以官方儲存精度核對同次觀測。B1只有562筆部分觀測，未封存，不冒充完整官方因素。

下表為官方因素序列平均；點數為count、RMSE為m、Fitness為比例：

|因素|B0|B2|C1|C2|C3|C4|
|---|---|---|---|---|---|---|
|RawPointCount|249540.3089005|249540.3089005|249540.3089005|249540.3089005|249540.3089005|249540.3089005|
|VoxelizedPointYield|19943.7172775|8302.7172775|19943.7172775|19943.7172775|19943.7172775|19943.7172775|
|CoarseRANSACFitness|0.9227953|0.9341015|0.9250392|0.9223018|0.9241246|0.9227338|
|CoarseRANSACRMSE|0.0269385|0.0411192|0.0273371|0.0272988|0.0269926|0.0266128|
|CoarseRANSACCorrespondences|18514.0789474|7797.0105263|18546.2526316|18508.5421053|18530.9578947|18514.1684211|
|ICPInlierFitness|0.9236870|0.9314186|0.9242447|0.9236882|0.9242117|0.9236705|
|ICPInlierRMSE|0.0208759|0.0300806|0.0208759|0.0208804|0.0208731|0.0208834|
|ICPInlierCorrespondences|18525.6421053|7781.1947368|18531.7210526|18525.6894737|18531.4210526|18525.4000000|

RawPointCount各組相同。B2平均voxel點數約8303，v=0.05各組約19944；B2的內部RMSE較高但GT誤差較低，顯示不同點集與門檻下的內部殘差不能直接作真實精度排名。C組平均Fitness相近，仍有截然不同的災難配對與Mean L2；全序列因素平均會掩蓋單一配對錯解。完整逐幀／逐對CSV、因素摘要與官方時間序列HTML均保留。

## 7. Runtime、RSS與監控權限驗證

|條件|總程序時間 (s)|reconstruct含觀測 (s)|CPU user/system (s)|峰值RSS (GiB)|峰值RSS (bytes)|退出碼|
|---|---|---|---|---|---|---|
|B0|305.895459|293.751107|291.937289 / 2.855139|0.863235|926892032|0|
|B1|290.755403|無正常回傳|275.254486 / 3.035104|0.484528|520257536|1：配準失敗|
|B2|91.218485|79.691431|87.968107 / 1.810149|0.922440|990461952|0|
|C1|301.956052|290.213978|296.470614 / 3.671016|0.879028|943849472|0|
|C2|299.157768|287.339602|293.463405 / 3.825274|1.042709|1119600640|0|
|C3|305.920728|293.731400|297.681873 / 5.747826|0.812973|872923136|0|
|C4|306.577317|294.157500|298.173213 / 5.880233|0.814331|874381312|0|

全部正式嘗試保留3 GiB即時RSS護欄與0.5秒取樣，無超限。B1耗時是失敗前嘗試，不能與完整191張直接比較。總時間含子程序啟動、正式重建、評估／PNG／Seal／Run及觀測驗證；不含後續Explore／Query、離線分析及監控前置合成測試。CPU為CLI觀測區間；reconstruct含觀測時間與總程序時間分開。每條件只有一次量測，背景負載／快取不完全一致，不宣稱統計顯著的效能改善。

前次`resume_03`在C3正式Declare前，因沙箱拒絕`ps`而停止，沒有C3工作目錄或重建。此次先在沙箱重現，再經Codex正式權限核准機制，在具有必要權限的環境確認直接`ps`、Python subprocess、`record_command._rss_bytes()`及實際子程序持續取樣全部通過。原`record_command.py`完全未改；沒有sudo、替代取樣機制、關閉監控或只用結束後Peak RSS。

正常合成測試保留3 GiB護欄並得到4筆實際RSS；另以獨立合成低門檻案例驗證超限終止，以故障注入驗證監測失效終止，均保存SIGTERM退出碼-15及原因。這些是預期負面測試，不是正式重建失敗。C3與C4各自在Declare前再次通過相同前置測試，正式重建分別保存 **597／598筆**持續RSS，取樣峰值與程序Peak RSS另存於`final_scientific_audit.json`及各`command/execution.json`。外層核准執行console亦保留真正觀測／重建程序PID；同程序runpy執行原CLI，監測的是實際重建程序。

## 8. 地圖品質與比較圖

B2／C1／C3在同範圍俯視圖的後段紅色估計軌跡較接近黑色GT；B0／C2／C4的後段軌跡向相反方向偏移，地圖錯位與擴張較明顯。C4末張L2=6.262907 m、全域旋轉179.715064°，未因可完成而成為高精度結果。B2／C1／C3仍有殘餘位移、重影與缺口，不宣稱幾何完全正確。

各正式實驗保留原生去天花板PNG。比較圖用同一首相機座標與共同X/Z範圍、正式地圖固定上限取樣，沒有重新配準或GT校正。地圖點數也受累積位姿與天花板裁切影響，不作涵蓋率或品質分數；191張皆保留不代表實際樓層表面正確涵蓋100%。B1沒有完整地圖，不以部分輸出冒充完成。

![七條件Mean L2](/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/research_outputs/m32_20261118_suite_01/resume_04/seven_conditions_mean_l2.png)

### B組最終比較圖

![B組逐幀誤差](/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/research_outputs/m32_20261118_suite_01/resume_04/B_comparison/frame_errors.png)

![B組同範圍地圖](/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/research_outputs/m32_20261118_suite_01/resume_04/B_comparison/map_trajectories.png)

另存 `B_comparison/local_errors.png`、`eight_factors.png`、`comparison.csv`、`comparison.json`與各自SHA manifest；B圖只畫完整B0／B2，B1失敗明列於表格，沒有假造全序列曲線。

### C組最終比較圖

![C組逐幀誤差](/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/research_outputs/m32_20261118_suite_01/resume_04/C_comparison/frame_errors.png)

![C組同範圍地圖](/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/research_outputs/m32_20261118_suite_01/resume_04/C_comparison/map_trajectories.png)

另存 `C_comparison/local_errors.png`、`eight_factors.png`、`comparison.csv`、`comparison.json`與各自SHA manifest；B圖只畫完整B0／B2，B1失敗明列於表格，沒有假造全序列曲線。

## 9. 正式Turtle、Seal、來源與科學完整性

恢復前899個既有保護項目與全部歷史停止證據均核對；最後`final_integrity.json`及`final_scientific_audit.json`再次確認。六個完成條件各有唯一191張FullBatch Baseline、有效Seal及1522因素；Turtle儲存數值依API七位有效數字與原始float64評估核對。B1宣告bytes不變、未Seal、無完整Baseline。每個條件的執行標記SHA、正式CLI退出紀錄、位姿、矩陣、PNG、preregistration、Turtle與Seal摘要均另存最終審計。

|條件|Turtle SHA-256|Seal declaration digest|
|---|---|---|
|B0|def5c42211c0e38be6d59335200c1fe6337e786c6148ecc9e04d10f2f0ae1629|845f15146304e86b9ab26a884072eaa79b12c1d96544239f540273b9029088ec|
|B1|a463b3f34cef7025e6053f6c3bad768e5216960d33873f75a9259090ed5bb152|未封存（配準失敗）|
|B2|cf87f42267315f89fe190de4cb860f5690888eef4be628afc4beb19c8f871944|9f77a592a587b73497f80b473339fc47bd96563b274bbd171208c76470371fe7|
|C1|00474b06667531213d2d7f8481f7ad11712ee97467d8916b4a29048ee211266d|2d6e97f084a3c708032fa3b6d4ac2f00908f004108aec8eda56cd5f76996767e|
|C2|648bcf17206f10a9d37472ee22683a0bd026e3761568815db7569de779ad8500|18050afa36902ac68db2e7193e5f234174c416ab3630c620619d1655e02396e9|
|C3|0cf575da57caa9d4eb17c812500b4e1da26f435328ece27177c37a7f848e0b9d|491b274e6b3fd7a5d25de7c199fbf63ff75c41540f19536752ca9720b5c1d193|
|C4|c121bd26340bd031889e320e480ce8e66edf683182b225db5ab70ff9f940ff96|421646030f345ffdb7f807044d626c31c851de1929357c72ec3f46ef16d82bef|

教師核心及鎖定環境SHA全部與原suite一致：

|檔案|SHA-256|
|---|---|
|api.py|14684fcf3ddd72b02982828f890e127f74095ab67566ae80bed6db5127895fe2|
|load.py|7b6aeea3afddd9be5f4f6c1630bc791221c45c82000f38aa4ebc34afeaf26043|
|ontology/hw1.ttl|4a3d52dd838d8feae9bba042ca9bcd594e7f4de081fbdbaa3bbc290a84339258|
|pixi.lock|4cdd23ec892245d2a49297fd1c7a32fc9236cdcc37c15ae39abc274447312794|
|pixi.toml|47830fa0decaceddeaa9bc39ce112180add22864e84e22e7d4257aba545acc16|
|plot.py|7a624b52bc8f9121fd9fc69d7045404d8c62566d018e776a4541460e4d6e6337|
|reconstruct.py|9808795f16eea02d20b47b813bf87989c9cabc5fae471834e3a5d13a1b9adf28|
|utils.py|a77176342126573647ba5bf0eeaea9fbe9620e42c901154a77c79cc8862e9d41|

Capture SHA-256：`22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`。原M2／M3.1正式workspace Turtle SHA：`bba92ffc4a031772a8b1b6bc80dc3056b0c103a1b0382784c3c82d4edc3eb4b6`，Seal、baseline／selected子圖與原suite保存內容完全相同。

新權限授權只允許C3／C4，綁定執行commit `146c9d5`、12個歷史suite／停止／授權／C2審計紀錄SHA、前次授權SHA、當前工具SHA及權限測試產物SHA。C3／C4的preregistration與封存宣告註解引用此次授權及真實參數；CLI實際引數、190對的v／seed與宣告逐筆核對。參數註解不是新的Ontology Parameter，未修改Ontology或偽稱正式API已提供每run獨立參數模型。

### 精確OS Metadata Exclusion Policy與歷史停止

例外仍僅`experiments/.DS_Store`及`research_outputs/.DS_Store`，限定既存一般檔案；符號連結（即使內容SHA相同）、缺檔、目錄或第三路徑仍停止。預設驗證器不啟用例外；本次有授權的恢復範圍才啟用。每次另存實際路徑、歷史／目前SHA、存在狀態、檔案類型與差異，日誌完成後獨立凍結；不改寫或刪除任何中繼檔，不排除任何科學資料、研究產物或程式碼。

|精確路徑|原始歷史SHA-256|resume_04開始時SHA-256|
|---|---|---|
|experiments/.DS_Store|c58b7c32125c5542846c1a020beff62119d939b6320db407c45f801705e3a6ad|4eacb80ef42c2fba48a71ba7b7bf62db1964908e72fe0216ab0b0465ebb191ad|
|research_outputs/.DS_Store|538937e5925c6023d088ceac2ed85d40b6f99c2b2288893bd99628ffe8f954cb|199e57540697d64fa1c9c9262e1b26d9ca4b59f9267ce4a78f142821afe09e91|

前後SHA差異與可取得的中繼檔bytes均保留；最早變更前bytes未保存，不能由SHA還原，也不假稱已取得最早逐位元差異或確定OS寫入來源。兩路徑之外未發現未授權檔案異動；不能將這句誤寫為所有歷史SHA（含中繼檔）完全未變。

歷史鏈完整保留：

1. B0最初序列化停止與後置恢復，見原suite停止與`resume_01`，未重跑B0。
2. B1在70→71真實RANSAC失敗，見`resume_failed.json`、失敗保全及原B1停止文件，未重跑B1。
3. `resume_02/system_stopped.json`：C2已重建，但原finalize因`experiments/.DS_Store`差異停止。
4. `research_outputs/m32_20261118_final_recovery_stop_01/`：前次精確排除僅一個路徑，發現第二個`research_outputs/.DS_Store`差異，依原規則停止。
5. `resume_03/C2_audit/`：新增兩路徑授權後完成C2唯讀科學審計；`resume_03/system_stopped.json`保留C3啟動前`PermissionError: Operation not permitted: ps`。
6. `resume_04/`：本次正式權限修復、沙箱／核准環境監控測試、C3／C4各一次成功receipt、最終比較與完整性；沒有新的系統停止。

原B0／B1停止版驗收另保留於`M3_Parameter_Experiment_B0_Stop_Record.md`與`M3_Parameter_Experiment_B1_Stop_Record.md`；本次改寫前完整驗收文件另存`resume_04/acceptance.before.md`，Git亦保留所有歷史。未修改舊停止JSON、Traceback或歷史SHA清單。

## Discussion and Future Work Candidates

### 1. Registration Success Rate（只規劃，未實作）

目前pipeline在第一個無效粗／細配準即中止。B1可確認70→71失敗，前69對被接受，**無法推論71之後所有原始相鄰配對的成功率**。不能用69／190當「全序列逐對成功率」，亦不能用前綴成功比例代表整批。

未來可建立獨立、唯讀的逐對Registration診斷工具，對全部190個原始相鄰RGB-D配對分別測試預先固定的voxel／seed，記錄每對粗／細成功狀態、失敗位置、因素與資源，統計Registration Success Rate。失敗對不串接成全域軌跡；獨立逐對測試不冒充正式完整重建，也不能替代本研究已封存或失敗的紀錄。**本次沒有建立或執行此工具。**

### 2. Failure-aware Frame Selection（只規劃，未實作）

未來可研究非GT的配準品質／失敗訊號，預先定義選幀規則，再透過官方SPARQL與Selected Reconstruction驗證。必須重新估計保留影格間的新配對、保留首參考、報告保留影格比例與地圖覆蓋，並在共同影格上公平比較Mean L2。

不能直接跳過失敗矩陣後拼接後續轉換，不能用GT挑失敗影格，也不能將選幀的效果混同純voxel介入。M3.1只排除104仍使新103→105翻轉，是不能假設刪幀一定有效的既有反例。本輪沒有新選幀規則、沒有新Selected、沒有改原M3.1。

### 3. Reconstruction Robustness vs Accuracy

Robustness可包含非GT的有效配準回傳率、完整重建完成率、失敗配對位置與數量；Accuracy包含成功完整重建的191張Mean L2、離線局部旋轉／平移誤差與地圖幾何品質。兩者應分開，再共同解釋。

本研究B1未能完成，沒有完整精度；B0與C2雖完整完成卻有近180°錯解與高Mean L2。B1失敗對ICP曾有高Fitness，也不能替代被拒絕的RANSAC→ICP鏈。未來可能出現已完成前綴／局部誤差較低、整批卻中止的條件；不能只在成功組排名而隱藏完成率。另須將C2的系統中繼檔護欄停止與演算法失敗分開，本次C3／C4已完成；先前系統未啟動的時段不能算作低配準穩健性。

### 4. B1技術限制與失敗分析

v=0.03保留更多voxel點：前71張yield加總約為B0同影格的2.469倍，第71張80385點對B0的31947點；原始有效點數相同。與此同時normal radius從0.10縮到0.06 m、FPFH從0.25縮到0.15 m、RANSAC及ICP距離由0.075縮到0.045 m，max_nn仍30／100。

70→71的RANSAC零有效對應；當次mutual-filter剩6369互惠特徵候選後回退。這是與失敗相關的實際觀察，不足以將失敗歸因於任何單一參數、回退或幾何成因。既有核心先算ICP後才檢查粗／細結果，因此ICP曾從RANSAC返回的單位初值產生Fitness約0.98156及78903個對應；該對仍被正式核心拒絕，未接受或累積。0 RMSE伴隨零RANSAC對應不是完美配準。預處理71張不等於成功完成71張軌跡；只有前70張的已接受位姿前綴，**不能將部分影格誤差冒充完整191張Mean L2**。

### 5. 是否進一步研究D或結束Phase 1

現有B2與seed1的改善顯示尺度與抽樣值得討論，但未證明RANSAC confidence0.999的自適應早停是主要問題；幾何對稱錯解也可高內點。D可保留為未來受控假說，不能現在修改confidence、增加預算或搜尋seed。

本次原訂B／C研究已完成，應先人工驗收完整結果與歷史停止鏈，再決定Phase 1是否結束。兩個OS中繼檔例外已由使用者精確核准，不是本研究自行擴張政策。D仍只作未來受控假說；沒有修改confidence、增加預算、搜尋seed或執行額外候選。本輪完成後停止，Phase 2、Bonus與最終英文報告仍須另外授權。

## 10. 產物索引與Git

共同根目錄為`research_outputs/m32_20261118_suite_01/resume_04/`：

|位置|內容|
|---|---|
|authorization.json、protected.before.json|本次有限授權、歷史SHA鏈與899項前置保護清單|
|sandbox_monitor_probe/、authorized_monitor_probe/|無Capture／無重建的沙箱失敗及正式權限功能測試|
|monitor_before_C3/、monitor_before_C4/|各次Declare前的原監控器即時取樣與負面測試|
|status/C3.json、status/C4.json|各一次完整成功終態與證據SHA|
|B_comparison/、C_comparison/、all_comparison/|全部候選CSV／MD／JSON、逐幀／局部誤差、八因素與同範圍地圖|
|seven_conditions_mean_l2.png|七個預定條件摘要，B1保留失敗無完整值|
|final_integrity.json、final_scientific_audit.json|既有保全、七條件Turtle／Seal、因素、位姿／矩陣／PNG／執行標記來源SHA及取樣筆數|
|metadata_checks/、closing_metadata_checks.jsonl|兩個精確中繼檔的逐次存在狀態與SHA差異|
|C3_authorized_entrypoint.console.log、C4_authorized_entrypoint.console.log|正式權限入口、子程序PID、原CLI及後置作業console|
|final_provenance.json、final_manifest.json|最終Git／Snapshot、驗收文件SHA及研究產物SHA索引|

C3正式成果在`experiments/p1_m32_20261118_c_v005_s3_01/`及`research_outputs/m32_p1_m32_20261118_c_v005_s3_01/`；C4對應`s4_01`。每組保留preregistration、原宣告、執行標記、官方CLI／資源、191位姿／190對矩陣、1522因素、Explore四份HTML／Query、正式PNG、完整性、`official_after/`快照及SHA manifest。C2新增審計仍在`resume_03/C2_audit/`；其原正式成果沒有覆寫。

本次Git小步提交：

- `7387aec`：原ps即時監控前置工具與監測失效停止測試，`record_command.py`未改。
- `146c9d5`：權限恢復入口、有限授權與歷史保全銜接；C3／C4真正執行commit。
- 前次`945aa7a`／`d91dfa3`保存兩路徑政策與C2審計恢復工具，`e3f00b1`保存原ps權限停止驗收；更早執行與停止commit均保留。
- 正式執行前完整 **235 passed in 6.82s**，正式重建期間不並行跑測試；文件及query以`git diff --check`與實際產物／SHA核對。後續文件／query提交由Git紀錄識別。
- 保持main、無remote、不改寫歷史；`snapshot/pre-implementation`維持`291209750bd8ecf84f337112c9b92307e6be192a`。只追蹤工具、測試、MD與可重現query原始碼，Turtle／PNG／HTML／NPY／JSON／研究產物不加入Git。

**M3.2七條件研究與必要後置分析已完成；立即停止，等待人工驗收Phase 1。未自行開始Experiment D、Phase 2、Bonus或最終英文報告。**
