# M1.3～M1.7 驗收紀錄

本次依使用者核准，僅完成 M1 剩餘演算法與功能驗證。未執行 M2、完整一樓 Baseline、二樓擷取、超參數搜尋、實驗宣告、Turtle 封存或 Selected 改善實驗；未實作 Bonus、未撰寫英文作業報告。

## 實作與權限

- `utils._global_registration`／`reconstruct` Stage 6：Open3D 0.18.0 FPFH mutual matching + RANSAC；當前影格 source → 前一已處理影格 target。剛體 Point-to-Point estimator 僅用於 RANSAC，幾何檢查為邊長比例 0.9 與距離 1.5 × voxel_size，收斂上限 100000、confidence 0.999，使用記錄的 seed。
- `local_icp_algorithm`：缺法向量時估計，Hybrid 半徑 2 × threshold、最多 30 鄰點；正式 ICP 固定 Point-to-Plane，上限 100 次、相對 fitness/RMSE 容差 1e-6，回傳原始 RegistrationResult。
- `_capture_inputs`／`_read_rgbd`／`reconstruct`：本批內參、數字共同檔名及要求順序、uint16 深度轉公尺、配準、`T_global = T_global @ T_current_to_previous`、相機中心、獨立地圖副本與原始回呼。
- `visualize_and_evaluate`：GT 首姿態的固定參考系、檔名對應 GT 列、Mean L2、紅估計／黑 GT、Headless 與 Open3D 顯示。未以最佳旋轉、平移或尺度擬合。
- 原始英文 TODO 及全部既有註解逐字、依序保留；對應處新增繁體中文說明及程式碼。必要 NotImplementedError 已移除；僅 Bonus 函式保留。
- M1.1／M1.2 函式、Bonus、其他教師已完成函式、CLI、API、Ontology、套件與原始資料均未修改。

## 深度與座標系依據

正式 PDF pp.2–3 要求手寫反投影，p.4 規定 capture 首姿態參考系，p.10 要求正式 Open3D Point-to-Plane。需求矩陣 C01、C04～C09、D02～D05 為追蹤依據。

擷取器 `packages/simulator/simulator/replay.py` 的 save_frame 將公尺深度乘 1000 寫入 uint16 PNG；既有 `DEPTH_SCALE=1000` 與反投影的 depth_m 公尺契約一致。本批 intrinsics.json 若缺 scale，讀檔邊界沿用該編碼；若有明示 `depth_scale` 則使用其正有限除數。只接受 uint16 深度 PNG，不猜測 8-bit 預覽或其他編碼；只在 `_read_rgbd` 換算一次，不修改原始 JSON。

重建座標為 X 右、Y 下、Z 前。評估以固定 diag(1,-1,-1) 轉到 Habitat 感測器軸向；GT 以原始首姿態旋轉與位置換算到同一參考系。GT 僅在評估函式載入。

### 已由使用者裁決的 Selected 衝突

PDF 指定原始 capture 首姿態，骨架則以首個消耗影格初始化。使用者已明確核准：Selected 必須保留原始首影格並置於第一位，否則明確 ValueError，不用 GT 補正，也不產生評分。保留首影格的非連續子集仍依要求順序處理。

## 測試範圍及結果

```bash
pixi run --locked -e habitat python -m pytest -q
```

結果：122 passed in 12.17s。相同測試檔案以反向順序、simulator 匯入測試在前重跑：122 passed in 12.20s。

| 測試檔案 | 案例數 | 核對內容 |
| --- | ---: | --- |
| tests/test_depth_unprojection.py | 34 | 已驗收反投影回歸 |
| tests/test_point_cloud_preprocessing.py | 24 | 已驗收前處理回歸 |
| tests/test_registration.py | 9 | 真實 FPFH/RANSAC、旋轉平移、真實 Point-to-Plane ICP、初始化、法向量、零對應與無效距離 |
| tests/test_capture_inputs.py | 12 | 本批內參、數字配對、明示／預設 scale、單次換算、損壞檔案、8-bit 拒絕 |
| tests/test_reconstruction.py | 8 | 真實 RGB-D 配準與 callback、build_cloud/down_voxel 不影響軌跡、GT 不參與、多影格矩陣組合、Selected 首影格限制、損壞影格與既有 CLI 完整性拒絕 |
| tests/test_trajectory_evaluation.py | 8 | 非零首位置／旋轉、非連續編號與順序、已知 5 m 偏差、GT 缺列與缺檔、紅黑軌跡、Headless |
| tests/test_m1_integration.py | 1 | 合成 RGB-D → 點雲 → 真實配準 → 18 因素 → Mean L2 → PNG |
| simulator 的 effects/import_surface | 26 | 既有非擷取測試 |

`pytest.ini` 明確限定以上預設專案回歸範圍；不收集第三方 Habitat-Lab 測試與 simulator 擷取 e2e。後者不在本輪授權範圍，本次未執行，也未列為通過。

