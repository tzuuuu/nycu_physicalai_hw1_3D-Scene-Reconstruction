# Physical AI HW1 — Phase 1 Final Closeout

## 任務定位

Phase 1（M2＋M3）所有正式實驗已完成，M3.2七個預先規劃的條件亦已全部各嘗試一次。

現在正式啟動 **Phase 1 Final Closeout**，整合以下工作：

1. 作業規範與必要程式碼的完整性稽核。
2. Ontology、Experiment Turtle與各實驗獨立性的確認。
3. 最終英文報告所需圖片、數據與圖說的準備。
4. Phase 1最終研究成果與Future Work整理。
5. 最終ZIP繳交的準備度檢查。
6. Phase 1結案與Phase 2交接。

本次不執行新的配準實驗、參數搜尋或重新重建。

請依照以下F1、F2、F3順序執行，保留各階段驗收紀錄，不要同時混合修改。

---

# F1 — 作業規範、程式碼與完整性稽核

## 1. 閱讀權威資料

必須先閱讀：

- 老師原始 `HW1_3D Scene Reconstruction.pdf`。
- 原始 `snapshot/pre-implementation` 分支。
- 現有核心程式及相關測試。
- M0至M3.2的既有驗收與研究計畫文件。
- 最新M3.2 `final_provenance.json`、科學完整性審計及歷史停止紀錄。

PDF為作業規範的最高依據，既有實驗驗收文件為已執行事實的主要證據。

若文件、程式碼、實際產物有不一致，必須列出差異，不可以自行推測或補造結果。

## 2. 必做程式碼稽核

逐項核對老師原始TODO及現有實作：

- Depth Unprojection：手寫Pinhole Back-projection。
- Voxel Downsampling。
- Normal Estimation與FPFH。
- RANSAC Global Registration。
- Open3D Point-to-Plane ICP。
- Pairwise Transformation與Trajectory Composition。
- Scene Map Reconstruction。
- Mean L2 Evaluation。
- Estimated Red／Ground Truth Black Trajectories。
- 八項Pipeline-grounded Factors。
- Baseline／Selected Reconstruction流程。
- Experiment Declaration、Explore、SPARQL Query與Turtle Seal。

對每項記錄：

- PDF對應頁碼。
- 原始TODO或規範。
- 目前程式位置。
- 實作完成情況。
- 測試或正式實驗證據。
- 未解決問題。

確認所有必做TODO已完成。Optional Bonus ICP須另外標記，不得混入必做內容。

請檢查既有 `--down-voxel` 修改是否仍保留預設行為及CLI相容性。

## 3. Ontology與Turtle稽核

特別檢查：

`ontology/hw1.ttl`

確認：

- 與老師原始版本的差異。
- RDF/Turtle語法有效。
- 必要Ontology Classes、Properties與八項Factor Definitions完整。
- 現有API能正確載入。
- 是否有任何PDF明確要求但尚未實作的部分。

必須明確區分：

**Ontology檔案**
`ontology/hw1.ttl`

**實驗紀錄**
`experiments/<experiment-name>/<experiment-name>.ttl`

最終ZIP包含前者，排除所有生成的Experiment Turtle。

不因本次稽核而修改Ontology，也不得把實驗數據合併進Ontology定義檔。

## 4. Baseline與實驗隔離稽核

確認以下研究成果仍完整保留：

- M2原始Baseline。
- M3.0唯讀診斷。
- M3.1 Selected Reconstruction。
- M3.2 B0／B1／B2。
- M3.2 C1／C2／C3／C4。

檢查每組的Workspace、Turtle、因素、參數、Run及研究產物來源。

特別確認：

- M2 Baseline未被後續M3.2實驗覆寫。
- M3.1雖在原Workspace加入Selected Run，但Baseline正式子圖保持完整。
- B／C獨立條件各自保存輸出。
- B0與C組Seed 0共用同一次Run。
- 所有正式Turtle、Seal及因素數量一致。
- 原Capture、GT與核心程式SHA保持一致。
- 歷史停止紀錄未被刪除或改寫。
- 已核准的兩個 `.DS_Store` 精確例外沒有影響科學資料驗證。

比對教師原始Snapshot與main的程式差異，明確區分必做TODO實作、已核准修改與其他差異。

## 5. 最終ZIP程式相依稽核

依PDF第5.1節，正式ZIP包含：

- `load.py`
- `reconstruct.py`
- `utils.py`
- `api.py`
- `ontology/hw1.ttl`
- `report.pdf`
- `README.md`

但PDF同時要求包含重建與Data Verification所需的全部原始碼。

因此必須分析Import與檔案依賴：

- `plot.py`
- `packages/simulator/`
- `configs/`
- SPARQL Query來源
- 其他必要本機模組
- Pixi環境與相依套件

