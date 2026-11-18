# M3.2 Parameter Experiment：B0完成與紀錄工具異常停止紀錄

日期：2026-11-18（臺灣）。**整體未完成／不申請七組實驗驗收通過。** 核准的7次新正式重建中，只執行B0一次，完整處理191張；B1、B2、C1–C4均未啟動。B0的重建、官方因素、Seal與FullBatch Baseline Run有效，但重建後驗證工具寫入歷史比對JSON失敗，因此依使用者明定的停止條件停止。沒有重跑B0、調參、增加候選或以其他條件取代缺失結果。

## 1. 停止原因與權限

獨立B級工具 `scripts/m32_experiments.py finalize` 在建立 `historical_comparison.json` 時拋出：

```text
TypeError: Object of type bool_ is not JSON serializable
```

原因是 `np.max(...) <= tolerance` 的比較產生 `numpy.bool_`，經Python的 `and` 運算仍可能保留此型別，標準JSON編碼器拒絕序列化。寫入已開始，所以該JSON留下不完整的 `"matched":` 欄位。**此為新增紀錄工具的缺陷，不是RANSAC／ICP失敗，也不是與歷史數值不一致。** 初次合成／CLI／防覆寫測試沒有涵蓋此歷史比對序列化分支，這是本輪測試的缺漏。

官方Turtle、Seal、191個位姿、190對矩陣、1522因素與評估原值在此之前均已成功保存。失敗發生於Explore之前，因此**B0尚未執行官方Explore、四份互動HTML未產生、完整finalize未通過**；不將正式重建成功說成整個官方工作流程已完成。

使用者規定遇到實驗紀錄完整性異常須保留證據並停止。因此沒有因缺陷容易修正而自行續跑後六組。停止後只修正B級紀錄工具、補上合成測試與停止護欄，並在**另一個新目錄**唯讀核對B0已存在的證據；沒有重試正式CLI重建、沒有重新執行失敗的finalize或覆寫不完整JSON。

修正將歷史核對結果轉為原生Python `bool`，抽出可測試的 `historical_comparison()`；另新增 `suite_stopped.json` 護欄，準備下一條件時拒絕已停止的suite。修正沒有更動 `utils.py`、`reconstruct.py`、`api.py`、Ontology、資料或演算法引數。

## 2. 工具、測試與正式入口

實際工具提交先於正式實驗：`860e842`。當時完整測試 **178 passed in 5.35s**，新增15項涵蓋固定七條件、現有CLI參數傳遞、真實合成RGB-D的官方首次重建／封存／Baseline、同次return觀測、GT時序、因素一致性、防覆寫及來源雜湊檢查。

觀測以 `runpy.run_path(..., run_name='__main__')` 執行原 `reconstruct.py`，只用 `sys.setprofile` 讀取call／return事件。不替換原函式、不修改局部變數、矩陣或對應點；GT不傳入重建。完整位姿由本次ICP矩陣鏈計算並與本次191個返回相機中心核對；只有正式CLI的評估階段在重建返回後讀GT。

後續增加1項序列化／各類不一致檢查、1項停止護欄測試及3項離線數學測試。最終完整測試 **183 passed in 5.33s**，`git diff --check`通過。測試只使用合成capture，沒有額外一樓重建。

正式流程紀錄如下，工作目錄皆為專案根目錄：

```bash
OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/m32_experiments.py suite-prepare \
  --output research_outputs/m32_20261118_suite_01

OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/m32_experiments.py prepare \
  --suite research_outputs/m32_20261118_suite_01 --condition B0

OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/record_command.py \
  --output research_outputs/m32_p1_m32_20261118_b_v005_s0_01/command \
  --rss-limit-gib 3 -- \
  .pixi/envs/habitat/bin/python scripts/m32_experiments.py observe \
  --output research_outputs/m32_p1_m32_20261118_b_v005_s0_01

# 此步在JSON序列化失敗，保留traceback並停止；沒有重試。
OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/m32_experiments.py finalize \
  --output research_outputs/m32_p1_m32_20261118_b_v005_s0_01
```

prepare真正呼叫官方 `api.py declare`，再於首次重建前補上假說、預測、完整引數與preregistration SHA。observe的原生CLI argv為：

```bash
.pixi/envs/habitat/bin/python reconstruct.py \
  --experiment experiments/p1_m32_20261118_b_v005_s0_01 \
  --version open3d --voxel-size 0.05 --seed 0 --down-voxel 0.05 --no-vis
```

未封存首次重建自動保存因素、Seal與baseline，不需要 `--write`。沒有selection query或虛假Selected。停止後另以官方 `api.py query --query-file .../queries/audit.rq --format csv` 唯讀核對191張，stdout／stderr／argv保存於stopped audit目錄。其餘條件的declare、reconstruct、explore均未呼叫。

## 3. 七條件狀態與可提供的比較表

