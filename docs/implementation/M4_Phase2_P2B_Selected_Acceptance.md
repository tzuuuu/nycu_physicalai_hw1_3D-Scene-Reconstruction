# M4.3 — Phase 2 Data Verification 與 P2-B Selected 驗收

日期：2026-11-19（臺灣）。

**M4.3 技術驗收通過：唯一正式 Selected 成功、同次科學成果保全、比較與圖表完成、已停止；供人工最終驗收。** 原生 Terminal 的11項必要 Preflight全部通過，40項測試通過、0失敗、0略過。正式重建僅一次；其後離線後處理精度缺陷已修復，原失敗紀錄完整保留，未重新重建。未提交最終作業。

## 1. 計畫決策與來源

本次正式取消 P2-C Different Route，詳見新增的 [取消決策](M4_Phase2_P2C_Cancellation_Decision.md)。不修改 [歷史 Phase 2 計畫](M4_Phase2_Capture_Plan.md)，不新增第二路線、P2-C Capture／Experiment／重建。保留 P2-A、P2-B、Phase 2 比較與交接。

固定 Experiment：`experiments/p2_114753116_a01_baseline_01`。
固定 Capture：`eval/_data/second_floor/114753116/P2_A_01`，320 張原始 RGB-D，Frame 1..320。

僅讀取已驗收 [M4.2](M4_Phase2_P2A_Baseline_Acceptance.md) 保存成果：`research_outputs/m42_p2_a01_baseline_01/` 與 `research_outputs/m42_p2a_closeout_01/`。已嚴格驗證結案 Manifest 77 項、原 Baseline 61 項、Frozen Capture 642 項與核心／Ontology／Pixi；原 Manifest 的歷史文件 SHA 對照已保存的 `runner_generated_acceptance_original.md`，沒有改寫歷史 SHA。Seal、唯一 FullBatch Run、2554 筆八因素與同次 Observer 交叉驗證通過。

原始 Capture、教師核心及原 Declaration／Seal 不修改；不重新執行 P2-A。既有 Turtle 執行前逐位元封存，執行後僅容許官方 Selected Run 新增 triples；Declaration bytes、Seal、Baseline 與全部歷史 triples 必須保留。官方 CLI 會更新共享 `reconstruction.png`，已設計執行前另存副本，原 `reconstruction_baseline.png` 不得變動。此為官方 Run 寫入契約，並非另造 Capture 或改寫 Baseline。

## 2. P2-A 八因素資料驗證

正式因素來源為 `m42_p2_a01_baseline_01/factors.csv`，已與正式 Turtle 及同次 `observation/events.jsonl` 核對。下表使用官方儲存精度，非重新量測。RawPointCount／VoxelizedPointYield 各 320 筆，其餘各 319 筆，合計 2554。

|因素|最小|p05|中位數|p95|最大|
|---|---:|---:|---:|---:|---:|
|RawPointCount|212865|219147.8|262144|262144|262144|
|VoxelizedPointYield|4013|5368.85|11022|17850.15|25134|
|CoarseRANSACFitness|0.7389817|0.82566203|0.9509453|0.99970362|1|
|CoarseRANSACRMSE (m)|0.009896865|0.019617265|0.02705007|0.034369618|0.04404025|
|CoarseRANSACCorrespondences|3672|4990.1|10558|17010|24435|
|ICPInlierFitness|0.7323405|0.82452494|0.9475837|0.99965383|1|
|ICPInlierRMSE (m)|0.009999617|0.015733816|0.01883593|0.024212058|0.02866493|
|ICPInlierCorrespondences|3639|4984.2|10557|16975.5|24421|

完整平均數、母體標準差及逐筆數值、品質尾端配對與非 GT 相對運動都保存於 `research_outputs/m43_p2b_preparation_01/`：`eight_factors.csv`、`eight_factor_statistics.csv`、`quality_tail_pairs.csv`、`non_gt_motion.csv`。圖表：`eight_factor_series.png`、`eight_factor_distributions.png`、`non_gt_motion_and_selection.png`。科學檔案 SHA 見該目錄 `manifest.json`；未納入 Git。