區分：

A. PDF明確指定必交。

B. 程式執行必要相依，可能需額外包含。

C. 研究輔助工具，非正式執行必要。

D. 生成產物，PDF明確排除。

檢查若只包含PDF示意檔案，是否會發生Import錯誤或其他缺檔問題。

可在獨立暫存目錄進行靜態分析及小型安全測試，不執行正式191張重建。

若有提交格式與依賴關係上的不明確之處，明確記錄為需向助教確認，不要自行假定。

## F1驗收產物

新增：

`docs/implementation/Phase1_Submission_Readiness_Audit.md`

內容包含：

- PDF符合性矩陣。
- 必做程式碼完成度。
- Ontology與Turtle檢查。
- Baseline與實驗隔離檢查。
- SHA保全。
- 最終ZIP相依分析。
- README缺漏。
- 需要留到Phase 2或最終報告處理的項目。

若發現實際缺少必做程式碼、科學資料不一致或重要成果損壞，停止並回報，不自行修復。

若僅有報告素材、README或ZIP準備度的待辦事項，清楚標記並繼續F2。

---

# F2 — Phase 1最終報告圖片與數據整理

## 1. 老師的正式重建圖片要求

必須符合：

"Provide reconstruction screenshots with the ceiling removed, the estimated trajectory in red, and the ground-truth trajectory in black."

每張正式重建圖片須：

- 移除天花板。
- 顯示真實重建場景／點雲。
- Estimated Trajectory為紅色。
- GT Trajectory為黑色。
- 使用固定首相機座標系。
- 不以GT進行最佳旋轉、平移、尺度擬合或修正。
- 不修復原本錯誤的重建結果。
- 清楚顯示房間、連通區域、角落與軌跡。

## 2. 必要單一重建圖片

準備以下結果：

- M2 Baseline。
- M3.1 Selected（排除Frame 104）。
- M3.2 B2。
- M3.2 C1。
- M3.2 C3。

另外為B0、C2、C4建立正式重建圖片索引，確保未來報告需要時可以查閱。

B1配準失敗，沒有完整191張地圖，不得製作虛假的完整重建圖片。

## 3. 必要比較圖

### A. Baseline vs Selected

呈現：

- Baseline：191張、Mean L2 = 3.174055104788 m。
- Selected：190張、Mean L2 = 4.200397987246 m。

另於圖說說明共同190張比較的Baseline Mean L2 = 3.185555603874 m，Selected相對惡化31.86%。

### B. Registration Pipeline Scale

比較：

- B0：v=0.05、seed=0。
- B1：v=0.03、seed=0，配準失敗。
- B2：v=0.08、seed=0。

B1清楚標記70→71 RANSAC失敗，不顯示虛構Mean L2。

### C. RANSAC Seed Sensitivity

固定v=0.05，呈現seed0至seed4全部五組。

清楚標示：

- Seed0、2、4：103→104重大旋轉錯解。
- Seed1、3：沒有同級翻轉。

所有成功條件都須列出實際完整191張Mean L2。

## 4. 圖片視覺化一致性

同一比較組使用：

- 相同視角及座標軸。
- 相同X／Z顯示範圍。
- 相同長寬比。
- 相同點雲可視化抽樣規則。
- 相同紅黑軌跡配色。
- 相同字體、標籤格式與圖例。

至少提供Top-down View；若既有資料允許，可另外製作Isometric View。

正式重建圖需包含場景點雲，不可只用紅黑軌跡曲線取代。

產生高解析度PNG，確保縮放到A4報告仍可閱讀。

優先使用既有正式重建PNG或已保存的點雲、位姿重新繪圖；若缺少必要來源，不得重新執行RANSAC、ICP或完整重建來補圖。標記限制即可。

## 5. Data Verification分析圖片

整理已存在的研究證據：

- 103→104姿態翻轉診斷。
- Per-frame L2 Error。
- RANSAC／ICP局部旋轉與平移誤差。
- 八項品質因素及時間序列。
- Baseline／Selected比較。
- B／C組完整比較。
- Mean L2、Runtime及設定表。

不得變更原始量測或挑選性隱藏負面條件。

## 6. 圖說與來源

每張圖片都要準備簡潔英文Figure Caption，包含：

- Experiment及設定。
- Frame Count。
- Mean L2（適用時）。
- 紅黑軌跡的意義。
- 圖中真正可以觀察的現象。

建立來源索引，記錄：

- 圖片路徑。
- 官方Experiment來源。
- 原始PNG／點雲／位姿來源。
- 是否原生截圖或離線重新繪圖。
- 視角、座標與裁切方式。
- 輸出尺寸。
- SHA-256。
- 圖說與限制。