| 條件 | Registration voxel (m) | Seed | 完整191張Mean L2 (m) | 103→104 RANSAC旋轉誤差 (°) | ICP旋轉誤差 (°) | 狀態 |
|---|---:|---:|---:|---:|---:|---|
| B0／C的seed0 | 0.05 | 0 | **3.174055104788137** | 176.0745043 | 179.7781591 | 重建完成；後置紀錄工具失敗，停止 |
| B1 | 0.03 | 0 | 未執行 | 未執行 | 未執行 | 未建立workspace |
| B2 | 0.08 | 0 | 未執行 | 未執行 | 未執行 | 未建立workspace |
| C1 | 0.05 | 1 | 未執行 | 未執行 | 未執行 | 未建立workspace |
| C2 | 0.05 | 2 | 未執行 | 未執行 | 未執行 | 未建立workspace |
| C3 | 0.05 | 3 | 未執行 | 未執行 | 未執行 | 未建立workspace |
| C4 | 0.05 | 4 | 未執行 | 未執行 | 未執行 | 未建立workspace |

沒有完整B尺度敏感度結果；C只有共用的seed0，**不計算五seed平均、樣本標準差、中位數或範圍，也不選最佳seed**。未知值沒有填0或排除於核准條件清單之外。

## 4. B0歷史重現與局部幾何

停止後在獨立目錄重新計算核對證據，不重新配準：

| 核對項目 | 結果 |
|---|---|
| 歷史M2／B0完整Mean L2 | 均為3.174055104788137 m，差0.0 m |
| 歷史因素／B0因素 | 1522／1522逐筆按官方精度相同，0不一致 |
| M3.0相符診斷／B0完整4×4位姿 | 最大逐元素差0.0；歷史位姿是診斷重跑來源，非M2原本保存的位姿 |
| 正式重建呼叫 | 1次，191 frame events、190 pair events |
| 輸入／處理／評估 | 191／191／191，保留率100% |

| 103→104指標 | RANSAC | ICP |
|---|---:|---:|
| 局部旋轉誤差 (°) | 176.0745043127 | 179.7781591207 |
| 局部平移誤差 (m) | 1.3521388050 | 0.9469599292 |
| Fitness | 0.6562556911 | 0.8359133127 |
| Inlier RMSE (m) | 0.0337191332 | 0.0310930241 |
| Correspondences | 7207 | 9180 |

在全部190對中，RANSAC及ICP旋轉誤差>150°皆只有103→104，共各1次；>90°也各只有該對。全域最大L2仍於第160張為10.6976822192 m，末張L2為5.7959826609 m、全域旋轉誤差179.8296257254°。圖中仍見104開始的翻轉與後段誤差傳播，沒有新的尺度／seed改善證據。

本次pair begin標記可定位到103→104觸發mutual filter不足930對應、回退原匹配集合的警告；102→103也有不足762的回退。因此**回退本身不是嚴重錯配的充分條件**，不能僅因警告而改mutual filter或認定唯一原因。

## 5. B0資源、地圖與八因素

| 指標 | B0 |
|---|---:|
| 純reconstruct wall time，含相同觀測 | 293.751107208 s |
| 總子程序時間：啟動→正式CLI／觀測／驗證退出 | 305.895459083 s |
| 正式CLI觀測區間CPU user／system | 291.937289／2.855139 s |
| 程序峰值RSS | 926892032 bytes，0.863235474 GiB |
| 0.5秒取樣峰值RSS | 925548544 bytes，0.861984253 GiB |
| RSS護欄／退出碼 | 3 GiB，未觸發／0 |
| 裁天花板後正式地圖點數 | 2725240 |
| 研究目錄bytes：離線摘要寫入前 | 5204851（不含正式workspace及suite備份） |

總程序時間不含失敗的finalize、未執行的Explore或停止後離線審計。CPU為觀測工具量到的CLI區間，不含啟動前已用的CPU；return觀測內計時約1.2863s，不涵蓋全部profiler dispatch成本。與歷史單次執行不具嚴格背景負載／快取控制，不將時間增加當成演算法退化證據。

固定map down_voxel=0.05、build_cloud=True、ceiling margin=1，地圖座標範圍X=[−3.0263,10.3698]、Y=[−0.4843,1.8031]、Z=[−10.0926,4.7106] m。保存官方紅／黑軌跡圖與每19點取1點的地圖樣本，已視覺檢視。點數／範圍不是正確覆蓋率，沒有計算完整樓層覆蓋百分比。

RawPointCount與VoxelizedPointYield各191筆；CoarseRANSACFitness、CoarseRANSACRMSE、CoarseRANSACCorrespondences、ICPInlierFitness、ICPInlierRMSE、ICPInlierCorrespondences各190筆。全部實際取自這一次Open3D Pipeline；完整序列及分布摘要存於 `factor_occurrences.csv`、`factor_summary.json`，不以歷史因素冒充新量測。

