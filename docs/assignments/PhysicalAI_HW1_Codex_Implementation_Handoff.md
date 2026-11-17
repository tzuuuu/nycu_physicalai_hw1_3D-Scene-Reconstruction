# Physical AI HW1 — Codex 開發、實驗與報告交接規劃

> **狀態**：使用者已核准本文件所列的整體流程及實作原則；具體實驗參數、資料選取門檻、P2-C 路線須在相應驗收點依證據決定。  
> **用途**：交給 Codex Desktop 在本機依序執行；本文件不是一次性授權完成所有工作。  
> **專案根目錄**：`/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1`  
> **執行方式**：Codex Desktop **Local** 模式，直接開啟上述專案根目錄；不要切換 Cloud／Worktree 或另外 clone HW2。  
> **語言**：與使用者溝通、開發記錄、程式內新增邏輯註解使用**繁體中文（臺灣用語）**；最終作業 `report.pdf` 必須是**英文**。

---

## 0. 執行總原則與權威來源

### 0.1 先讀來源，再動手

開始任何修改前，Codex 必須**實際開啟並閱讀**：

1. `docs/assignments/HW1_3D Scene Reconstruction.pdf`：**最高優先級**，共 13 頁的正式作業說明。如果實際檔名不同，先在專案內定位並確認。
2. `docs/assignments/physical_ai_hw1_architecture_analysis.md`：原始碼架構盤點。
3. `docs/assignments/PhysicalAI_HW1_作業規範與Codex對照.md`：先前整理的 PDF 與程式差異。
4. `docs/assignments/貼上的 Markdown.md`：正式需求追蹤矩陣，若檔案確實存在；若檔名不同，以實際檔案為準。
5. 專案現有 `README.md`、`pixi.toml`、`pixi.lock`、`utils.py`、`reconstruct.py`、`api.py`、`load.py`、`plot.py`、`ontology/hw1.ttl`、`configs/second_floor.yaml`，以及相關模組。

**遇到衝突時：**正式 PDF 規範優先；再用原始碼判斷目前實際行為。摘要、架構文件與 TODO 註解可協助解讀，但**不可擅自取代或降低 PDF 的必要要求**。對於 PDF、原始碼與實際資料無法一致的地方，明列「事實／風險／可行方案」並請使用者決策；不可默默修改教師規範。

### 0.2 不可違反的規範

- **先完整符合老師的作業規範，再做延伸**。不為了降低 Mean L2、方便實作或自動化而省略必要流程。
- **Depth Unprojection 必須自行實作針孔相機反投影**，不可呼叫 Open3D 內建深度反投影／RGB-D 轉點雲函式來代替。可用 NumPy 計算，再建立 Open3D PointCloud。
- 正式 **Phase 1／Phase 2 均固定使用 RANSAC + Open3D Point-to-Plane ICP**；絕不可使用 Bonus 的自製 ICP 產出正式成果。
- Ground Truth (GT) 僅供**重建完成後的評估與結果分析**，不得當作配準初值、演算法輸入、補正軌跡或最佳化依據。
- 每次 capture 的首相機姿態為參考座標系；估計與 GT 必須在同一座標系計算指定的 Mean L2，**不得額外做最佳旋轉／平移／尺度擬合來掩飾誤差**。
- Data Verification 必須記錄**八項直接來自實際 Pipeline 的量測因子**；首輪保留完整批次資料並量測，不能預先將影格判定為好壞或虛構 Pass/Fail。
- 確實產生、驗證合法 Turtle 宣告、Sealed Machine Section、完整因素紀錄，以及正式 `baseline`／`selected` reconstruction runs。
- 不得虛構、代填、默默略過失敗的量測或影格；每次實驗須可重現，並能追溯到程式版本、資料、設定、時間與輸出。

### 0.3 已驗證的本機狀態（僅供起始參考，執行前再核對）

- Apple Silicon M4、macOS；Pixi `0.84.2`。
- Habitat-Sim／Habitat-Lab `0.3.3`；Open3D `0.18.0`；RDFLib `7.1.4`；OpenCV `4.8.0`；NumPy `1.26.4`。
- 既有 Habitat Pixi 環境已安裝，為修正舊版 `gym` 建置問題，`pixi.toml`／`pixi.lock` 已加入 `setuptools>=64,<70` 與 `wheel`；`pixi run -e habitat smoke` 曾成功。
- `replica_v1/apartment_0/` 已下載；`eval/_data/first_floor/` 已有老師提供的一樓 RGB-D、GT 與內參；`eval/_data/second_floor/env_test/` 是**兩張測試影格，非正式 Phase 2**。
- 二樓模擬器曾由使用者在本機成功互動擷取；一樓資料檔案與 Codex 的讀取能力已通過初步檢查。
- 曾有約 `19 GiB` 剩餘空間；這是歷史數值，**執行前重新量測**。不要任意重裝、升級套件或下載大型資產。
- Gym 停止維護、重複 plugin 警告未阻止先前 smoke test；沒有明確功能失敗時不要擅自升級核心依賴。

