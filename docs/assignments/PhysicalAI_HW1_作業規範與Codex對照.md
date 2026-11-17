# Physical AI HW1：正式作業規範與 Codex 架構分析對照

> 本文件用途：供 Codex 先理解正式作業規範，再和既有原始碼分析進行差異盤點。**目前僅用於規格對齊，不授權修改程式、執行實驗或撰寫正式報告。**
>
> 規範來源：`HW1_3D Scene Reconstruction.pdf`（13 頁；正式作業說明）。架構現況來源：`physical_ai_hw1_architecture_analysis.md`（Codex 依本機原始碼做的唯讀分析）。若兩者衝突，先以正式 PDF 的作業要求為準，並標記差異；不得自行臆測老師沒有明定的實作細節。

## 0. 已確認的本機環境（驗證紀錄，不代表重建完成）

- 專案根目錄：`/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1`；此資料夾獨立於原 GitHub Repository，無 Git Remote，僅保留 HW1。
- Pixi 0.84.2；Habitat-Sim / Habitat-Lab 0.3.3；Open3D 0.18.0；RDFLib 7.1.4；OpenCV 4.8.0；NumPy 1.26.4；Bullet 支援 True。為修復舊版 gym 建置，已於 Pixi habitat feature 補入 setuptools 與 wheel，並更新本機 `pixi.toml` / `pixi.lock`。
- `pixi run -e habitat smoke` 已通過；二樓模擬器已可互動擷取 2 組 RGB、Depth 及 GT pose，並生成 intrinsics；Codex 能呼叫 Pixi 及讀取兩階段資料。
- `replica_v1/apartment_0/` 為 3D 場景資產（約 7.5 GB）；`eval/_data/first_floor/` 為老師提供的一樓資料；`eval/_data/second_floor/env_test/` 為環境測試資料。
- 磁碟可用空間先前約 19 GiB，正式實驗前應再檢查；此為操作風險，不是老師規定的容量門檻。

## 1. 作業目標與兩階段（PDF pp.1–2、8–10）

- 從 RGB-D（彩色＋深度）影像重建 Replica `apartment_0` 的 3D 場景，估計相機軌跡，對照 Ground Truth 評估重建品質。
- Phase 1：**使用課程提供的一樓資料**（含設計過的資料品質變化）；先用完整批次執行首次重建與指標量測，再依量測證據提出至少一項改善／探究策略，重新重建並比較。
- Phase 2：**自行在二樓模擬環境中操作、擷取 RGB-D 與相機姿態**；需記錄 capture path、route、frame count。接著使用與 Phase 1 相同的重建、資料驗證、介入與比較工作流程。
- 比較兩階段的重建結果，討論資料品質因素與擷取決策對結果的關係。
- PDF 中一樓 152、二樓 213 的數字是**參考圖中的資料量**，不是明文規定每個人必須擷取的固定影格數。

## 2. 必須完成的重建核心（PDF pp.2–4、10）

1. **Depth Unprojection**：依每個 capture 的 `intrinsics.json`（解析度、FOV、depth scale 等實際可用欄位）與有效深度像素，使用針孔相機模型自行實作 2D→3D 反投影。**不得直接使用 Open3D 內建投影函式完成這一步。** 注意原始深度單位與公尺轉換只能做一次。
2. **Voxel Downsampling**：降採樣以兼顧效率與幾何結構；必要的 normals、FPFH 特徵估計。可用 Open3D。
3. **Global Registration（RANSAC）**：利用幾何特徵求得不同視角點雲的粗略變換。可用 Open3D。
4. **Local Registration（ICP）**：以粗配準為初始化，再精細調整。PDF 第 2 頁一般說明允許 point-to-point 或 point-to-plane；**第 10 頁的評分規準明確要求標準作業使用 Open3D Point-to-Plane ICP**，因此正式必做後端以後者為準。
5. **Scene Map + Trajectory**：將逐影格配準轉換正確組合到以首影格為參考的共同座標系，整合點雲並估計相機軌跡。必要時移除天花板，以**紅線呈現估計軌跡、黑線呈現真實軌跡**。
6. **Evaluation**：GT 姿態**只作為評估用途，不得拿來當作重建／配準輸入**。將 GT 轉換到與估計軌跡相同的首影格參考系，計算相機中心的平均歐氏距離：`MeanL2 = (1/N) Σ ||p_est_i - p_GT_i||₂`。值越低代表位置一致性越高。並檢視地圖涵蓋主要房間、連通空間與角落的完整性。

注意：PDF 沒要求一定做 TSDF／網格表面重建；作業文字描述的是配準後點雲整合成場景圖。若想額外輸出 PLY，須區分為輔助產物，不應誤當正式必備項目。