環境與所有演算法引數見preregistration，與M2固定設定一致：Open3D0.18.0、Point-to-Plane、OMP_NUM_THREADS=1；v=0.05使normal radius0.10、FPFH0.25、RANSAC與ICP距離0.075 m；max_nn30／100、mutual=True、edge0.9、n3、RANSAC100000／0.999、ICP100／1e-6／1e-6。候選值沒有改變。

## 6. Turtle與既有成果保全

| 證據 | 狀態 |
|---|---|
| B0 Turtle語法、Seal與Declaration bytes | 合法、驗證通過、宣告bytes未變 |
| B0因素完整性 | complete=True，expected=measured=1522、pending=0、errors=[] |
| B0 Run | 唯一FullBatch baseline、runFrameCount=191、mapMeanL2=3.174055（官方儲存精度），沒有Selected |
| B0 declarationDigest | `845f15146304e86b9ab26a884072eaa79b12c1d96544239f540273b9029088ec` |
| 原始RGB-D／GT／內參整體來源SHA | `22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`，與M2相同 |
| 舊成果、核心、資料及前置紀錄 | B0的566個受保護檔案SHA皆未變 |
| 原M2／M3.1 workspace | TTL、Seal、原baseline及selected子圖／結果、圖表完整保留；完整workspace另有備份 |
| 原baseline／selected | 191張／3.174055、190張／4.200398（Turtle儲存值），均未覆寫 |
| 新Experiment的官方Explore | 未執行；不宣稱完整官方工作流程通過 |

## 7. 產物位置與已檢視圖表

| 專案根目錄下路徑 | 內容 |
|---|---|
| `research_outputs/m32_20261118_suite_01/` | 七條件事前登記、版本／核心SHA、舊成果SHA、原workspace完整備份、`suite_stopped.json` |
| `experiments/p1_m32_20261118_b_v005_s0_01/` | B0官方Turtle、兩張重建圖、唯讀查詢；plots目錄尚無Explore輸出 |
| `research_outputs/m32_p1_m32_20261118_b_v005_s0_01/` | preregistration、原宣告、官方declare紀錄、實際argv、command／RSS、同次observation、因素CSV／summary、失敗traceback與原不完整JSON |
| `.../observation/camera_poses.npy`、`positions.npy` | 同次191個4×4位姿與相機中心 |
| `.../observation/transforms.jsonl`、`events.jsonl` | 190對RANSAC／ICP矩陣、191個單幀事件及190個配對因素事件 |
| `research_outputs/m32_20261118_stopped_audit_01/` | 獨立歷史核對、來源／停止證據、官方query stdout／stderr與argv；未回寫原失敗檔 |
| `.../analysis/frames.csv`、`pairs.csv`、`poses_offline.npz` | B0完整逐幀L2／姿態誤差、逐對粗／細誤差與固定首姿態GT評估 |
| `.../analysis/frame_and_pair_errors.png` | 已檢視：逐幀L2、全域旋轉、局部旋轉；底圖藍線ICP、橘線RANSAC |
| `.../analysis/summary.json`、`manifest.json` | B0離線摘要與審計產物SHA，full_workflow_complete=False |

上表前兩個`.../observation/`均位於B0研究目錄；後續`.../analysis/`均位於stopped audit目錄。已檢視新官方 `reconstruction_baseline.png`，看到與歷史相同的漂移。尚無完整B／C比較圖；未用B0一組複製成其他條件的假結果。

## 8. Git、下一步與停止點

- `860e842`：獨立正式參數實驗觀測工具與15項新增測試；**真正B0執行commit**。
- `737a681`：歷史比對JSON序列化修正、回歸測試與已停止suite護欄；未續跑正式重建。
- `57ca8b6`：重建後離線分析／停止審計工具、三項數學測試與B0唯讀SPARQL查詢。
- 本驗收／停止文件另以docs commit保存。所有大型產物維持忽略，只追蹤原始碼、測試、query及MD；main、無remote、不改歷史，snapshot/pre-implementation維持原SHA。

**目前資料不足以判斷尺度敏感度或seed穩定性，因此不能基於「全部實驗」推薦D或結束Phase 1。** B0支持歷史失敗可重現，但沒有新的介入結果。建議人工先驗收工具修正、停止證據與B0保全，明確核准後再安排剩餘6組並完成B0尚缺的Explore／後置驗證；不得重跑B0湊足新控制，也不自動解除停止標記。若後續繼續，需保留原失敗檔、明確記錄恢復授權與版本，先完成同次B0證據的非重建後置作業，再依原順序B1→B2→C1→C2→C3→C4，且仍不可擴充候選。

**本輪已依異常停止條件停止，未開始D、Phase 2、Bonus或英文報告。**
