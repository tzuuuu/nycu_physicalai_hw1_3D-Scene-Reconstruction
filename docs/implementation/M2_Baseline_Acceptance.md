# M2 驗收：Map Voxel 最小 CLI 修改、Preflight 與正式 Phase 1 Baseline

## 結果與停止點

使用者已核准 C 級最小修改。本次已完成 `--down-voxel` CLI、回歸測試、5／10／20 張新舊 Preflight 比較，以及官方完整 191 張 Baseline、1522 筆因素／Seal／Baseline Run 驗證與 Explore／Dashboard 檢視。**停止於 M2，未建立 Selected、未進入 M3、Phase 2、Bonus 或英文作業報告。**

正式 Mean L2 為 **3.174055104788137 m**。流程與資料完整性驗證通過，但地圖與軌跡有明顯漂移；這是需要保留及分析的 Baseline 結果，不宣稱重建品質良好。

本紀錄接續歷史的 M2_Preflight_Review.md；該文件記載當時尚未核准 CLI 旗標、M2.1 尚未啟動的狀態，保留不覆寫。

## 授權修改與測試

核心程式僅修改 reconstruct.py：新增可選浮點參數 `--down-voxel`，預設 None，拒絕非正值、NaN、Inf；在未封存 Baseline 與 sealed／Selected 兩個呼叫位置傳入 utils.reconstruct。未更改其他旗標、預設配準參數或官方流程。

**utils.py、Depth Unprojection、RANSAC、ICP、GT 評估、Callback、api.py、Ontology 與原始資料均未修改。** 既有 down_voxel 僅作用於地圖副本。

另新增／擴充獨立紀錄與唯讀驗證工具，不取代 CLI。預設 pytest 範圍仍排除第三方與模擬擷取 e2e。

```bash
pixi run --locked -e habitat python -m pytest -q
```

最終結果：**148 passed in 13.33s**。

- CLI 獨立測試 13 案：未封存 Baseline、sealed Baseline、Selected 的 None／0.05 傳遞；非法數值；真實 Pipeline 的位姿／八項因素／Mean L2 不變性。
- Preflight 工具共 8 案；程序紀錄／RSS 護欄 3 案；唯讀因素彙整 2 案。
- 既有 M1／非擷取 simulator 測試保持通過。
- CLI 路徑測試使用明確 mock 隔離參數傳遞，沒有建立正式 Selected 實驗；不變性測試另用真實 Open3D 合成 Pipeline。

## 同一批資料的新舊 Preflight

資料：191 組一樓 RGB-D、GT=(191,7)，512×512、HFOV 90°、uint16 毫米深度；缺明示 scale 時沿用 1000，僅讀檔時換算一次。未修改 JSON 或資料。

所有測試固定 version=open3d、registration voxel=0.05 m、seed=0；唯一差異為 map down_voxel 從 None 改為 0.05 m。

```bash
MPLCONFIGDIR=/tmp/physicalai-m2-matplotlib \
pixi run --locked -e habitat python scripts/m2_preflight.py \
  --data-root eval/_data/first_floor \
  --output research_outputs/m2_20261118_mapvoxel_01/frames_05 \
  --frames 5 --down-voxel 0.05
# 10／20 張分別使用 frames_10／frames_20 新目錄。
```

| 張數 | Mean L2：新舊相同 (m) | 重建秒數：舊→新 | 含評估／PNG秒數：舊→新 | 峰值 GiB：舊→新 | 裁切後地圖點數：舊→新 |
| --- | --- | --- | --- | --- | --- |
| 5 | 0.00316569952 | 4.1406→3.9236 | 15.1893→4.2487 | 0.4671→0.4060 | 666223→41992 |
| 10 | 0.00513626047 | 8.2769→8.0348 | 18.0825→8.3571 | 0.7684→0.4510 | 1335522→86570 |
| 20 | 0.00698689362 | 15.0951→14.4622 | 24.7106→14.7904 | 0.9268→0.5056 | 2672499→154767 |

三組的逐影格預測相機位置最大差皆 **0**；排除時間與記憶體欄位後，全部逐幀／配對因素 payload **完全相同**，Mean L2 亦完全相同。因素數為 34／74／154。