已檢視八因素時序圖與原 RGB 接觸表 `diagnostic_rgb_contact_sheet.png`，得到以下描述性結論：

- **弱支援配對**：以 current frame 命名，103–105、122–127、144–149 是 Correspondences 低尾區，Frame 2 亦偏低。最低 147→148：Coarse／ICP Fitness 0.7389817／0.7323405，Correspondences 3672／3639。這是較低支援，並非沒有有效配準。
- **視角與幾何風險**：73–75、103–105、146–151 的 RGB 可見近距離門框、大片淺色牆、窄幅遮蔽與轉向後逐漸露出的房內視野；與低體素點產出／配準支援相容。122–124 視野包含天花板與大片淺色區，124 顯示極亮；257–259 亦有明暗大幅變化。僅憑 RGB 不能斷言原因是感測曝光或深度故障，也不能把顏色變化直接等同 FPFH 特徵不足；核心主要使用幾何特徵。
- **高殘差**：Coarse RMSE 最高在 257→258（0.04404025m），亦見 83→84 的尖峰；ICP RMSE 最高在 254→255（0.02866493m），250 張以後高尾較多。低 Fitness、低支援與高 RMSE 並不總出現在同一配對，不能只用單一因素判斷成功。
- **非 GT 冗餘證據**：保存的 ICP 轉換顯示相鄰旋轉中位數 5.95885°、最大 6.09131°；相鄰平移中位數 0.00276856m、p95 0.20056554m。319 對中，258 對同時符合 ICP Fitness≥0.9、估計平移≤0.21m、旋轉≤6.2°，支持許多相鄰觀測有高局部重疊。高 Fitness 或近零平移不等於完全相同觀測，轉向仍會引入新表面。
- **橋接需求**：門框／轉角、103–105、122–127、144–151 的弱支援端點應保守保留；1→2（約0.47233m）與300→301（約0.40059m）的大估計位移也保留兩端。這些相對變換來自已保存的 Baseline ICP，不使用 GT。保留端點可避免直接跳過已知弱邊，不能保證其前後新跨格邊配準穩定。
- **GT 診斷限制**：既有末段 297–320 誤差增加只作評估問題；本次不因 GT 誤差決定保留或刪除。局部配準仍有效不代表累積漂移為零。沒有逐房間路線註記與表面 GT，不編造房間完整率。

## 3. 唯一研究假說與凍結規則

假說：減少高重疊短基線觀測可降低前處理、配準及地圖整合工作；保留已知品質尾端與大位移邊的端點，有機會維持連通與主要可見結構。預期時間下降，但 L2 可能改善、接近、惡化或配準失敗，均保留真實結果。

正式規則僅此一個（sparse-v1）：

1. 以原始索引保留所有奇數 Frame，另保留 Frame 320；Frame 1 必保留。
2. 在官方 Baseline 六個配對因素的各自 319 筆分布中，以 NumPy `percentile` 線性插值求分位數。Fitness／Correspondences ≤ 各自 p05，或 RMSE ≥ 各自 p95 的配對，保留其兩個端點。等號納入。
3. 已保存的 Baseline ICP 相對平移範數 >0.35m 的配對，保留其兩個端點。
4. 聯集去重並遞增排序。不重新編號，不載入 GT，不套用 Phase 1 Frame 104 排除規則；本次 Frame 104 實際保留。

凍結結果：**204 張、203 對、保留63.75%、刪減116張、預期新量測1626筆、最大原始索引步距2**。本次沒有依 Selected 結果搜尋其他保留率。

規則及完整索引：[selection_rule.json](m43/selection_rule.json)。SPARQL：[p2b_sparse.rq](m43/p2b_sparse.rq)。每張保留原因見準備目錄 `selected_indices.csv`。SPARQL 使用限定本次 Experiment 的 onBatch→hasFrame→frameIndex 關係，搭配凍結 VALUES、DISTINCT 及 ORDER BY；官方 `frames_from_sparql_query` 已唯讀驗證精確回傳204個唯一原索引。

- Selection 規則 SHA256：`2117058e33c89b84f44c63a8ae3e1f48592e86e1d15d5db47889924605d8dabe`
- SPARQL SHA256：`0252c1cd23cceeb3ac1b1953d67a672f116d3a7f51ef050501a3039f7abf834d`