真實配準測試使用 Open3D 的實際結果。只有隔離矩陣累積的測試注入受控轉換，並明確標示用途；不把該測試產生的統計當真實配準成果。

原始 CLI 失敗分支測試僅替換宣告讀取，使用真實重建與真實 callback；將封存／評估／run writer 設為禁止呼叫，證實缺因素時先行拋錯。未實際執行 Turtle 封存或宣告。

## 合成 Smoke Test 證據

資料由 test_reconstruction 的 rgbd_capture 合成建構器建立；三幀為相同視角，編號 3、20、101，48×40、HFOV 75°、voxel_size 0.08 m、seed 0。不是正式 Phase 1 或 Phase 2 資料，也不是改善實驗。

- 暫存證據：`/var/folders/22/2_0s87y12934rk6kt6823t2m0000gn/T/physicalai-m1-smoke-xhf9f_5i/summary.json`
- 圖片：同目錄 `smoke.png`，已實際檢視。
- 裁切後地圖點數：4149。
- Mean L2：6.82635178632514e-16 m，3 幀，無最佳擬合。
- 因素總數：2×3 + 6×2 = 18。透過既有 api.make_pipeline_measurement_callback 取得，未生成 TTL。

| 因素 | 實測值 | 真實來源 |
| --- | --- | --- |
| RawPointCount | 1920，逐幀共 3 筆 | 反投影點數 |
| VoxelizedPointYield | 1818，逐幀共 3 筆 | 降採樣點數，非保留率 |
| CoarseRANSACFitness | 1、1 | RANSAC RegistrationResult.fitness |
| CoarseRANSACRMSE | 5.422810143805612e-16、同值 | RANSAC RegistrationResult.inlier_rmse |
| CoarseRANSACCorrespondences | 1818、1818 | RANSAC correspondence_set 長度 |
| ICPInlierFitness | 1、1 | ICP RegistrationResult.fitness |
| ICPInlierRMSE | 0、0 | ICP RegistrationResult.inlier_rmse；兩次均有 1818 個對應，非無對應的假完美 |
| ICPInlierCorrespondences | 1818、1818 | ICP correspondence_set 長度 |

整合測試另外逐欄比對實際 RegistrationResult 與 callback 數值，Diagnostics 轉換亦核對原始 ICP 結果。上述暫存檔案未加入 Git，可由同一合成測試重建。

## 失敗處理、相容性與限制

- 無內點或非有限配準結果會以含影格編號、fitness、RMSE、對應數的例外中止；不以零誤差當成功。
- 損壞中間影格會依教師原分支警告並略過；不補回假因素。既有 CLI 完整性檢查會拒絕封存；預測數量與評估輸入不一致時回傳 inf。首參考影格損壞則直接拒絕，避免更換參考系。
- RGB／Depth 不對稱仍依既有共同檔名契約處理並發出警告。正式資料完整性不能只依 declaration 成功判斷；M2 前須獨立核對兩邊完整集合與 GT 列數。
- 原始 JSON 缺 scale 是已知來源落差，不宣稱已修正資料；未驗證未知外部深度編碼。
- 法向量／特徵存在不保證幾何不退化；合成配準測試不代表完整一樓、低重疊或長軌跡穩健性。
- 合成 Smoke Test 為相同視角；非零旋轉與平移分別由已知剛體配準及矩陣累積測試驗證，未據此宣稱真實移動場景重建品質。
- Open3D 0.18.0 在本機先載入 NumPy 而未先設定 OpenMP 時曾原生崩潰；根目錄 conftest.py 在所有測試收集前沿用既有 OMP_NUM_THREADS=1。預設與反向順序測試均通過，未升級核心依賴。
- Pixi 快取讀取警告、Matplotlib 預設快取目錄不可寫警告仍存在；Matplotlib 使用系統暫存快取後成功產圖，未修改使用者環境。
- 紅黑視覺化測試攔截 draw_geometries 檢查幾何與色彩；實際 Headless PNG 已產生並檢視，未做人工互動視窗驗收。
- 未驗證正式 Turtle 封存、Baseline／Selected run 寫入或正式結果品質，依使用者本輪限制留待後續授權，不宣稱 Data Integrity 的正式成果已完成。

## 本次功能提交

| 階段 | Commit | 訊息 |
| --- | --- | --- |
| M1.3 | 1c0c843 | feat: implement FPFH RANSAC global registration |
| M1.4 | 88c65bc | feat: implement Open3D point-to-plane ICP |
| M1.5 讀取 | a371ae4 | feat: load capture-specific RGB-D inputs and depth scale |
| M1.5 整合 | c8fd430 | feat: compose camera poses and integrate RGB-D reconstruction |
| M1.6 | 1922c1c | feat: evaluate and visualize trajectories in capture reference frame |
| M1.7 | 包含本紀錄的提交 | test: verify M1 integration and import-order stability |

本次所有工作在 main 完成，snapshot/pre-implementation 必須仍指向 291209750bd8ecf84f337112c9b92307e6be192a。停止於 M1，等待使用者驗收，不進入 M2。