## 3. Data Verification 必須具備的實驗流程（PDF pp.4–8、10–11）

1. **Declare**：為一組 capture 宣告實驗與重建設定；此階段**不先設定品質判定閾值、不先將影格分成 Pass/Fail**。
2. **First-pass reconstruction**：完整批次首次重建，邊運算邊量測八個因素。
3. **Factor recording**：保存逐影格或相鄰深度影格配對的原始因素量測（不改寫原始證據）。
4. **Inspection**：透過統計表、時間序列、分布圖及因素間關係分析異常與重建表現。
5. **Intervention + reconstruction**：根據量測證據提出有理由的介入（可用 SPARQL 選取／排除影格，亦可調整資料使用方式或重建設定），重新執行並量化比較；**資料篩選不是唯一合法的介入方式**。
6. **Reporting**：保存實驗宣告、量測紀錄、介入與重建結果，能解釋不同重建執行的差異。

### 指定的八項因素

| 類別 | 名稱 | 意義 |
| --- | --- | --- |
| 單張 Depth | `RawPointCount` | 反投影後的有效點數（Voxel 前） |
| 單張 Depth | `VoxelizedPointYield` | Voxel 後的剩餘點數（不是比例） |
| 相鄰 Depth Pair | `CoarseRANSACFitness` | RANSAC 內點比例 |
| 相鄰 Depth Pair | `CoarseRANSACRMSE` | RANSAC 內點對應的 RMSE |
| 相鄰 Depth Pair | `CoarseRANSACCorrespondences` | RANSAC 保留的對應點數 |
| 相鄰 Depth Pair | `ICPInlierFitness` | ICP 內點比例 |
| 相鄰 Depth Pair | `ICPInlierRMSE` | ICP 內點對應的 RMSE |
| 相鄰 Depth Pair | `ICPInlierCorrespondences` | ICP 保留的對應點數 |

- 以 RDF/Turtle 與 Ontology 記錄實驗及對應關係；使用 SPARQL 分析或選取影格。
- 正式評分會檢查有效 Turtle：完整 declaration、**sealed machine section**、全部應有的 factor occurrences，以及 baseline、selected 重建 run 紀錄。無效語法、封存毀損、量測缺漏、run 紀錄缺漏都會扣分。
- 依現有程式骨架，若完整批次有 N 張有效影格，預期 factor occurrences 為 `2N + 6(N−1) = 8N−6`；此為程式架構推算，須配合實際成功處理資料確認，不是 PDF 明示的固定張數配分。
- PDF 第 7–8 頁的 SPARQL 僅為**範例**，`FILTER NOT EXISTS` 的邏輯要照實際查詢結果確認，不能直接把示例門檻當作正式評分規定或預設最佳值。

## 4. 評分規準（PDF pp.10–11）

正式要求同時考察：

- **Data Integrity**：Turtle declaration、sealed machine section、八項量測的完整 occurrence 與 baseline/selected runs。
- **Code Implementation**：全部必做 TODO、正確反投影、voxel/normals/FPFH、Open3D point-to-plane ICP、逐影格流程、相機姿態累積、Mean L2、紅/黑軌跡。
- **Reconstruction Quality**：軌跡 Mean L2 越低越好，且地圖須有足夠的目標樓層覆蓋範圍與完整性。
- **Reproducibility**：老師可能用自動化測試驗證；不要為報告好看而破壞既有程式介面與實驗資料的可重現性。
- **Report Quality**：方法、指標、分析與圖表有可追溯的實驗證據。

## 5. 英文 PDF 報告內容（PDF pp.11–12）

**格式：精簡、英文、PDF。** 至少包含：

### Implementation
- Reconstruction Pipeline：說明主要步驟的實作方式、使用設定與參數、遭遇問題／解法／理由。
- Data Verification：報告八項因素的量測、量測設定及**來源連結（source links）**；辨識失敗案例，連結量測證據與地圖瑕疵／配準失敗；解釋資料前處理或重建調整。

### Results and Discussion
- Phase 1 與 Phase 2 重建結果及比較。
- 一樓／二樓重建截圖；需要時移除天花板，估計軌跡**紅色**、GT **黑色**。
- 產生的 verification plots 截圖。
- 重建 run 比較表：**Mean L2 Distance、Frame Count、Total Execution Time、Tested Hyperparameters**。適當記錄 evaluated frames 與 retained-frame fraction（PDF 第 7 頁亦要求報告）。
- 說明如何使用指標規律、選取條件／SPARQL 或其他介入策略改善重建，並呈現調整前後比較；結合量測證據比較兩階段。