規則與索引於正式 Selected 前已凍結；不因後續 GT 或地圖結果調整。p05／p95 是此單次介入的保守保留政策，不宣稱為普遍最佳品質門檻。

## 4. 官方 CLI 與因素寫入契約

已核查本機官方 `docs/reconstruct.md`、`reconstruct.py`、`api.py:frames_from_sparql_query`、`api.py:write_run`。沿用相同 Experiment／Capture。Selected 的連續段僅用於 spliceCount／maxGapLength 記錄，實際會將全部選定索引攤平成一條序列，逐一配準至前一個 Selected 影格，包括跨索引缺口；不是每個連續段獨立重建。

官方 sealed Selected 呼叫 `utils.reconstruct` **未傳入 pipeline measurement callback**，`write_run` 只寫入 Selected Run、mapMeanL2、runFrameCount、usedFrame 及 splice metadata。因此：

|證據|保存位置與數量|
|---|---|
|原始 FullBatch 八因素|原 Turtle，2554 筆，全部不變|
|Selected 新單張／新配對八因素|同次唯讀 Observer：408＋1218＝1626 筆；JSONL、CSV、統計檔，存於新正式目錄|
|Selected 新變換與位姿|同次 RANSAC／ICP 各203組4×4；204組4×4 Estimated Poses|
|Selected 完整回傳地圖|同次 map_points.npy／map_colors.npy，全部點與色，各自 SHA|
|官方 Selected Run|由官方 `--override-experiment` 新增，非手寫 Turtle|

不向原 sealed 因素集硬加新配對因素，不將原相鄰因素冒充跨格新量測。對原 Turtle 逐 triple 比較，任何歷史 triple 移除或變動都停止驗收；Declaration bytes 與 Seal 另驗證。原 Turtle bytes 也完整封存，沒有覆寫歷史 Manifest。

固定 Open3D Point-to-Plane ICP、registration voxel0.05m、Seed0、OMP_NUM_THREADS=1、map-only down_voxel0.05m。GT 只在同次重建地圖已完整保存後供官方離線評估；不作 RANSAC 初值、修正或最佳擬合。

## 5. 工程準備、Preflight 與唯一執行

新工具：`scripts/m43_analysis.py`（唯讀分析）、`scripts/m43_selected.py`（整合 Preflight／單次 CLI）、`scripts/m43_results.py`（離線比較），沿用原 `m42_monitor.py`／`m42_observer.py`，不改核心或原監測器。

正式執行前要求：凍結科學資料642項、Baseline／Turtle／Seal／77項結案Manifest、核心／Ontology／Pixi、Snapshot `291209750bd8ecf84f337112c9b92307e6be192a`、選幀與來源SHA、乾淨已提交Git、原生程序樹權限與零skip監測／Observer／Selected合成測試、磁碟／RAM／完整地圖容量、官方唯讀Query、受保護檔案快照、最後來源複查全部通過。

程序樹RSS每0.5秒取樣、3GiB護欄、獨立8秒watchdog，沿用M4.2。保留共享頁重複計數與瞬間峰值可能漏採的限制。`.DS_Store` 依已驗證分層政策獨立記錄前後狀態與SHA，僅接受檔名／一般檔案／版本1 Bud1檔頭／Finder類型均符合者；其餘科學檔案不放寬。

唯一正式目錄：`research_outputs/m43_p2b_selected_01/`。全部必要 Preflight 通過後以 `mkdir(exist_ok=False)` 建立永久單次鎖；失敗不得清除鎖或自動重跑。每次 Preflight 有唯一時間戳目錄，未通過不建立正式目錄、不啟動負載。

以下為**已執行的一次性歷史命令**；正式目錄及Selected Run已存在，不再執行：

```bash
cd /Users/alyssa/Documents/Codex_Workspace/physicalai_hw1 && OMP_NUM_THREADS=1 MPLCONFIGDIR=/private/tmp/m43_matplotlib /Users/alyssa/.pixi/bin/pixi run -e habitat python -m scripts.m43_selected run
```

