# M4.3 — Phase 2 Data Verification 與 P2-B Selected 驗收

日期：2026-11-19（臺灣）。

**目前狀態：P2-A 資料驗證完成、唯一 P2-B 規則與索引已凍結；正式 Selected 尚未開始，M4.3 尚未完成驗收。** Codex 沙箱已實測禁止 `/bin/ps` 讀取程序樹；正式負載必須由下列整合式 Mac Terminal 命令通過原生 Preflight 後啟動。本文件不把合成資料測試當成正式結果。

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

在 **Mac Terminal** 執行以下單一命令（本次已授權，不需逐項核准）：

```bash
cd /Users/alyssa/Documents/Codex_Workspace/physicalai_hw1 && OMP_NUM_THREADS=1 MPLCONFIGDIR=/private/tmp/m43_matplotlib /Users/alyssa/.pixi/bin/pixi run -e habitat python -m scripts.m43_selected run
```

此命令整合所有原生 Preflight、正式一次 Selected、RSS監測、同次輸出、圖表與來源驗證。正式 Selected 的核心 CLI 由 runner 原樣傳入 `reconstruct.py --experiment … --selection-query … --override-experiment --version open3d --voxel-size 0.05 --seed 0 --down-voxel 0.05 --no-vis`。只有合成資料測試可以多次執行，不碰正式Capture。

## 6. 事前比較方式與驗收準則

同一原首相機參考、相同 GT 索引、Euclidean camera-center L2，不做 GT 最佳擬合。

|比較項目|P2-A|P2-B|
|---|---|---|
|完整輸入數|320|204（凍結）|
|完整Mean L2 (m)|0.07025845236530649|待正式執行|
|Same-Frame Mean L2|由保存的320個位姿取S，不重建|新建的S位姿，待執行|
|Worker時間 (s)|220.751497|待正式執行|
|重建函式觀測時間 (s)|207.318515709|待正式執行|
|完整Map Point Count|2,054,529|待正式執行|
|八因素來源|正式Turtle及同次Observer2554筆|新Observer1626筆，待實測|

兩者 Worker 時間均含匯入、Observer、完整地圖／位姿保存、評估、原生圖及官方Run寫入；不含Preflight或後續獨立比較Worker。Baseline另有因素量測／Seal成本，Selected另有Query／usedFrame寫入成本；另列重建函式call-to-return計時及Observer成本，避免把不同儲存成本當成純演算法加速。

Same-Frame僅公平化評估目標：P2-A使用全部320張歷史資訊，P2-B只用S，不代表輸入資訊相同。

事前的描述性取捨檢核：Worker時間低於Baseline、Same-Frame Mean L2增加不超過0.05m、完整Baseline點雲至少85%在Selected點雲0.20m內。這是本次研究可接受性定義，不是作業評分門檻或統計檢定；三者分開呈現，Selected未更準不自動判失敗。另報0.20m體素佔據IoU、兩個方向全點最近鄰距離、四個固定空間象限與視覺結構。

Coverage使用完整同次地圖，不用繪圖樣本；固定座標中的相對觀測地圖一致性同時受視角、密度與漂移影響，不能當成絕對表面完整率。不同點數／影格數不能直接解讀為演算法優劣。低支援或高殘差與誤差上升的關聯只作描述，不宣稱因果。

## 7. 正式結果產物與交接

正式執行成功後新增 `comparison.csv/json`、`same_frame_l2.csv`、`selected_factors.csv`、`factor_statistics.json`、`scene_coverage.json`、`spatial_coverage.csv`、完整點雲距離陣列、`research_conclusions.md`，並產生共同尺度俯視／3D、紅Estimated黑GT軌跡、Same-Frame L2、八因素分布及時間／誤差／影格數圖。完整資料與確定性stride繪圖樣本分開，`figure_manifest.json`記錄來源與SHA；不以隱藏第二次重建補造缺失。

失敗則保存真實最後配對、部分因素與變換、完成前綴、traceback及監測原因；沒有完整結果就不報完整L2／地圖／成功Run，也不自動換Seed、Voxel或Selection重跑。

目前六項研究問題（時間、定位精度、因素關聯、受影響場景、效率品質取捨、結果限制）尚不能以Selected實證回答。已具備分析與檢核流程，正式數值須等上述唯一執行。成功回傳後仍需檢視共同尺度圖、缺失結構與失敗位置，更新本驗收及Phase2交接；不得由一次實驗推論顯著性或最佳影格比例。

Git僅提交必要新程式、測試、規則／Query、決策及驗收文件。Capture、生成Turtle、NPY點雲、圖表、大型研究產物都保持忽略。來源綁定在 `m43/readiness.json`；正式執行收據另記實際Git commit及所有tracked sources SHA。Manifest不含自身。本次不開始P2-C、Bonus、新Seed／Voxel、英文報告或Submission ZIP；不宣稱最終作業已提交。

## 8. 沙箱工程測試紀錄（正式執行前）

整合測試結果：**34 passed、6 skipped**。6項skip全部為已知沙箱`ps`限制的原生程序樹測試，不能視為原生Preflight已通過；Mac Terminal將以`M42_REQUIRE_NATIVE=1`強制40項全部通過、零skip。合成測試涵蓋官方Selected CLI／跨格配對／GT延後讀取、歷史triple保全、同次完整地圖與位姿、失敗前綴、正式鎖與Preflight拒絕、固定首相機／索引誤差、完整比較圖表／Coverage流程。沒有使用正式Capture進行測試重建。


## Terminal 正式執行結果（自動新增）

狀態：**Selected stopped; acceptance withheld; no retry**。

```json
{
  "error": "Traceback (most recent call last):\n  File \"/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/scripts/m43_selected.py\", line 225, in run\n    if not post['passed']:raise RuntimeError('Selected returned; validation/postprocess failed; no reconstruction retry')\nRuntimeError: Selected returned; validation/postprocess failed; no reconstruction retry\n"
}
```

完整證據：`research_outputs/m43_p2b_selected_01/`。人工檢視圖表與最終驗收仍須完成；未提交最終作業。