---

## 1. Codex 修改權限與原始程式保護

### 1.1 三級修改權限（已核准）

| 等級 | 範圍 | 權限 |
|---|---|---|
| **A — 必做 TODO** | 教師在 `utils.py` 等檔案明確標示的待實作部分 | **可以直接實作與測試**，但必須保留原始 TODO 指引與函式契約。 |
| **B — 獨立新增** | 非侵入式單元測試、測試資料、實驗追蹤腳本、分析程式、實驗紀錄樣板、報告產生工具 | **可以新增**，不得破壞既有執行入口、資料或自動評分行為。 |
| **C — 教師已完成核心** | 非 TODO 的既有核心實作、公開 API、CLI、Ontology、教師預設設定及相容行為 | **不能自行修改**。若必要，先說明原因、修改位置、影響、替代方法，並經使用者批准後再改。 |

若不修改等級 C 的程式就無法符合 PDF，**先停止該部分**，提出最小修改提案；可以繼續其他獨立且已授權的工作，但不能先改後報。

### 1.2 保留老師 TODO 的指定編碼格式

每一個教師原有 TODO 都要符合：

1. 原始英文 `# TODO:` 指引**逐字保留、保持原順序、留在原對應位置**；即使註解跨多行，也不可改寫、合併、移動或刪掉。
2. 在該 TODO 指引下方新增**簡短的繁體中文註解**，說明「這段要如何實作及原因」，不要逐行翻譯 Python 語法。
3. 緊接註解放入**該 TODO 對應的實際程式碼**。下一項 TODO 再按同樣方式處理，不要把所有實作集中在與 TODO 無關的位置。
4. 如果確實需要額外 helper，原始 TODO 下方仍要保留有意義的呼叫及說明，輔助函式也需有適當測試。
5. 完成後移除對應會阻斷流程的 `NotImplementedError`／占位用 `pass`，但**保留 TODO 原文作為教師要求與自身實作的對照**。
6. 最後驗收不能只用搜尋 `TODO` 字串當作未完成依據，而要核對每個 TODO 都有實作、測試與可追溯 Commit。

**格式示意（非實際算法實作）：**

```python
# TODO: Convert `rgb` and `depth_m` to NumPy-compatible arrays and
# validate that the depth shape agrees with `(height, width)`.
# 將輸入轉成 NumPy 陣列，確認深度影像尺寸與本次相機內參一致。
rgb = np.asarray(rgb)
depth_m = np.asarray(depth_m)
if depth_m.shape != (height, width):
    raise ValueError("Depth image size does not match intrinsics")

# TODO: Convert depth values to metres when the input representation
# requires it; follow the capture convention used by the caller and do
# not hardcode camera parameters from another capture.
# 依呼叫端資料契約確認深度單位，僅在必要時轉為公尺，避免重複換算。
# 實際換算應在查證本次 capture 的來源與呼叫契約後撰寫。
```

**注意**：上述只是排版範例。請先驗證真正原始碼中的 TODO 原文及當前型別，不能拿示意碼直接覆蓋正式函式。

### 1.3 程式品質與異常處理

- 使用一致且可讀的 Python 撰寫方式；不要為了簡化而取消輸入形狀檢查、單位檢查或必要紀錄。
- **程式錯誤**（陣列／矩陣方向、API 版本、型別、檔案讀取等）可依權限修復，並新增回歸測試。
- **實驗失敗**（配準差、軌跡漂移、空對應、低 Fitness、噪聲、範圍不足）是研究證據；保存失敗現象、原因假設與數值，**不得偷偷跳過、填假數據或無紀錄地調參**。
- 在無法計算指標時，清楚標示為未定義／失敗及原因；勿把 `NaN`、`0` 或缺對應點當作正常且完美的配準結果。
- 對專案與資料採取最小必要修改；不修改原始 capture 的 RGB、Depth、GT 或相機內參來讓分數變好。

---

## 2. Git：本機追蹤、原始版本保存與小步提交

### 2.1 Git 的最終結構（已決定）

- **只使用本機 Git Repository**，沒有 Git remote；不得擅自新增 `origin`、推送遠端，或重新 clone 包含 HW2 的完整專案。
- **`main` 是唯一持續開發與提交功能的分支**。
- 在任何作業 TODO 開始實作前建立並固定保留 **`snapshot/pre-implementation`** 分支，指向首次保存的「實作前」Commit；建立後不繼續提交到該分支。
- 專案目前的 `pixi.toml`／`pixi.lock` 已因環境建置補過依賴，首次快照應如實標記為**「本機環境已修正、但尚未實作 TODO」**，不可稱為逐 byte 與 GitHub 完全相同的原始版。