此次命令已完成所有原生 Preflight及正式一次 Selected；比較後處理其後以離線方式修復完成。正式 Selected 的核心 CLI 由 runner 原樣傳入 `reconstruct.py --experiment … --selection-query … --override-experiment --version open3d --voxel-size 0.05 --seed 0 --down-voxel 0.05 --no-vis`。只有合成資料測試可以多次執行，不碰正式Capture。

## 6. 事前比較方式與驗收準則

同一原首相機參考、相同 GT 索引、Euclidean camera-center L2，不做 GT 最佳擬合。

|比較項目|P2-A|P2-B|
|---|---|---|
|完整輸入數|320|204（凍結且實測）|
|完整Mean L2 (m)|0.07025845236530649|0.04487258932911286|
|Same-Frame Mean L2|0.07170949737501646（保存位姿取S）|0.04487258932911286（只用S重建）|
|Worker時間 (s)|220.751497|163.365968959|
|重建函式觀測時間 (s)|207.318515709|145.343667667|
|完整Map Point Count|2,054,529|1,277,572|
|八因素來源|正式Turtle及同次Observer2554筆|新Observer1626筆，已驗證|

兩者 Worker 時間均含匯入、Observer、完整地圖／位姿保存、評估、原生圖及官方Run寫入；不含Preflight或後續獨立比較Worker。Baseline另有因素量測／Seal成本，Selected另有Query／usedFrame寫入成本；另列重建函式call-to-return計時及Observer成本，避免把不同儲存成本當成純演算法加速。

Same-Frame僅公平化評估目標：P2-A使用全部320張歷史資訊，P2-B只用S，不代表輸入資訊相同。

事前的描述性取捨檢核：Worker時間低於Baseline、Same-Frame Mean L2增加不超過0.05m、完整Baseline點雲至少85%在Selected點雲0.20m內。這是本次研究可接受性定義，不是作業評分門檻或統計檢定；三者分開呈現，Selected未更準不自動判失敗。另報0.20m體素佔據IoU、兩個方向全點最近鄰距離、四個固定空間象限與視覺結構。

Coverage使用完整同次地圖，不用繪圖樣本；固定座標中的相對觀測地圖一致性同時受視角、密度與漂移影響，不能當成絕對表面完整率。不同點數／影格數不能直接解讀為演算法優劣。低支援或高殘差與誤差上升的關聯只作描述，不宣稱因果。

## 7. 正式結果產物與交接

離線結案目錄 `research_outputs/m43_p2b_closeout_01/analysis/` 已新增 `comparison.csv/json`、`same_frame_l2.csv`、`selected_factors.csv`、`factor_statistics.json`、`scene_coverage.json`、`spatial_coverage.csv`、完整點雲距離陣列、`research_conclusions.md`，並產生共同尺度俯視／3D、紅Estimated黑GT軌跡、Same-Frame L2、八因素分布及時間／誤差／影格數圖。完整資料與確定性stride繪圖樣本分開，`figure_manifest.json`記錄來源與SHA；不以隱藏第二次重建補造缺失。

失敗則保存真實最後配對、部分因素與變換、完成前綴、traceback及監測原因；沒有完整結果就不報完整L2／地圖／成功Run，也不自動換Seed、Voxel或Selection重跑。

六項研究問題的正式回答見第11節。共同尺度俯視、3D、軌跡、八因素與分區圖片已檢視；技術驗證完成，人工最終驗收仍由使用者決定。不得由一次實驗推論顯著性或最佳影格比例。

Git僅提交必要新程式、測試、規則／Query、決策及驗收文件。Capture、生成Turtle、NPY點雲、圖表、大型研究產物都保持忽略。來源綁定在 `m43/readiness.json`；正式執行收據另記實際Git commit及所有tracked sources SHA。Manifest不含自身。本次不開始P2-C、Bonus、新Seed／Voxel、英文報告或Submission ZIP；不宣稱最終作業已提交。

## 8. 沙箱工程測試紀錄（正式執行前）