### Questions（須逐題回答）
1. What happens if ICP is performed without global registration (RANSAC)? Why?
2. Describe the choices used to improve ICP stability, such as voxel size, correspondence thresholds, or robust losses.
3. How do the observed data-quality factors and collection choices relate to reconstruction performance and Mean L2 Distance?

報告中的所有實驗數值、截圖、時間與改善結論都必須來自實際執行結果，不得虛構。

## 6. Bonus Track（PDF pp.10–11）

- 選做：實作 `my_local_icp_algorithm`，包含最近鄰對應點搜尋與剛體變換估計。
- 比較自己 ICP 與 Open3D ICP 的場景重建結果、執行時間，討論效能／準確度、搜尋、穩健權重、門檻與收斂等。
- 加分實作**不能取代**必做 Open3D ICP。
- Codex 發現 `my_local_icp_algorithm` 的 docstring 說 Point-to-Point＋Kabsch SVD，而 TODO 說 Point-to-Plane 線性化更新。**正式 PDF 沒明定 Bonus 的特定形式**，故標記為待討論，不先替使用者決定。

## 7. 繳交規定（PDF p.12）

檔名：`<student-id>_hw1.zip`，ZIP 根目錄直接為以下內容，**不可以再包一層資料夾**：

```text
<student-id>_hw1.zip
├── load.py
├── reconstruct.py
├── utils.py
├── api.py
├── ontology/
│   └── hw1.ttl
├── report.pdf
└── README.md
```

- 包含必要的重建與資料驗證程式原始碼；如有 Bonus，應在提交程式中保留 `my_local_icp_algorithm` 並於 README 註明。
- **不要打包**實驗 Turtle 檔、生成診斷圖表、Phase 2 擷取資料、Replica 場景資產、無關建置產物。
- 繳交截止時間與遲交扣分由所屬學校公告；PDF 未給單一通用日期。
- 作品須原創；未經授權複製他人程式或報告內容禁止。

## 8. Codex 架構分析的重要實作警示（**以下源於原始碼分析，而非 PDF 正式規定**）

1. `utils.py` 集中了主要 TODO，正式作業的各個必備環節仍未完成；`reconstruct.py` 主要是 CLI 與流程協調器。
2. `api.py declare` 會產生 prediction／label 文字 TODO，屬每個實驗的敘述欄位，不等於未完成的演算法函式。
3. 影格選取的跨缺口情況，依現有實作仍可能將距離很遠的前後兩張選取影格作配準；這會影響介入設計。
4. 若重建 selected run 要留在 Turtle，Codex 分析指出可能需明確指定 `--override-experiment`／`--write`，不能假設預設一定寫入。修改前應查對原始碼、避免破壞封存資料。
5. `--no-write` 可能仍輸出 PNG，`--no-vis` 仍可能進行點雲整合；不能把它們視為全面唯讀／零產物。
6. Phase 2 YAML 的 `clear_existing: true` 可能**刪除整個指定的輸出根目錄**。正式擷取前必須明確隔離 output-root、保護 `env_test` 與其他已完成資料。
7. YAML `--clean` 不保證完全無深度雜訊；須依 source code 與設定核對。
8. 自製 ICP 的資料回呼結構可能缺少 fitness/RMSE/correspondence；若要比較，應先確認對八項因素完整性的影響。
9. 現有 `pixi.toml` 的部分測試任務可能指向缺少的檔案；不要把無法執行的內建測試誤認為演算法錯誤。
10. Codex 架構分析的來源連結是使用者本機絕對路徑；應在 Codex 專案中重新確認對應檔案及行號，不應以分析報告代替原始碼。

## 9. 目前不得提前決定的事項

- 何種資料介入策略、參數網格、影格門檻、Phase 2 正式拍攝路線或組數，**尚待使用者閱讀專案後共同決定**。
- 是否執行 Bonus ICP、Bonus 的實作形式，尚未決定。
- 不應先自動修改現有程式、設定、資料集或開始正式重建；先完成「正式 PDF × 現有程式」的要求追蹤與風險盤點。

## 10. 建議交付給 Codex 的下一個唯讀任務

1. 讀取 `HW1_3D Scene Reconstruction.pdf` 全文及此規範摘要，並對照既有架構分析與本機原始碼；確認每項正式要求都有可追溯的對應來源（PDF 頁碼、程式檔案／函式／行號）。
2. 產出「必做／選做／報告／繳交」需求追蹤矩陣，各項標記：已實作、部分實作、待實作、待釐清。
3. 列出與作業規定相衝突的地方、程式註解互相矛盾的地方、可能損毀既有資料或封存紀錄的危險操作。
4. 給出可選的實作順序與驗收條件，但**不要先替使用者選定實驗設計**。
5. 全程唯讀、不要修改任何檔案，也不要執行會寫入資料的命令。