### 2.2 Git 初始化（Milestone M0）

Codex 依序執行（先檢查現況，勿無條件重建或覆寫）：

1. 確認目前位於 `physicalai_hw1`；檢查 `.git` 是否已存在、`git status`、remote、目前 `main`／其他分支。如已初始化，先彙整而非重做歷史。
2. 建立合理 `.gitignore`，至少排除：`.pixi/`、`replica_v1/`、`eval/_data/`、`experiments/` 的大型或生成紀錄、Python 快取／虛擬環境、測試快取、實驗生成 PNG／HTML／PLY 與 ZIP。**不可誤排** `ontology/hw1.ttl`、正式程式碼、測試程式碼、實驗分析腳本或未來的 `report.pdf`。
3. 檢視忽略規則與 `git status`，避免將大型 Replica、私人擷取資料、Pixi 環境納入 Git。對 `dependencies/habitat-lab/` 等第三方來源若有容量／可攜性疑慮，先列出大小、固定版本、保留或排除的影響，請使用者決定；**不得默默省略乾淨環境所需來源**。
4. 在 `main` 建立 `chore: snapshot pre-implementation HW1 source` Initial Commit。除 `.gitignore` 外，這個步驟不得修改作業程式內容；檢查 `git show --stat` 與狀態。
5. 使用 `git branch snapshot/pre-implementation` 保存該 Commit，確認目前仍位於 `main`；不必建立遠端、不要做 rebase／force-reset。
6. 回報 Initial Commit 的短 SHA、分支名稱、追蹤檔案概要與忽略規則。

**M0 停止點**：完成 Git 快照且通過驗收後，**停止等待使用者同意 M1**。不要同一輪自動開始填 TODO。

### 2.3 開發期間 Commit 規則

- **每完成且測試通過一項 TODO、函式或可獨立驗證的功能，就在 `main` 建立一筆小而有意義的 Commit**。例如 Depth Unprojection、Voxel/FPFH、RANSAC、Open3D ICP、Pose Compose、Mean L2、對應測試等。
- 某項 TODO 的程式及必要測試可在同一 Commit；不必把不能獨立執行的半成品硬拆。
- 每個 Commit 前檢查 `git diff --check`、相關測試結果、`git status` 和 staged diff；**不要直接無差別 `git add .`**。
- 避免同一 Commit 混入無關的程式、資料集或大量實驗輸出；不要在未授權下修改既有 Commit 歷史。
- 建議 Conventional Commits：`feat: implement depth unprojection`、`test: cover camera pose composition`、`fix: correct unit conversion`、`chore: add experiment log template`。
- **微型 Commit 不取代階段驗收**：一個大里程碑可以包含多個 Commit，但完成後仍必須提供驗收證據並等待使用者放行下個里程碑。

---

## 3. 正式作業必要實作清單（不可跳過）

| 模組 | PDF 依據 | 正式要求／驗收重點 |
|---|---|---|
| Depth Unprojection | pp.2–3、10 | 自行依針孔模型使用該批相機內參與深度單位計算 `(X,Y,Z)`；不得用 Open3D 投影函式代替。有效像素、顏色與尺寸正確。 |
| Point Cloud Preprocess | pp.2–3、10 | Voxel 下採樣、法向量、FPFH；可使用 Open3D。 |
| Global Registration | pp.2–3 | 使用 RANSAC 進行全域粗配準；特徵與轉換方向正確。 |
| Local Registration | pp.2–3、10 | 正式路徑使用 **Open3D Point-to-Plane ICP**，由 RANSAC 轉換初始化。 |
| Map & Trajectory | pp.2–4、10–11 | 正確組合逐影格相對位姿、整合點雲；重建圖及紅色 Estimated／黑色 GT 軌跡；需要時移除天花板。 |
| GT & Mean L2 | p.4、10 | GT 只評估，首影格共同座標系，計算相機中心 Mean L2；不以 GT 修正演算法。 |
| Data Verification | pp.4–5、7–8、10 | 先完整量測八項原始因素，再查看序列／分布、選介入策略，重建並比較。 |
| Experiment RDF/Turtle | pp.4、6–8、10 | 正確 declaration、完整 factor occurrences、sealed machine section、baseline/selected run 與可查詢圖表。 |
| Phase 1 | pp.2、8–9 | 老師提供的一樓完整批次 Baseline、分析、證據導向 Intervention、重新重建比較。 |
| Phase 2 | pp.2、9–10 | 自行收集二樓 RGB-D／poses、記錄 capture path/route/frame count，並執行相同驗證、介入、重建比較。 |
| Quality & Report | pp.10–12 | 同時評估 Mean L2 和地圖覆蓋；英文 PDF、完整比較表、驗證圖、三題指定問答。 |

### 3.1 反投影與相機內參的重要衝突