整合測試結果：**34 passed、6 skipped**。6項skip全部為已知沙箱`ps`限制的原生程序樹測試；其後Mac Terminal以`M42_REQUIRE_NATIVE=1`實際取得40項全部通過、零skip，不以沙箱結果代替原生驗證。合成測試涵蓋官方Selected CLI／跨格配對／GT延後讀取、歷史triple保全、同次完整地圖與位姿、失敗前綴、正式鎖與Preflight拒絕、固定首相機／索引誤差、完整比較圖表／Coverage流程。沒有使用正式Capture進行測試重建。


## 9. 正式執行與離線修復歷史

執行來源 Git：`c91078d879f4a65c9525bcfcfc76468929c7a292`。正式目錄 `research_outputs/m43_p2b_selected_01/` 已消耗本次唯一授權；`observation/observer_summary.json`證明reconstruct_calls=1、204張／203對完整回傳，Worker exit=0、reason=null。沒有新Capture、Baseline重跑、第二次隱藏重建或參數／索引調整。

Terminal最初的`terminal_status.json`保留 **Selected stopped; acceptance withheld; no retry**，原因是獨立後處理在驗證Baseline時遇到3.2020728846×10⁻⁹m差異。這不是RANSAC／ICP失敗：正式Selected與Turtle Run在此之前已成功保存。

根因為Capture GT本身是float32，而新離線`frame_errors`在轉float64前便做了首相機平移相減；官方`utils.visualize_and_evaluate`與M4.2則先轉float64。先以實際保存資料及最小合成float32測試重現失敗，再補上明確float64轉型；維持1e-12檢查，不放寬容許值。修復後Baseline及Selected重算Mean L2與官方值差異皆為0。回歸與相關測試 **10 passed**，未碰核心、GT、正式位姿或地圖。原合成測試主要用float64／零首平移，未涵蓋真實float32在非零首相機位置下的相減精度；新增此回歸案例以避免再發生。

原Terminal文件已逐位元封存於`m43_p2b_closeout_01/terminal_generated_acceptance_original.md`，原Manifest的39項已先完整驗證。原失敗後處理的stdout／stderr／RSS、terminal_status及manifest不修改；新結果存到獨立結案目錄。執行時的原程式及文件bytes依Git及preregistration SHA存於`execution_sources/`，與本次修復來源分開。

|階段|時間(s)|程序樹RSS峰值(bytes)|狀態|
|---|---:|---:|---|
|P2-A正式重建Worker|220.751497|1198620672|原M4.2成功|
|P2-B正式重建Worker|163.365968959|751648768|成功，唯一一次|
|P2-B原離線後處理|4.117353542|374587392|精度檢核停止，保留原紀錄|
|離線修復／完整比較Worker|20.751796916|741687296|成功，無重建|
|離線詳細圖表Worker|7.627151791|779075584|成功，無重建|

全部上述負載均由原程序樹監測器與3GiB護欄監測，watchdog解除。正式Selected共324筆RSS取樣。離線後處理與圖表成本獨立揭露，不混入Selected重建runtime。Observer額外觀測時間：P2-A0.525915282s、P2-B0.891288812s；函式時間含函式執行期間的Observer，完整回傳地圖匯出在函式計時停止後，仍屬Worker時間。

## 10. 八因素、累積漂移與場景比較

下表為全體各自結果的**中位數**；原始所有min／p05／mean／std／median／p95／max見`analysis/factor_statistics.json`。原Turtle為官方儲存精度，Selected為同次Observer原始浮點；兩者不是相同配對母體。

|因素|P2-A中位數|P2-B中位數|
|---|---:|---:|
|CoarseRANSACCorrespondences|10558|9873|
|CoarseRANSACFitness|0.9509453|0.916987137|
|CoarseRANSACRMSE|0.02705007|0.0277390976|
|ICPInlierCorrespondences|10557|9833|
|ICPInlierFitness|0.9475837|0.915486726|
|ICPInlierRMSE|0.01883593|0.0198003471|
|RawPointCount|262144|262144|
|VoxelizedPointYield|11022|10893.5|

Selected的單張RawPointCount及VoxelizedPointYield已按相同原索引逐筆核對Baseline，全部相等；其整體分布變動來自抽樣組成。新配對量測包含87對原索引步距1、116對步距2，全部正支援、有限有效變換。步距2的ICP Fitness中位數0.897988，步距1為0.920283；Selected整體Fitness比FullBatch低，RMSE略高、對應點中位數略少，與跨格較低局部重疊相容。步距1組亦受保守保留弱邊的選擇影響，不能將兩組當成隨機對照。