20 張地圖點數減少約 94.2%，峰值下降約 45.4%。主要牆面／地板輪廓及紅黑軌跡仍可辨識，邊界最大差約 0.0093 m，符合體素平均造成的小幅邊界變化。未量化全樓層覆蓋百分比。

新舊含圖片時間差包含 Matplotlib 字型快取暖機差異，不能全部歸因於 map voxel；重建秒數另行列出。未執行 down_voxel=None 的完整 191 張對照。

## 資源安全門

正式執行前再次檢查：實體 RAM 16 GiB、系統 memory_pressure free percentage 約 45%、swap 已用 3616.88 MiB、磁碟剩餘 10.261 GiB。該百分比不當作程序可配置 RAM 的保證。

在 5→10、10→20 張的程序峰值增量趨勢下，完整批次約估 1.4～2.1 GiB；固定匯入開銷使原始「整個峰值／原始點數」外推偏保守。估計僅供風險判斷，不當作實測，也未單憑低於 16 GiB 宣稱安全。

安全措施：外層每 0.5 秒以 ps 記錄子程序 RSS；超過 **3 GiB** 或無法監測即中止。只監測／終止程序，不更動演算法、影格或實驗值。正式執行時實測最大 RSS 未接近護欄，完成後 swap 仍為 3616.88 MiB、記憶體 free percentage 約 45%，未見 swap 異常增長。

## 官方完整 Baseline

Experiment：`p1_baseline_20261118_map005_s0_01`。

正式執行前使用原入口建立工作區：

```bash
pixi run --locked -e habitat python api.py declare \
  --name p1_baseline_20261118_map005_s0_01 \
  --data-dir eval/_data/first_floor --floor 1
```

宣告的 Pipeline Prediction、Baseline Prediction、實驗名稱及 map voxel 揭露已於重建前填寫；未預設品質 Pass/Fail，也未在看見完整結果後倒填。原文備份與參數預先記錄於 `research_outputs/m2_phase1_baseline_20261118_01/`。

原官方重建入口與參數：

```bash
.pixi/envs/habitat/bin/python reconstruct.py \
  --experiment experiments/p1_baseline_20261118_map005_s0_01 \
  --version open3d --voxel-size 0.05 --seed 0 --down-voxel 0.05 --no-vis
```

實際由 `scripts/record_command.py` 直接啟動上列子程序，外層紀錄 stdout/stderr、資源及總時間。外層未改寫重建函式或官方 workflow。

| 項目 | 實測／驗證 |
| --- | --- |
| 原始／重建／評估幀數 | 191／191／191 |
| 保留比例 | 100% |
| Mean L2 原始值 | 3.174055104788137 m |
| Turtle 儲存值 | 3.174055 m，依原 API 的 7 位有效數字序列化 |
| 總程序時間 | 286.378044 秒，約 4 分 46.38 秒 |
| 程序峰值 RSS | 891551744 bytes = 0.830322 GiB |
| 0.5 秒取樣峰值 | 887275520 bytes；未觸發 3 GiB 護欄 |
| 因素 | 1522 筆，全部有限、Measured，無缺漏／重複 |
| Baseline Run | 存在、FullBatch、runFrameCount=191 |
| Selected Run | 不存在，符合本次授權 |
| 退出碼 | 0 |

總時間含子程序啟動、讀取、重建、評估、PNG、封存與 run 寫入；不含之後的 Explore。不同於 Preflight 已先載入套件的計時邊界，不能直接當作純配準速度比較。正式 CLI 沒有各 stage 計時輸出，本次不虛構。

演算法固定參數：Normals radius=0.1 m/max_nn=30；FPFH radius=0.25 m/max_nn=100；RANSAC mutual=True、distance=0.075 m、edge checker=0.9、n=3、max_iteration=100000、confidence=0.999、不估尺度；ICP Point-to-Plane、distance=0.075 m、100 iterations、relative fitness/RMSE=1e-6；缺法向量時才用 radius=0.15 m/max_nn=30。所有影格皆參與，GT 只在重建完成後評估，以原始首姿態和固定軸向對齊，不做最佳擬合。

