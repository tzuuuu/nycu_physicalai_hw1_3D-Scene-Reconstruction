# M2.0 真實資料前置驗證與 M2.1 停止紀錄

## 結論

M2.0 的 5、10、20 張功能測試均完成，未遇配準例外或漏幀；20 張已涵蓋約 2.5 m 平移，紅黑軌跡接近，未見明顯轉換方向錯誤。但正式全批次的資源安全尚未通過，依使用者停止條件停在 M2.0，**M2.1 未啟動、未建立正式 Declaration／Turtle、未封存 Baseline、未建立 Selected**。

這是資源風險的預防性停止，並非宣稱已發生 OOM，也不是以 Preflight 取代正式 Baseline。

## 新增官方規範核對

已重新閱讀完整交接 MD、新增「官方實驗工作流程與最終繳交驗收」、正式 PDF §3.2.1～3.2.4（pp.6–8）、Submission（p.12）、需求追蹤矩陣與 M1_Acceptance.md。

| 要求 | 核對結果 |
| --- | --- |
| Declare → First-Pass → Explore | 新增規範與 PDF 一致；正式 M2 使用原有 api.py/reconstruct.py，不以獨立工具代替 |
| 宣告預測與設定 | 必須在正式重建前填寫；可揭露已知 Preflight 觀察，但不能事後倒填正式結果 |
| 八項因素、Seal、Baseline Run | M2.1 必須實際驗出；本次未建立，狀態為未執行 |
| Query → Selected | 官方流程必要，依授權於 M3 才執行；本次不做 SPARQL 篩選 |
| Selected 首影格／寫入選項 | 保留使用者已核准的首影格限制；現有 --write/--override-experiment 才更新 sealed run，PDF 範例不能當作已寫入證據 |
| ZIP 根目錄、英文 PDF、排除生成產物 | 與 PDF 一致；全部必要相依來源如何打包仍需 M6 向課程確認，非 M2 阻擋因素 |

新增內容已成為正式交接規範並獨立 Commit 保存；無流程衝突。實際阻擋為目前完整地圖的資源安全。

## 原始資料完整性

- 來源：`eval/_data/first_floor/`，191 張 RGB、191 張 Depth、GT shape=(191,7)，數字檔名一一配對，全部可讀，尺寸均正確，GT 數值有限。
- 內參：width=512、height=512、hfov=90°；JSON 沒有 depth_scale。
- 深度全部為 uint16 PNG；依既有 DEPTH_SCALE 與擷取器毫米編碼，在讀檔時除以 1000 一次。未修改相機 JSON 或原始深度。
- 四元數長度範圍約 0.99999994～1，未改寫原始 GT。
- 全部有效深度點數：47,662,199。完整因素預期 8×191−6=1,522 筆；這是需求數量，**本次未量測完整批次因素**。
- 資料雜湊（按數字順序加入 RGB/Depth 相對路徑與檔案內容，再加入 intrinsics.json／GT_pose.npy 檔名及內容）：`22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`。Preflight 前後一致。

## 實際執行指令與設定

```bash
pixi run --locked -e habitat python scripts/m2_preflight.py \
  --data-root eval/_data/first_floor \
  --output research_outputs/m2_20261118_preflight_01/frames_05 --frames 5
# 接著使用不同輸出目錄 frames_10／frames_20，僅將 --frames 改為 10／20。
```

- 正式演算法：手寫 Pinhole → Open3D Voxel／Normals／FPFH → RANSAC → Open3D Point-to-Plane ICP。
- 固定 voxel_size=0.05 m，seed=0，build_cloud=True，down_voxel=None，未搜尋或改變任何演算法參數。
- Normals radius=0.1 m、max_nn=30；FPFH radius=0.25 m、max_nn=100。
- RANSAC：mutual_filter=True、distance=0.075 m、邊長 checker=0.9、距離 checker=0.075 m、ransac_n=3、max_iteration=100000、confidence=0.999；剛體 estimator 不估尺度。
- ICP：Point-to-Plane、distance=0.075 m、max_iteration=100、relative_fitness=relative_rmse=1e-6；沿用前處理法向量，缺少時才估計 radius=0.15 m、max_nn=30。
- 地圖使用全解析度有效原始點；最後沿用教師 remove_ceiling_points，margin=1 m。未額外儲存大型 PLY。
- 每次測試皆從原始第 1 張開始，分別連續使用 1–5、1–10、1–20，不是正式 Selected。
- 重建完成後才讀取 GT 評估，固定首姿態及軸向換算，不做最佳擬合。
- 執行程式版本：`0fb8942f45ca8d860f4e0cf7eb3bdb2d03bd2f9e`；演算法與 M1 最終版本完全一致。
- Python 3.9.23、Open3D 0.18.0、NumPy 1.26.4、OpenCV 4.8.0.76、RDFLib 7.1.4、SciPy 1.13.1、Panel 1.4.5、Bokeh 3.4.3、Habitat-Lab 0.3.3。