最低Coarse／ICP Fitness在43→45，分別0.709430756／0.711858235，仍成功；19→21、289→291亦較低。最低Coarse／ICP Correspondences仍在147→148，3672／3639；該弱支援橋接邊實際保留。最高Coarse RMSE在257→258（0.044040255m），最高ICP RMSE在254→255（0.028664935m）。沒有失敗影格或零支援配對；不可把這些低值配對標成重建失敗。

Selected最大L2為0.155863799533m、位於原Frame320；中位數0.038434006764m、p95為0.106105297949m。Baseline最大為0.283142486707m，也在320。末段誤差仍上升；Selected最大的單步L2增加在296→297（0.018766536m）、300→301（0.017985431m）、297→299（0.014809328m）。這些只是事後診斷，沒有回頭調整選幀。

|原索引區間|S內張數|P2-A Same-Frame Mean L2(m)|P2-B Mean L2(m)|
|---|---:|---:|---:|
|1–100|59|0.010996572|0.010693896|
|101–200|64|0.050127230|0.043368311|
|201–296|63|0.110270786|0.060791704|
|297–320|18|0.212485416|0.106534391|

204個共同索引中仍有36張Selected誤差高於Baseline；平均改善不代表逐張改善。六個配對因素與Selected L2增量的描述性Spearman係數約−0.024至0.063，未顯示單一局部因素能直接解釋累積誤差；不作顯著性檢定或因果結論。完整配對、低尾與誤差增量位置見`report_details/selected_pair_diagnostics.csv`、`diagnostics_summary.json`。

完整地圖比較（固定原首相機，未擬合）：

- Baseline→Selected全點最近鄰≤0.20m：**99.997517679%**；距離中位數0.014976430m、p95 0.066840584m。
- Selected→Baseline≤0.20m：99.998982445%；中位數0.013606843m、p95 0.062359547m。
- 0.20m佔據體素：Baseline6433、Selected6158、交集5615、聯集6976，IoU **0.804902523**。較寬的距離門檻接近飽和，不能將99.9975%宣稱為實際房間／表面完整率；IoU對體素邊界與位姿差異敏感。
- 超過0.20m的Baseline點共51個（不是51個表面）：原相機LowX／HighZ43個、HighX／HighZ7個、LowX／LowZ1個，HighX／LowZ0個；多在顯示圖下端的外緣／零散結構。`relative_map_disagreement.png`以全51點標示，背景才使用繪圖抽樣。

視覺檢視：下端封閉區、中央狹長連通、低X側寬廣區、右側矩形分支與高顯示Z端區，在兩個地圖仍可辨識，未見整個大型區塊消失。Selected完整地圖點數較少，圖中部分外緣及細小結構較稀疏；但兩圖stride不同，不能直接由顯示密度量化觀測損失。高顯示Z端紅／黑軌跡分離較小，但仍存在。不能把原本留白認定為刪幀造成的房間漏建；也不能只靠stride點圖區分未觀測、遮蔽、深度缺失、去天花板或真正幾何缺失。

分區圖的Low／High Z依**原相機Z**，顯示垂直座標為−原Z；不是房間名稱。兩個3D報告圖使用相同尺度／視角／座標範圍。原並排3D圖右側標籤邊距不足仍保留，報告使用另存的`reconstruction_3d_baseline_report.png`及`reconstruction_3d_selected_report.png`；只改顯示邊距，沒有補面、改位姿或重建。

## 11. 六項研究回答與驗收