官方 PDF 寫明需要依 `intrinsics.json` 的解析度、FOV 與 depth scale 反投影；但 Codex 在本機分析到兩批 JSON **目前僅有 `width`、`height`、`hfov`，沒有 depth scale 欄位**。因此：

1. 先用**資料建立端、現有函式契約、實際 `uint16` PNG 編碼與獨立檢查**確認原始深度單位、像素是否為毫米、呼叫端是否已轉成公尺。
2. 深度只能轉換為公尺**一次**；不能同時在呼叫端與反投影內又除一次 `1000`，也不能依別的 capture 硬編相機參數。
3. 針對缺少明示 scale 的來源，用**有證據且可追溯的相容處理**；不要假稱 JSON 已含欄位，也不要為了通過測試偷偷改寫教師提供的資料。若需要動到等級 C 原有行為，先取得批准。
4. 避免混淆相機座標系（圖像 x 右、y 下、z 前）與 Habitat 世界／GT；確認相對 transform 的 source→target 方向及相機中心累積順序。GT 對齊不得自由最佳化。

### 3.2 八項必要因素（依 PDF p.5）

**單張深度影像：**`RawPointCount`、`VoxelizedPointYield`。  
**相鄰深度影格：**`CoarseRANSACFitness`、`CoarseRANSACRMSE`、`CoarseRANSACCorrespondences`、`ICPInlierFitness`、`ICPInlierRMSE`、`ICPInlierCorrespondences`。

- 每張完整處理影格預期兩項、每個相鄰影格 pair 六項；若有 `N` 張有效完整批次，預期紀錄數量是 **`2N + 6(N-1) = 8N-6`**。例如若一樓確為 `N=191`，則為 `1,522` 筆；必須依實測 N 確認。
- 量測值要來自 **voxel 前／後與真實 RANSAC／ICP** 結果，不以推估值代替。
- `VoxelizedPointYield` 是**點數**，非保留率。`Mean L2` 是重建執行結果，**不是第九項因素**。
- 原始因素是證據，不是主觀品質評級；**第一次 Baseline 不預設 Pass/Fail 門檻**。
- 新 Selected 影格子集可能產生原本不存在的相鄰配對；不能重用舊 pair 的配準數據當作該新配對的真實量測。既有 sealed Baseline 證據必須保留。

---

## 4. 實驗紀錄管理與公平比較規範

### 4.1 正式紀錄與額外研究紀錄分開

**正式紀錄（必做）：**沿用老師的 `api.py`、Ontology、Turtle、SPARQL、Baseline／Selected Run，並驗證合法性、封存及完整性。  
**輔助研究紀錄（可新增）：**在獨立工作區由 Codex 建立每次實驗的設定、結果、圖檔、指令、版本及解讀，避免教師系統同模式 run 會覆寫舊紀錄的問題；不擅自改動 Ontology。

建議建立不覆蓋的 `experiments/` 正式工作區及 `artifacts/` 或 `research_outputs/` 輔助結果區（依實際程式行為確認後建立），並將**實驗輸出**排除於 Git；**用來重現的腳本、設定範本、說明及清單**應追蹤於 Git。任何重跑都用新的唯一 ID 或新實驗目錄，避免舊圖片冒充最新數據。

每次 Run 至少記錄：

| 類別 | 必要欄位 |
|---|---|
| 身分 | Run ID、時間、資料批次／樓層、階段、正式或 Bonus、對應 Git Commit SHA |
| 輸入 | 來源資料路徑、影格總數與實際使用索引、相機參數來源、深度單位、拍攝路線（Phase 2） |
| 演算法 | ICP Backend、Voxel、FPFH／RANSAC／ICP 設定、Seed、軟體版本、可重跑指令 |
| 動機 | `Observation → Hypothesis → Intervention → Result → Interpretation`，明確說明目的與為何選擇此參數 |
| 結果 | Mean L2、成功重建／實際評估幀數、保留比例、總耗時、可得的階段耗時、地圖覆蓋情況、八項因素統計 |
| 證據 | RGB-D 檔案、Turtle Run、圖表與圖片路徑、查詢檔、失敗原因及限制 |

### 4.2 輸入與比較原則

- **區分數量**：原始配對影格數、選取影格數、成功重建數、實際納入 GT 評估數、保留比例，不能混用。
- 每個 Run 使用一致定義的**總執行時間邊界**（例如從重建開始至計算／圖像輸出結束），並另外記錄 registration／ICP 時間供 Bonus 分析。比較時必須揭露計時方法。
- Mean L2 不同組若對應不同相機位置或影格數，不能不加限制直接當成公平排名。除官方 Mean L2，必要時對 P2-A／P2-B **相同被保留影格**補充相同樣本的比較；不能以此替換正式官方值。
- 評估場景是否涵蓋主要房間、連通區與相關角落；不能為了更小 Mean L2 選很短路線或大量刪影格，卻忽略地圖完整性。
- 固定隨機種子、記錄實際參數與環境；重新執行時驗證數值容差與結果圖對應的版本。報告只能使用實測資料；推論與已觀察事實明確區隔。
- SPARQL 的 `FILTER NOT EXISTS` 語意要依查詢實際結果驗證；PDF 範例**不是固定或最佳門檻**，尤其不能把其 `VoxelizedPointYield > 50000` 範例誤解為直接保留大於門檻影格。