計時從 Preflight 開始重建前至評估與 PNG 完成；不含 Python／套件啟動及最後摘要寫檔。程序記憶體採 macOS getrusage.ru_maxrss 的高水位，非系統總用量，也非逐時點的即時 RSS。

## Preflight 結果

| 使用影格 | 完成／評估數 | 原始批次使用比例 | Mean L2 (m) | 重建秒數 | 含評估／PNG秒數 | 程序峰值 GiB | 裁切後地圖點數 | 因素數 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1–5 | 5／5 | 2.62% | 0.00316570 | 4.1406 | 15.1893 | 0.4671 | 666,223 | 34 |
| 1–10 | 10／10 | 5.24% | 0.00513626 | 8.2769 | 18.0825 | 0.7684 | 1,335,522 | 74 |
| 1–20 | 20／20 | 10.47% | 0.00698689 | 15.0951 | 24.7106 | 0.9268 | 2,672,499 | 154 |

每組預期影格均完成，無刪幀、無失敗值代填。不同規模的 Mean L2 涵蓋不同相機位置，不能作為改善策略排名。

前 5 張 GT 中心未平移；前 20 張 GT 最大位移約 2.5000 m，估計最大位移約 2.4927 m，逐幀 L2 最大約 0.01004 m。這支持目前前段的方向／單位處理，但不代表全樓層、長軌跡或失敗區間都已驗證。

## 八項因素：僅前 20 張

| 因素 | 數量 | 最小值 | 最大值 | 平均值 |
| --- | --- | --- | --- | --- |
| RawPointCount | 20 | 262141 | 262144 | 262143.85 |
| VoxelizedPointYield | 20 | 6506 | 17287 | 13893.25 |
| CoarseRANSACFitness | 19 | 0.740158 | 0.999325 | 0.940457 |
| CoarseRANSACRMSE (m) | 19 | 0.0211524 | 0.0352057 | 0.0261741 |
| CoarseRANSACCorrespondences | 19 | 6288 | 16310 | 13178.58 |
| ICPInlierFitness | 19 | 0.733643 | 0.999422 | 0.939131 |
| ICPInlierRMSE (m) | 19 | 0.0166855 | 0.0229978 | 0.0202657 |
| ICPInlierCorrespondences | 19 | 6307 | 16311 | 13157.95 |

因素直接取自正式 M1 Pipeline 的點數及 RegistrationResult；藉既有 api.make_pipeline_measurement_callback 收集，僅寫輔助 JSONL，未建立 Turtle。

值得追蹤的區間：1→2 的 Fitness 最低；10→11 的 RANSAC RMSE 最高；8→9 的 ICP RMSE 最高；約 12–20 張 Voxel 點數及對應數逐步下降，17→18 的 Fitness 亦下降。這些是本次前段的描述性觀察，不設 Pass/Fail、不決定門檻，也不能推論完整批次的異常分布或原因。

## 資源安全門與停止理由

- 本機實體 RAM：16 GiB；量測後系統 memory_pressure 報 free percentage 43%，swap 已用約 4088.94 MiB。該百分比不是可保證配置給單一程序的可用 RAM。
- 初始磁碟剩餘約 11.60 GiB；目前未證實磁碟直接不足，主要風險是記憶體峰值及額外 swap。未刪除或清理任何既有資料。
- 全批次有效原始點的座標＋色彩最低為 2.1307 GiB；尚不含容器容量、合併重配置、裁天花板時的副本／索引、每幀中間資料及輸出圖像。
- 外推方法：每次 `(程序峰值−啟動後當時高水位)/本次原始有效點數`，乘完整批次原始有效點數，再加回該次啟動高水位。5／10／20 張分別外推 9.995／10.566／6.838 GiB。
- 此外推只提供風險範圍，不是實測完整批次，配置器、重配置、裁切比例及場景差異都可能改變尺度。不能據此宣稱一定 OOM，也不能據此保證安全。
- 重建時間線性外推約 144–158 秒，另加評估／圖片時間；後段配準難度與記憶體壓力可能使其增加，不宣稱固定時限。
- `reconstruct.py` 正式入口固定 build_cloud=True，而且沒有傳入既有 down_voxel 的 CLI 選項；`--no-vis` 不會省去原始點地圖。沒有在本機證明全批次可安全執行前，不冒險啟動 M2.1。