1. **是否降低時間？** 是，本次Worker減少57.385528041s（25.9955%）；同一重建函式邊界由207.318515709s降至145.343667667s（29.8935%）。兩者Worker均含完整輸出及官方寫入，但Baseline量測／Seal與Selected Query／Run寫入成本不同，不能稱為純演算法加速比例。
2. **定位精度如何？** 本次相同S集合Mean L2由0.071709497375m降至0.044872589329m，下降0.026836908046m。各自完整結果則為0.070258452365m／0.044872589329m，必須與Same-Frame結果分開。沒有GT最佳擬合，未聲稱輸入資訊相同。
3. **哪些因素相關？** 較少影格與203而非319對配準對應較低計算量；跨格重疊降低使Fitness下降、RMSE略升，弱Correspondences橋接區仍存在。局部品質下降而全域平均誤差下降，顯示這些代理量不能單獨預測累積漂移；因果機制可能涉及配對路徑與誤差抵消，現有單次資料無法確認。
4. **哪些場景受影響？** 可見大型布局與中央連通保留；相對差異主要是下端邊緣、零散結構與密度變化。沒有足夠證據斷言特定命名房間漏建或所有表面完整；上端與末段仍見軌跡偏離。
5. **是否支持效率品質取捨？** 是，本次三項事前條件全部通過：Worker較短、Same-Frame Mean L2增加≤0.05m、Baseline點雲≥85%位於Selected的0.20m內。這支持此Capture下的sparse-v1介入，並非因Selected更準才事後定義成功。
6. **限制？** 單Capture／單路線／單Seed／單次正式Selected；無統計顯著性、無最佳保留率或跨路線泛化結論。0.20m距離指標寬鬆、完整點有重複取樣權重；相對Coverage受雙方漂移、取樣、遮蔽、深度與官方去天花板影響。沒有真實表面GT，局部配準成功不保證無全域漂移。

**M4.3技術驗收通過並停止，人工最終驗收待使用者確認。** 正式實驗一次完成、後處理修復不消耗新的重建、凍結規則未變、科學來源驗證通過。Phase2研究結果整理與交接完成；P2-C已取消，不列為剩餘實驗。未開始新Capture、Bonus、其他Seed／Voxel、英文報告、Submission ZIP，未宣稱最終作業提交。

## 12. Git／SHA與交接位置

正式Selected完整保存在`m43_p2b_selected_01/observation/`：204組float64(4,4)位姿、203組RANSAC與ICP變換、1,277,572點／色，皆為同次正式回傳，非第二次重建。Selected新因素1626筆另存JSONL／CSV；原Turtle2554筆Baseline因素不變。歷史22692個RDF triples全部保留，僅新增211個Selected triples；Declaration bytes不變、Seal有效。

- Selected map_points SHA256：`9567cd97ff77babefe025a20452d8cc1b69d36044cf5fbafdc64683302224726`
- Selected map_colors SHA256：`9c08bcf5aeebc831904792344f99ea6cf4aed6cff5fb2affab4a82771a8dd81b`
- Selected camera_poses SHA256：`788d78560711ba9e7c325f7144030937d8c5a09570da80eb356c976a91d80a68`
- Selected pairwise ICP SHA256：`a6d99cea545e9e9ead3fb3e4d378d8abcab3cb4722521af621b36b046d2730c1`

未變動的原readiness／preregistration仍指向正式執行前Git與SHA，不將離線修復倒填成當時版本。原M4.2 Manifest的Turtle／共享圖SHA對照Selected執行前完整快照，M4.3原Manifest的文件SHA對照Terminal文件快照；新最終文件另由結案Manifest與Git綁定。不是改寫舊SHA使舊驗證假通過。

`m43_p2b_closeout_01/audit_before_analysis.json`／`audit_after_analysis.json`／`audit_final.json`記錄642項Frozen Capture、2099項受保護科學檔案、77項M4.2結案Manifest及62項原M4.2 Manifest（含原文件快照）、39項原M4.3 Manifest。`.DS_Store`僅依原分層政策記錄前後；科學SHA不放寬。結案`provenance.json`綁定修復來源Git、來源SHA與文件版本轉換，`manifest.json`不含自身。

完整圖表來源、stride及SHA見`analysis/figure_manifest.json`、`report_details/figure_provenance.json`。Baseline繪圖stride14／146753點；Selected stride9／141953點，兩者都未替代完整地圖；Coverage計算使用全部點。另見 [Phase2交接](Phase2_Final_Handoff.md)。Git僅保存必要程式／測試／文件；所有生成Turtle、Capture、點雲及大型研究產物保持Git忽略。