### 4.3 刪除、覆寫與磁碟安全

- Phase 2 YAML 可能設定 `clear_existing: true`；在 `load.py`／`prepare_capture_dirs` 行為確認前，不得對共用 `eval/_data/second_floor/` 根目錄啟動會刪除既有資料的 capture。
- 每次擷取使用**獨立、唯一**的 `--output-root`；執行前顯示將寫入／可能清除的實際絕對路徑，確認既有資料是否受影響。
- `--no-write` 不一定是完全唯讀（可能仍寫圖）；`--no-vis` 不表示跳過重建與地圖整合；執行前核對真實 CLI 行為。
- 磁碟空間不足時先回報哪些檔案占空間與可安全清理項目，**未經同意不得清除 capture、Replica、Pixi 或已驗收的實驗產物**。

---

## 5. 實施里程碑、微型 Commit 與驗收停止點

> **重要：每個 Milestone 只能在使用者核准後啟動。Milestone 內可連續完成已授權的相關 TODO，但每項獨立完成且通過測試的功能要立即 Commit，不必等到整個 Milestone 結束才提交。**

### M0 — 建立 Git 基線並保留實作前版本

**執行：**依第 2 節檢查 Git 現況、建立 `.gitignore`、Init Commit、固定 `snapshot/pre-implementation`、回到 `main`。可先整理最小驗收列表，但**不修改程式與資料，不開始 M1**。

**驗收：**`main`／`snapshot/pre-implementation` 指向相同初始程式版本、沒有 remote（除非使用者日後另行授權）、大型資料與環境未納入 Git、Initial Commit SHA 可辨識。

**停止並請使用者核准 M1。**

### M1 — 必要演算法、TODO 與基本驗證

依依賴關係拆成可獨立驗證的小單位，依序實作並 Commit；例如：

1. `depth_image_to_point_cloud`：使用本批 `intrinsics` 與有效深度，**自行**完成 Depth Unprojection、顏色配對、單位檢查；合成像素可對上手算。
2. `preprocess_point_cloud`：Voxel、法向量、FPFH；處理空點雲或點數不足。
3. RANSAC Global Registration：用 FPFH 找粗對齊，確認 source／target 方向及真實配準統計。
4. `local_icp_algorithm`：用 **Open3D Point-to-Plane ICP** 從 RANSAC 初始化精細配準；保留真實結果物件與指標。
5. `reconstruct`：完成配對、逐影格讀取、姿態累積、相機位置、全域點雲整合；`build_cloud` 開關不應影響定位結果。
6. `visualize_and_evaluate`：正確以首相機姿態為座標基準，GT 僅用於評估、計算 Mean L2，繪製紅估計／黑 GT 及必要時移除天花板。
7. 八項 factor callback：針對完整影格／相鄰 pair 寫入真正測得的值；驗證結果紀錄與 `reconstruct.py`／`api.py` 相容。
8. 用**小型合成測試資料**驗證宣告、Baseline、selection query、Selected run 真正可回讀、Turtle/seal、圖像與不覆蓋行為；不得將合成數據當正式作業實驗。若需要修改原有等級 C 核心或 Ontology，先提出修改申請。

**至少要有的測試：**手算反投影與零／負／無效深度；色彩通道；已知剛體平移與旋轉；三影格位姿合成；首幀非原點且帶旋轉的 GT 對齊；影格檔名與 pose 對應；真實或合成低重疊退化配準；八項因素的數目／來源；封存有效與失敗分支。

**M1 輸出：**修改清單、逐功能 Commit SHA、測試指令與結果、Depth Scale 與座標約定的查證依據、完整因素與 RDF 驗證、未解決風險。**不執行 Phase 1 正式完整 Baseline**。

**停止並請使用者核准 M2。**

### M2 — Phase 1：一樓完整 Baseline 與診斷

1. 使用原始 `eval/_data/first_floor/`；確認 RGB/Depth 數量、排序、GT pose／內參一致性，資料不修改。
2. 透過老師的正式 CLI 建立一樓 experiment，對**完整批次**執行 First-Pass，後端固定 Open3D Point-to-Plane。
3. 保存真實重建圖（必要時去天花板）、紅估計／黑 GT、Mean L2、影格／評估數、實際耗時、完整參數、Seed、八項因素及 Turtle/seal。
4. 產生 `api.py explore`／驗證圖表、異常影格時間區間、問題分類；確認地圖涵蓋主要房間、連通空間及角落。
5. 根據量測提出有限數量的**候選**介入方向（Voxel、registration、frame selection 等），每一項指出量測證據、目的、預期效果與可能代價。
6. **此時不得自己搜尋最佳參數、設定 SPARQL 篩選門檻或直接做 Selected**。先向使用者提出 Baseline 診斷摘要與建議選項。