## 需要使用者決策的最小提案（尚未實作）

建議讓正式 CLI 明確支援現有的「僅地圖降採樣」，保留完整 191 張影格、全部八項因素及配準設定：

1. 在 reconstruct.py argparse 加入可選 `--down-voxel`，預設 None，正有限值檢查。
2. 將 `args.down_voxel` 傳給 baseline 與 sealed run 的兩個 utils.reconstruct 呼叫；不改 API、Ontology、因素計算或封存邏輯。
3. 首次候選使用與既定前處理相同的 0.05 m，**不是參數最佳化，也不改 registration voxel**。utils 既有 down_voxel 只作用於地圖副本，不作用於位姿、配準或因素。尚未測試這個候選，本次不提供降低峰值的保證數字。
4. 核准後先重做新的獨立 5／10／20 Preflight，比對原參數下軌跡／因素是否一致、地圖涵蓋及峰值，再決定完整官方 Baseline 是否安全。宣告與輔助參數紀錄必須揭露 map voxel。

具體呼叫位置為 reconstruct.py 的 baseline 與 sealed `utils.reconstruct(...)`；所需改動等價於新增 `down_voxel=args.down_voxel`。正式入口預計仍為：

```bash
pixi run --locked -e habitat python reconstruct.py \
  --experiment experiments/<new-name> --no-vis --voxel-size 0.05 --seed 0 \
  --down-voxel 0.05
```

此旗標目前不存在，不能直接執行。這會修改老師已完成的 CLI，依交接規範三級 C 權限必須先取得使用者明確批准；本次未修改。替代方案是在記憶體餘裕更大的環境使用原 CLI，重新核對平台與 Preflight，不需修改 CLI。

## 證據位置與 Git

產物集中於 `research_outputs/m2_20261118_preflight_01/`，已被忽略且未提交：

- inventory.json、input_integrity_after.json：來源完整性與前後雜湊。
- frames_05／frames_10／frames_20：各次 summary.json、events.jsonl、transforms.jsonl、positions.npy、reconstruction.png；外層另有 console.log。
- preflight_analysis.json、resource_assessment.json、software_versions.json：彙整、估計與環境。
- preflight_factors.png：前 20 張八項時間序列，已檢視；這不是官方 Explore 圖表，也不替代正式驗收。

工具驗證：`pixi run --locked -e habitat python -m pytest tests/test_m2_preflight_tool.py -q` → 4 passed in 1.30s；彙整工具亦已對本次完整記錄執行並核對 34／74／154 筆因素，未生成 TTL。

| Commit | 用途 |
| --- | --- |
| 4fb92e6 | 保存使用者新增的官方流程／繳交交接規範 |
| 0fb8942 | 通過測試的 Preflight 紀錄工具，也是三次實測所記錄的程式版本 |
| 0d697b3 | 通過測試的資源彙整與圖表工具 |
| 包含本文件的提交 | M2.0 證據及停止提案紀錄 |

所有工作在 main，snapshot/pre-implementation 維持 2912097，未新增 remote。utils.py、api.py、reconstruct.py、Ontology、套件與原始資料均未修改；未提交大型資料或實驗產物。

## 正式 M2 尚未驗收項目與後續方向

正式 Baseline 的完整 191 幀 Mean L2、保留比例、1522 筆因素、全樓層場景覆蓋、Turtle 合法性、Seal、Baseline Run、官方 Explore 圖表／Dashboard **均未執行或未完成**。不得以本次 Preflight 代替。

尚無完整 Baseline 證據可決定 M3 改善策略。未來值得調查的方向只有候選：前段點數／對應數降低與視野幾何的關係、較高 RANSAC RMSE 與精配準結果的關係、長軌跡漂移及全樓層覆蓋。需完整 Baseline 後再提出參數或 SPARQL 選項；本次不選門檻、不執行介入。