地圖 down_voxel=0.05 m；既有 ceiling margin=1 m。Ontology 沒有 map voxel 欄位，本次只在宣告註解與獨立 config.before_run.json 揭露，未新增 RDF predicate。

Python 3.9.23、Open3D 0.18.0、NumPy 1.26.4、OpenCV 4.8.0.76、RDFLib 7.1.4、SciPy 1.13.1、Panel 1.4.5、Bokeh 3.4.3、Habitat-Lab 0.3.3。正式執行記錄的 Commit 為 `7fbe9042f3bdfff59a9188a05b4f02eb23ac1f0a`；其後只加入唯讀驗證工具與本紀錄，核心來源與執行時版本一致。

## Turtle、Seal 與來源驗證

- api.read_experiment 解析 Turtle 並通過 seal，complete=True、expected=measured=1522、pending=0、errors=[]。
- RawPointCount／VoxelizedPointYield 各 191 筆；六項 pair 因素各 190 筆。
- 前 20 幀正式因素共 154 筆，與新 Preflight 依官方 `_storable` 精度逐欄相符。
- 宣告 bytes 與執行前備份一致，SHA-256：`3306cd6f0729b45b9583edcf31772df314b18347487621dc1b2eec84c8e09ab5`。
- 封存後 Turtle SHA-256：`5ee9f6c35c61bfe5ccabb068bc4fb18fce54fbd4005465645e925ce5a2192bb6`；Explore／Dashboard 後仍一致。
- 原始 RGB-D、intrinsics、GT 的前後來源雜湊皆為 `22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`。
- 來源雜湊定義延用 M2_Preflight_Review.md，未修改原始資料或先前執行產物。

## 官方 Explore 與 Dashboard

```bash
pixi run --locked -e habitat python api.py explore \
  experiments/p1_baseline_20261118_map005_s0_01
pixi run --locked -e habitat python api.py explore \
  experiments/p1_baseline_20261118_map005_s0_01 --launch-dashboard
```

Explore 退出碼 0、耗時 7.197488 秒、峰值約 0.4755 GiB，產生 `plots/dashboard.html`、`timelines.html`、`distributions.html`、`tradeoff.html`。原始四份 HTML 約共 40 MiB，第一次輸出亦備份保留。

Dashboard 已實際在 localhost:63032 的瀏覽器檢視時間序列、分布與 FullBatch 的 (retained fraction=1, Mean L2≈3.174) 比較點。分布頁顯示單影格 n=191、pair n=190，均 0 missing／0 non-finite。驗證後已正常關閉本次伺服器；可保留／重開 HTML，不需常駐服務。

## 八項因素統計與待調查區間

| 因素 | n | 最小 | 最大 | 平均 |
| --- | --- | --- | --- | --- |
| RawPointCount | 191 | 177608 | 262144 | 249540.309 |
| VoxelizedPointYield | 191 | 4003 | 39638 | 19943.717 |
| CoarseRANSACFitness | 190 | 0.6228355 | 1 | 0.9227953 |
| CoarseRANSACRMSE (m) | 190 | 0.009524659 | 0.03834294 | 0.02693847 |
| CoarseRANSACCorrespondences | 190 | 3546 | 37479 | 18514.079 |
| ICPInlierFitness | 190 | 0.6189574 | 1 | 0.9236870 |
| ICPInlierRMSE (m) | 190 | 0.01022277 | 0.03109302 | 0.02087594 |
| ICPInlierCorrespondences | 190 | 3539 | 37642 | 18525.642 |

所有統計來源為正式 Turtle；完整逐筆 CSV 與 JSON 已保存。未使用統計值制定 Pass/Fail 或選取影格。

實際觀察：