**驗收：**可以重跑的完整一樓 Baseline、合法因素紀錄、實際圖片與數值；真實觀察／尚待驗證假設分開。  
**強制停止：使用者看過 Baseline 後，選定 M3 的實驗方向。**

### M3 — Phase 1：證據導向參數／資料介入

1. 根據使用者核准的 M2 診斷挑選實驗，不預設每種策略都要做。
2. 可選方向包括 Voxel Size、RANSAC/ICP 對應距離或收斂條件、SPARQL Frame Selection；實際值以真實資料及使用者核准為準。
3. 每組實驗用獨立 ID 保存 `Observation → Hypothesis → Intervention → Result → Interpretation`，控制變因、參數差異、影格索引、實測 Mean L2／執行時間／地圖覆蓋與因素圖。
4. 比較不僅看 Mean L2，也看樣本數、影格保留率、配準品質及地圖完整性；即使變差也保留結果。
5. 確保**正式合法 `selected` run 確實寫入**，而非只在記憶體計算出結果。現有程式的 `--selection-query` 預設是否寫入必須先檢查；不能不經授權修改教師 API。
6. 保留全部經評估的候選結果與對應的 Git Commit、實驗指令、圖片；只將經確認的正式成果列入主比較表。

**驗收：**至少有可解釋的 Baseline／Intervention 實測前後比較、八項因素證據、合法 Baseline／Selected、可追溯紀錄。  
**停止並請使用者核准 M4。**

### M4 — Phase 2：三組資料設計與完整實驗

**重要區分：**P2-A／P2-C 是兩次**獨立實際擷取**；P2-B 是由 P2-A 的**同一批資料選取影格形成的介入／對照**，不是新拍的一條路線。

#### M4-A — P2-A：主要完整路線與密集拍攝

- 使用者參與規劃、**自行操作**目前 Habitat-Sim 的 `W/S` 前後移動、`A/D` 水平轉向、`C/Space` 擷取、`Q/Esc` 結束。相機高度與俯仰固定，不新增上下轉動功能。
- 路線須覆蓋二樓主要房間、連接空間及相關角落；優先以較密集拍攝取得相鄰視角重疊，**不預先固定 213 張**（PDF 圖例並非必須張數）。
- 固定相機設定與 Depth 效果設定；記錄路線圖／行走順序、擷取位置、影格數、觀測缺失與實際輸出目錄。
- 捕獲路徑應是**新的獨立資料夾**，不得沿用 `env_test` 或會清掉其他資料的共用根目錄。
- 在正式捕獲後，先檢查 RGB/Depth/GT/Intrinsics 完整性，再以 Open3D Point-to-Plane 執行完整 First-Pass Baseline、記錄八項因素並產生完整場景。
- **停止點：先讓使用者檢視 P2-A Baseline 及品質量測，再決定 P2-B 的取樣比例。**

#### M4-B — P2-B：同一路線的稀疏影格／較低預期重疊對照

- 從 P2-A 的**原始完整 capture**選取較稀疏影格（可透過老師的 SPARQL Selection 介面），相機路徑、拍攝方向和環境觀測來自同一次擷取。
- 取樣比例、篩選規則由 P2-A Baseline 的真實診斷與使用者決定；儘可能保留首影格，避免參考座標系不一致。
- 比較 Mean L2、保留影格比例、配準 Fitness/RMSE/Correspondences、實際耗時、重建覆蓋與失敗區間；必要時補充共同影格上的評估。
- **「較低視角重疊」是實驗假設，不是已量測事實**；若無客觀重疊量測，不可報成某個 overlap 百分比。
- 記錄相鄰影格跨度、位移及轉角等可分析的採集特徵；不把互動模式下的按鍵快慢直接當作真實相機速度實驗。
- P2-B 是 P2-A 的 Data Intervention；保留完整 P2-A Baseline factors，不擅自改寫封存證據；確保正式 Selected Run 可回讀。

#### M4-C — P2-C：不同路線（新增且確定必做）