## F2驗收產物

使用新的獨立目錄：

`research_outputs/phase1_report_assets/`

內部至少區分：

- `single_runs/`
- `comparisons/`
- `diagnostics/`
- `captions/`
- `manifest.json`
- `README.md`

所有圖片必須寫入新目錄，不覆寫M2、M3正式PNG或既有分析圖。

完成後應實際檢視圖片，確認圖例、場景、軌跡、座標範圍與文字沒有錯誤。

若沒有可用的影像檢視能力，不能假稱已完成視覺驗收；須在回報中列出需人工目視確認的圖片。

---

# F3 — Phase 1正式結案與交接

完成F1及F2後，整理唯一的正式交接文件：

`docs/implementation/Phase1_Final_Handoff.md`

文件內容：

## A. 作業規範與程式碼

- 正式PDF規定與對應實作。
- 必做TODO完成情況。
- Ontology與正式Turtle區別。
- 最終ZIP必要相依及未解決問題。
- 已核准的程式碼修改與原始Snapshot差異。

## B. 實驗研究歷程

- M2：Baseline。
- M3.0：103→104錯誤診斷。
- M3.1：Frame 104消融與負面結果。
- M3.2：B組Registration Pipeline Scale。
- M3.2：C組五個Seed敏感度。

每個階段保留研究問題、實驗設定、實際數據、主要發現與限制。

## C. 最終研究發現

明確討論：

- 103→104單一重大姿態錯解如何影響整段累積軌跡。
- 刪除第104張並沒有改善結果。
- B1細尺度配準失敗。
- B2改變整套Registration Scale改善Mean L2。
- 相同v=0.05下，RANSAC Seed造成極大差異。
- 5個Seed中3個發生重大旋轉錯解。
- Fitness／RMSE較好不一定代表GT軌跡精度較好。

區分資料直接證實的現象與尚待驗證的機制假說。

## D. Future Work

保留以下規劃，不實作：

- 全190對相鄰影格的Registration Success Rate。
- Failure-aware Frame Selection。
- Robustness vs Accuracy。
- 對RANSAC參數及confidence的額外研究。
- 更完整的跨資料集泛化驗證。

## E. 最終報告素材

整理：

- 所有必要重建圖。
- Verification Plots。
- 比較表。
- 英文Figure Captions。
- 來源連結及證據。
- 報告哪些章節可以直接使用。
- 哪些內容須等Phase 2完成。

## F. Phase 2交接

記錄可延續的：

- 正式Reconstruction Pipeline。
- Data Verification方法。
- 八項品質因素。
- Experiment Declaration與Turtle工作流程。
- 重建圖片標準。
- Mean L2及場景涵蓋評估方法。

不要把C1的Seed1或B2的Voxel0.08自動認定為Phase 2最佳設定。

Phase 2必須另訂實驗設計與核准程序。

---

# 最終執行規範

## 可以執行

- 唯讀稽核與必要小型測試。
- 使用既有科學證據產生新報告圖片。
- 新增獨立繪圖腳本、測試及來源索引。
- 撰寫F1、F2、F3的文件。
- 按原有小型Git Commit制度提交文件及輔助程式。

## 不得執行

- 修改老師的 `utils.py`、`reconstruct.py`、`api.py`、`load.py`。
- 修改Ontology或原始RGB-D／GT。
- 覆寫正式Experiment Workspace及Turtle。
- 重跑既有M2／M3實驗。
- 執行新Seed、Voxel或Experiment D。
- 修改SHA排除政策。
- 刪除任何歷史停止或授權紀錄。
- 開始Phase 2資料擷取。
- 實作Bonus ICP。
- 撰寫最終英文報告。
- 建立正式繳交ZIP。
- 把大型研究產物提交到Git。

若F1發現必做程式碼缺漏或來源完整性問題，必須停止並回報，不得未經核准修改核心。

若F2發現正式點雲或影像來源不足，保留既有可用圖片，清楚說明缺漏，不得為了補圖擅自重新重建。

## 最終交付摘要

請完成後回報：

1. F1規範與程式碼稽核結果。
2. F2報告圖片清單及預覽。
3. F3最終交接文件。
4. 是否有任何必做程式碼缺漏。
5. Ontology是否可直接納入未來正式ZIP。
6. 哪些相依檔案需另外打包。
7. 最終英文報告素材完成度。
8. 正式Turtle與SHA保全結果。
9. 測試、Git Commit及未解決風險。

最終狀態只能在完成必要檢查後標記：

`Phase 1 — Experiment Accepted / Submission Readiness Audited / Report Assets Prepared / Handoff Complete`

完成後停止，等待人工驗收。

不得自行進入Phase 2或其他實作階段。