- RawPointCount 在 49–55、71–133 有成段降低與波動，另有零星後段變化；最低為第 114 張 177608 點。
- 第 104 張 pair 的 ICP RMSE 最大 0.03109302 m；第 105 張 RANSAC RMSE 最大 0.03834294 m。
- 第 116 張 Voxel 點數最大 39638；第 148 張最少 4003。點數高低不能單獨當成品質分級。
- 第 147／148 張兩種 Fitness 都為 1，但 Voxel 點數僅 5626／4003；之後第 151 張 RANSAC／ICP Fitness 降到 0.6228355／0.6189574。這個區間值得檢視幾何支撐，不直接宣稱原因。
- 執行時有兩次「mutual filter 對應太少，回退到原候選對應」警告，分別列出 762／930；CLI 未提供其精確 frame ID，故不擅自指定。原始警告已保存。
- 全批次 286 秒超過前段外推的約 138–153 秒。程序持續使用 CPU、記憶體與 swap 穩定，未當作卡住或隱藏失敗；後段配準難度與收斂成本需進一步調查。
- 官方圖片中紅黑軌跡後段明顯分離，符合全批次 Mean L2 3.174 m 的品質問題。前段小誤差不能代表完整路線。

## 圖片與可重現限制

正式圖片：`experiments/p1_baseline_20261118_map005_s0_01/reconstruction_baseline.png`，亦有 reconstruction.png。已實際檢視紅黑軌跡及地圖。

本機使用既有 Matplotlib fallback；教師 helper 顯示時只抽樣約 5000 個地圖點，圖片因此較稀疏，不等於實際整合只含 5000 點。由正式 VoxelizedPointYield 求和可推得逐幀地圖合併前共 3,809,250 點；這是依程式路徑與因素推得的數量，**不是 CLI 輸出的裁天花板後點數**。

原 CLI 未保存 PLY、逐幀預測位姿或 ICP 矩陣，本次未為此擴大修改。因而不能以逐幀軌跡誤差精確定位漂移起點；也不能只靠稀疏單張圖片宣稱主要房間／角落已充分覆蓋。正式功能與證據已保存，場景品質及覆蓋仍需人工審視。

## M3 候選方向（未執行）

1. **資料品質區間診斷**：先檢視 49–55、71–133 與 104–116 的 RGB-D、點數與誤差聯動，區分缺深度、雜訊與幾何結構；再討論是否採 SPARQL 介入，不先選門檻。
2. **幾何支撐與配準穩定性**：檢視 147–151 的低點數／高 Fitness／隨後下降現象，提出可驗證假說；若要調整 voxel 或配準設定，需另行核准並控制變因。
3. **漂移定位與全路線涵蓋**：討論是否在獨立診斷執行保存逐幀變換／位姿，以定位轉向或低支撐區間；不覆寫這次 Baseline，不以 GT 修正配準。

這些是依本次證據提出的討論方向，不是已證實因果或已選定策略。未執行 Query／Selected 或參數搜尋。

## 產物與 Git

- 官方 Workspace：`experiments/p1_baseline_20261118_map005_s0_01/`。
- 正式輔助紀錄：`research_outputs/m2_phase1_baseline_20261118_01/`，含執行前宣告／設定、console、時間／記憶體取樣、validation.json、factor_occurrences.csv、diagnostic_observations.json、來源驗證與 Explore 備份。
- 新 Preflight：`research_outputs/m2_20261118_mapvoxel_01/`；舊紀錄保持在 `research_outputs/m2_20261118_preflight_01/`，未覆寫。
- 上述產物均未加入 Git；只追蹤程式、測試與驗收紀錄。

| Commit | 訊息 |
| --- | --- |
| 32c1e7d | feat: expose optional map-only downsampling in reconstruction CLI |
| 7e08d9e | chore: record optional map voxel in preflight runs |
| 373b7cd | chore: record official command output time and peak memory |
| 7fbe904 | chore: guard official command memory without changing reconstruction |
| b8dbd78 | chore: verify sealed baseline factors and provenance read-only |
| 包含本紀錄的提交 | docs: record completed Phase 1 baseline and quality findings |

所有修改位於 main；snapshot/pre-implementation 維持 291209750bd8ecf84f337112c9b92307e6be192a，無 remote，無歷史覆寫。完成本紀錄提交後停止等待 M2 人工驗收與 M3 決策。