- **再獨立擷取一個不同的二樓路線**。不同之處在於行走順序、進出房間方式、水平轉向／重訪安排，而非相機上下俯仰。
- 盡量與 P2-A 涵蓋同一批主要房間與連通區，並保持相近相機設定、Depth 效果與拍攝密度，使「路線差異」的分析更有說服力；實際路線與影格數由使用者在本子階段核准。
- 用新的唯一 Capture ID，保存路線紀錄與擷取影格數，**不能覆蓋 P2-A／B 或 env_test**。
- 對 P2-C 執行自己的**完整 Baseline 重建與八項因素分析**，視實際問題再決定是否新增 P2-C 的資料介入；至少必須與 P2-A／B 比較 Mean L2、影格數／評估數、耗時與地圖覆蓋。
- 比較時清楚標示 P2-C 與 P2-A **不是相同 GT 評估樣本或相同順序**；不能只用 Mean L2 數字宣稱路線的單一因果效果。

#### M4-D — 二樓階段整體驗收

- 至少在 P2-A 完成 **完整 Baseline → 八項因素檢查 → P2-B 介入 → 重建與比較**，滿足正式 Phase 2 的資料驗證及改善分析要求。
- 另外完成 P2-C 的獨立 capture、重建與比較；對 P2-C 的改善策略是否增加額外 Selected，由實測診斷再決定。
- Phase 1 和 Phase 2 均需有正式 Open3D 結果；整理跨階段比較與研究限制。

**驗收：**三個條件都有明確資料來源；P2-A／P2-B 與 P2-C 輸出可辨識，二樓至少有合法 Baseline／Selected 的實驗紀錄，圖片、數值、路線與取樣條件可追溯。  
**停止並請使用者核准 M5。**

### M5 — Bonus：Custom Point-to-Point ICP + Kabsch SVD（已確定，最後才實作）

1. 僅在 Phase 1／2 **正式 Open3D 成果全部驗收**後開始；不要讓 Bonus 回寫或覆蓋正式實驗資料與 run。
2. 在 `my_local_icp_algorithm` 自行實作 **Point-to-Point ICP**：最近鄰對應點搜尋、對應過濾、用 **Kabsch SVD** 求最佳剛體旋轉和平移（包含反射校正）、轉換累積、收斂條件及異常處理。
3. 不得呼叫 Open3D 的 `registration_icp` 或相同封裝，假裝已自行完成 ICP 核心；可以在不違反自製核心要求的前提下使用一般陣列／近鄰搜尋工具，但必須說清楚哪些步驟自行實作。
4. 若教師原有 Bonus TODO 註解同時寫 Point-to-Plane 與 Point-to-Point，不可刪改老師原文；保留原有 TODO，在新增註解中說明**正式 PDF 未限制 Bonus 形式、使用者已選擇 Point-to-Point + Kabsch**。若需改既有非 TODO 契約，先取批准。
5. 固定代表性的 Phase 1 與 Phase 2 資料、影格及相容參數；沿用 RANSAC 初值，**僅替換 ICP 後端**，以獨立路徑記錄 Custom 與 Open3D 的 Mean L2、ICP 時間、總時間、重建圖及可比較的配準指標。
6. 自製 Point-to-Point 與 Open3D Point-to-Plane **最小化的誤差目標不同**，不能將所有差異當作純粹實作速度差；報告須明確描述這項限制。
7. Bonus 對應程式、單元測試與 README 註記都應有小步 Commit；絕不能把正式 Phase 1／2 Backend 改成自製。

**驗收：**自製最近鄰與 Kabsch 可通過已知剛體變換測試；有獨立且真實的時間／準確度比較，正式 Open3D 成果未改動。  
**停止並請使用者核准 M6。**

### M6 — 英文 PDF、最終繳交 ZIP 與可重現性驗收

**正式 `report.pdf`：**內容簡潔、全英文，且以真實實驗結果撰寫：

1. **Implementation / Reconstruction Pipeline**：手寫反投影、Voxel、Normals、FPFH、RANSAC、Open3D Point-to-Plane ICP、點雲整合、Pose／GT／Mean L2；說明實際設定、困難與解法。
2. **Data Verification**：八項因素名稱、量測定義、設定及 source links；觀察到的失敗案例、圖表及證據導向的介入原因。
3. **Results and Discussion**：Phase 1 與 Phase 2 重建截圖（需要時去天花板）、紅估計／黑 GT；各次比較的 **Mean L2、Frame Count、Total Execution Time、Tested Hyperparameters** 表格；另外交代 evaluated frames、retained-frame fraction 與地圖覆蓋。
4. **Phase Comparison**：Phase 1 的改善策略、P2-A／B 拍攝間隔、P2-C 路線差異、跨階段比較與限制。
5. **Bonus**：獨立介紹自行實作 Kabsch Point-to-Point 與 Open3D Point-to-Plane 的方法差異、時間／準確度比較。
6. **Questions**：依 PDF 第 12 頁逐題回答：(1) 不執行 RANSAC 直接 ICP 的情況與原因；(2) 提高 ICP 穩定性的設定；(3) 資料品質與拍攝選擇如何影響重建表現及 Mean L2。
7. **可追溯性**：所有表格、圖像、超參數與描述必須來自實際 Run、正確版本與當次輸出；不編造數字、結果或因果。

**ZIP 交付：**

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

- ZIP 根目錄直接放上述內容，不要再包一層同名資料夾。
- PDF 同時要求包含**所有重建及資料驗證所需原始碼**。目前 `plot.py`、`packages/simulator/`、必要設定及相依來源與 PDF 示意樹存在差異；打包前先檢查實際依賴並**向助教／課程規則確認額外來源的繳交方式**，不能為了迎合示意樹而漏掉執行所需程式，亦不可自行假定可任意附加。
- **不得包含**實驗 Turtle 結果檔、生成診斷圖表、Phase 2 Capture、Replica 資產、`.pixi`、建置快取或無關檔案。注意 `ontology/hw1.ttl` 是**必交的定義檔**，不等於需排除的實驗 `.ttl`。
- Bonus 函式應留在提交來源中，並於 README 說明；仍保留正式 Open3D Pipeline。
- 驗收前先取得正確 `<student-id>`，依已確認的規則建立 ZIP，檢查完整檔案清單、英文報告與乾淨環境可重現性；不能猜測學號、截止日期或扣分比例。

**驗收：**作業規定項目齊全、報告圖表與實測一致、正式 ZIP 格式及相依程式已確認、使用者最終審查通過。

---

## 6. 每個 Milestone 必交的驗收報告模板

Codex 在每個里程碑完成後，都必須**停止，不自動開啟下一里程碑**，用繁體中文回報：

1. **完成內容**：對應正式 PDF 需求及本里程碑驗收條件；區分完成與未完成。
2. **Git 狀態**：目前分支、短 Commit SHA、該階段所有小步 Commit 與變更檔案；確認沒有把大型資料加入 Git。
3. **執行證據**：實際使用指令、測試通過／失敗結果、資料與輸出位置、必要截圖或指標。
4. **實驗紀錄**（如適用）：原始資料、設定、Seed、版本、評估影格數、Mean L2、Runtime、八項因素與 Baseline／Selected 狀態。
5. **未解決問題**：錯誤、警告、規範衝突、可能資料破壞與比較限制；不要隱藏失敗。
6. **建議下一步與決策點**：列出待使用者決定的選項，但**不得自行進入下一階段**。

小功能完成時可以先做微型 Commit，無須每一個 Commit 都向使用者詢問；若遇到**等級 C 修改、破壞性操作、正式實驗策略決策**，則須在該動作前取得明確同意。

---

## 7. Codex 讀到本文件後的第一個任務（重要）

**本次先只執行 M0，不要直接實作任何 TODO，也不要執行 M1～M6。**

具體順序：

1. 讀完原始 PDF、本交接文件、現有架構盤點及相關程式，並確認使用者指定的專案路徑。
2. 檢查本機 Git 狀態、磁碟容量、可能被刪除的輸出路徑，以及 `.gitignore` 草案。
3. 執行 **M0：在 `main` 初始化本機 Git、建立實作前原始碼 Commit、建立固定的 `snapshot/pre-implementation` 分支並回到 `main`**；不設 remote。
4. 提供 M0 驗收報告，列出 Git Short SHA、分支、追蹤／忽略檔案、任何需使用者裁決的相依來源或容量問題。
5. **停止，等待使用者核准 M1**。不要因為開發計畫已完整，就自行一路做完後續實作、實驗與報告。

---

## 8. 可參考的作業原始 CLI（執行前仍須用 `--help` 與實際原始碼核對）

```bash
# 工作目錄
cd "/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1"

# 已成功使用的環境驗證
pixi run -e habitat smoke
pixi run -e habitat python -c "import open3d, rdflib, cv2, numpy; print('core packages OK')"

# Phase 1 宣告（名稱、路徑依實際方案設定）
pixi run -e habitat python api.py declare \
  --name <experiment-name> \
  --data-dir eval/_data/first_floor \
  --floor 1

# 完整 Baseline（使用已宣告的獨立實驗）
pixi run -e habitat python reconstruct.py \
  --experiment experiments/<experiment-name>

# 檢視圖表／資料
pixi run -e habitat python api.py explore \
  experiments/<experiment-name>

# 以查詢選取影格（確定正確 query path、並核對是否需要明確寫入 selected）
pixi run -e habitat python api.py query \
  experiments/<experiment-name> \
  --query-file experiments/<experiment-name>/queries/frames.rq

# 正式 Phase 2 擷取只可在 M4 核准後使用；output-root 必須是新的獨立路徑
pixi run -e habitat python load.py \
  --config configs/second_floor.yaml \
  --output-root eval/_data/second_floor/<unique-capture-id>
```

> **提醒：**以上僅是流程範例，不是要求立刻執行；尤其 `load.py` 的清除行為、`reconstruct.py` 的 selected 寫入條件、現有 `pixi test` 是否指向不存在的測試檔，都必須先核對實際程式。
