已完整閱讀並核對正式 PDF 的 **13 頁文字與頁面圖像**，再比對兩份 Markdown 與目前原始碼。資料實際位於 `docs/assignments/`。

主要結論是：**現有 TODO 大致涵蓋必做重建演算法，但完成 TODO 並不等於完成作業**。另外還必須驗證 Turtle 完整性、Baseline／Selected Run 寫入、實驗時間與參數追蹤、兩階段實驗證據，以及繳交套件的可重現性。

本次未修改專案檔案、設定或資料集，未執行重建、建立實驗紀錄或撰寫英文報告；僅於系統暫存目錄產生 PDF 閱讀用圖像。

規範來源為 [正式作業 PDF]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/docs/assignments/HW1_3D Scene Reconstruction.pdf)。下列頁碼均為 PDF 印刷頁碼，也與檔案頁次一致。

**1. Requirements Traceability Matrix：必要實作**

狀態定義：「已實作」指已有原始碼邏輯，本次未做執行驗收；「部分」指只有介面、骨架或部分流程；「待完成」指尚未實作或尚無成果。

| ID  | 正式要求                                                     | PDF               | 對應原始碼                                                                                                                                                                                                                                              | 目前狀態                     | 未來驗收條件                                                              |
| --- | -------------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------- |
| C01 | 使用每批 capture 自己的相機參數與深度尺度                                | pp.2–3、10         | [\`utils.reconstruct\`:167 (line 167)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:167)；[\`save_intrinsics\`:46 (line 46)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/packages/simulator/simulator/replay.py:46) | 部分；實際 JSON 缺 depth scale | 正確讀取批次參數；深度轉公尺一次；缺欄位處理有明確依據。                                        |
| C02 | 自行實作 pinhole Depth Unprojection，不得直接使用 Open3D projection | pp.2–3、10         | [\`depth_image_to_point_cloud\`:18 (line 18)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:18)                                                                                                                                 | 待完成                      | 合成像素可得到正確三維座標；無效深度排除；未呼叫內建投影完成此步驟。                                  |
| C03 | Voxel Downsampling、normals、FPFH                          | pp.2–3、10         | [\`preprocess_point_cloud\`:58 (line 58)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:58)                                                                                                                                     | 待完成                      | 輸出降取樣點雲、有效法向量與對應 FPFH；尺寸及空資料處理正確。                                   |
| C04 | Global Registration：RANSAC 粗配準                           | pp.2–3            | [\`reconstruct\`:205 (line 205)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:205)                                                                                                                                             | 待完成                      | 使用幾何特徵及一致性檢查，得到方向正確的初始剛體轉換與真實統計。                                    |
| C05 | 標準後端使用 Open3D Point-to-Plane ICP                         | p.10；一般介紹見 pp.2–3 | [\`local_icp_algorithm\`:78 (line 78)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:78)                                                                                                                                        | 待完成                      | 從 RANSAC 結果開始，使用 Point-to-Plane estimator，回傳完整 registration result。 |
| C06 | 完整逐影格流程、轉換累積、統一場景點雲與相機軌跡                                 | pp.2–3、10         | [\`reconstruct\`:142 (line 142)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:142)                                                                                                                                             | 部分；171 行立即拋錯             | 正確配對並處理影格；相對轉換組合方向正確；點雲與軌跡共用參考座標。                                   |
| C07 | GT 僅供評估，不得作為重建輸入                                         | p.4               | [\`reconstruct\` 契約:159 (line 159)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:159)；[\`visualize_and_evaluate\`:281 (line 281)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:281)                        | 介面分工符合；核心待完成             | 相同 RGB-D、不同 GT 不得改變配準結果；GT 僅影響評估。                                   |
| C08 | 共同首相機參考系下計算相機中心 Mean L2                                  | p.4、10            | [\`visualize_and_evaluate\`:281 (line 281)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:281)                                                                                                                                  | 待完成                      | 正確處理位置、旋轉、軸向與影格對應；手算案例一致；不得以額外最佳擬合掩飾誤差。                             |
| C09 | 紅色估計軌跡、黑色 GT；需要時移除天花板                                    | pp.2、10–11        | [\`visualize_and_evaluate\`:326 (line 326)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:326)；[\`remove_ceiling_points\`:124 (line 124)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:124)                 | 顯示待完成；裁切及圖片函式已有          | 視窗與截圖的座標、顏色一致；裁切不改變配準及評分。                                           |
| C10 | 地圖涵蓋主要房間、連通空間與相關角落                                       | p.11              | 點雲整合及結果顯示                                                                                                                                                                                                                                          | 尚無重建成果                   | 以兩樓層實際結果檢視涵蓋範圍；不得只用低軌跡誤差宣稱地圖完整。                                     |

PDF 沒有要求 TSDF、網格表面重建或必須輸出 `.ply`；目前缺少這些功能，**不應直接列為不符合規範**。

**2. Requirements Traceability Matrix：資料驗證與實驗分析**

| ID  | 正式要求                                                    | PDF         | 對應原始碼                                                                                                                                                                                                                             | 目前狀態                    | 未來驗收條件                                                                |
| --- | ------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------- |
| D01 | 宣告 capture 與重建設定；此時不選品質閾值、不判 Pass／Fail                  | pp.4、6      | [\`cmd_declare\`:847 (line 847)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:847)                                                                                                                              | 已實作宣告流程                 | 產生合法 declaration，來源批次與設定正確；不預填量測結果或品質分類。                              |
| D02 | 首次使用完整批次，邊重建邊量測八項因素                                     | pp.5、7      | [\`reconstruct.py\`:124 (line 124)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/reconstruct.py:124)；[\`pipeline callback\`:1000 (line 1000)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:1000)     | 協調器與回呼已有；上游未完成          | 所有預期影格與相鄰 pair 都有直接來自實際 pipeline 的量測。                                 |
| D03 | 原始量測為 experiment-scoped evidence，不改寫成 Pass／Fail         | pp.4–5      | [\`\_mint_pipeline_occurrences\`:1473 (line 1473)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:1473)；[\`Factor\`:428 (line 428)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/ontology/hw1.ttl:428) | 已有資料模型與 writer          | 因素正確連結 experiment、definition、Depth image／pair、value、evaluation state。 |
| D04 | 合法 Turtle declaration、Sealed Machine Section、完整因素       | p.10        | [\`seal_experiment\`:1560 (line 1560)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:1560)；[\`read_experiment\`:584 (line 584)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:584)              | 已有機制；未有端到端產物            | Turtle 可解析、seal 符合、occurrences 完整且無重複或外來影格。                           |
| D05 | 記錄 baseline 與 selected reconstruction runs              | p.10        | [\`write_run\`:638 (line 638)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:638)；[\`reconstruct.py\`:277 (line 277)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/reconstruct.py:277)                | writer 已有；selected 預設不寫 | 檔案中實際存在兩種 run；誤差、影格數及 used frames 與執行一致。                              |
| D06 | 檢視時間序列、分布及與結果的關係                                        | pp.4、7      | [\`plot.\_plots\`:197 (line 197)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/plot.py:197)                                                                                                                            | 圖表程式已有；無量測成果            | 八項因素圖與 run 比較圖可讀；原始量測與圖中數值可對應。                                        |
| D07 | 根據證據提出介入、重新重建、比較與解釋                                     | pp.5、7–9、11 | [\`frames_from_sparql_query\`:422 (line 422)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:422)；重建 CLI                                                                                                          | 選取介面已有；分析未開始            | 每項介入都有先前量測依據、明確變更及實際前後結果；不預設一定改善。                                     |
| D08 | Phase 1 使用課程提供的一樓批次並保留資料結構                              | pp.2、8      | `eval/_data/first_floor/`；共用重建流程                                                                                                                                                                                                  | 資料已有；實驗未開始              | 使用提供批次完成首次量測、介入及比較；不以自製資料取代。                                          |
| D09 | Phase 2 自行於二樓擷取，記錄 path、route、frame count               | p.9         | [\`load.main\`:154 (line 154)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/load.py:154)                                                                                                                               | 擷取功能已有；只有環境測試資料         | 正式擷取有可追溯路線、目錄與影格數，並完成相同驗證／重建流程。                                       |
| D10 | 比較兩階段結果、資料品質與擷取決策                                       | pp.2、11–12  | 多實驗比較與報告分析                                                                                                                                                                                                                        | 待執行與分析                  | 以實際量測、截圖、run 表格支持比較，區分觀察與因果推論。                                        |
| D11 | 報告 evaluated frames、retained-frame fraction、runtime 與設定 | p.7、11      | `runFrameCount`、圖表比例已有；無總時間紀錄                                                                                                                                                                                                     | 部分                      | 各數量定義清楚，時間與完整參數可追溯，不把消耗影格數自動當成評估影格數。                                  |

八項因素的個別追蹤如下；正式來源皆為 **PDF p.5，完整性要求見 p.10**：

| 因素                            | 必須來自的實際資料                    | 原始碼位置                              | 目前狀態              |
| ----------------------------- | ---------------------------- | ---------------------------------- | ----------------- |
| `RawPointCount`               | 反投影後、Voxel 前的有效點數            | `utils.py:197–202`；\`api.py:1018\` | 取值敘述與回呼已有，反投影待完成。 |
| `VoxelizedPointYield`         | Voxel 後點數，非比例                | `utils.py:197–202`；\`api.py:1020\` | 取值敘述已有，前處理待完成。    |
| `CoarseRANSACFitness`         | RANSAC `fitness`             | `utils.py:226`；\`api.py:1024\`     | RANSAC 待完成。       |
| `CoarseRANSACRMSE`            | RANSAC `inlier_rmse`         | `utils.py:227`；\`api.py:1027\`     | RANSAC 待完成。       |
| `CoarseRANSACCorrespondences` | RANSAC correspondence set 大小 | `utils.py:228`；\`api.py:1030\`     | RANSAC 待完成。       |
| `ICPInlierFitness`            | ICP `fitness`                | `utils.py:229`；\`api.py:1033\`     | ICP 待完成。          |
| `ICPInlierRMSE`               | ICP `inlier_rmse`            | `utils.py:230`；\`api.py:1036\`     | ICP 待完成。          |
| `ICPInlierCorrespondences`    | ICP correspondence set 大小    | `utils.py:231`；\`api.py:1039\`     | ICP 待完成。          |

上述位置可由 [utils.py (line 197)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:197)、[api.py (line 1015)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:1015) 查閱。

成功標準除了「欄位存在」，還包括**數值確實取自該次粗配準／ICP 結果**。\`Measured\` 是量測狀態，不是品質合格狀態；\`mapMeanL2\` 是 run outcome，不是第九項因素。

**3. Requirements Traceability Matrix：Bonus、英文報告與繳交**

| ID／分類                 | 正式要求                                                            | PDF      | 對應位置／目前狀態                                                                                                                  | 未來驗收條件                                                  |
| --------------------- | --------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| B01／Bonus             | 自製最近鄰搜尋與剛體轉換估計 ICP                                              | p.10     | [\`my_local_icp_algorithm\`:98 (line 98)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/utils.py:98)，待完成、尚未決定是否做 | 由自行實作完成 ICP 核心；不得取代必做 Open3D 後端。                        |
| B02／Bonus 分析          | 與 Open3D 比較重建及時間，解釋方法與取捨                                        | pp.10–11 | 尚無成果                                                                                                                       | 有實際比較、方法說明與時間／準確度證據；未使用的技術不必假稱實作。                       |
| R01／英文報告              | 精簡、英文、PDF                                                       | p.11     | `report.pdf` 尚未存在                                                                                                          | 語言與格式符合；本次不開始撰寫。                                        |
| R02／Implementation    | 說明各步驟、參數、問題、解法與理由                                               | p.11     | 對應 C01–C09                                                                                                                 | 說明符合最終提交程式與真實工作紀錄。                                      |
| R03／Data Verification | 八項量測、measurement settings、source links、失敗案例與調整                  | p.11     | API／Ontology／實驗證據                                                                                                          | 來源連結可供他人理解，數值與案例可追溯；不能只列八個名稱。                           |
| R04／Results           | 兩樓層重建圖、紅黑軌跡、verification plots 截圖                               | p.11     | 結果圖片、\`plot.py\`                                                                                                           | 圖片來自實際成果，清楚呈現軌跡與場景；依報告要求準備去天花板視圖。                       |
| R05／比較表               | Mean L2、Frame Count、Total Execution Time、Tested Hyperparameters | pp.11–12 | 誤差／影格數已有寫入介面；總時間與完整參數不足                                                                                                    | 每次比較都有四項，並補充 p.7 的 evaluated frames 與保留比例。              |
| R06／問題回答              | 無 RANSAC 的 ICP；ICP 穩定性選擇；資料品質／擷取與結果關係                           | p.12     | 無獨立回答模組                                                                                                                    | 三題逐題回答。第一題本身未明文強制額外做一組無 RANSAC 實驗。                      |
| S01／套件                | `<student-id>_hw1.zip`，根目錄直接放指定內容                               | p.12     | 尚未建立                                                                                                                       | 無額外外包資料夾；包含四個入口／核心 Python、Ontology、英文 PDF、README。       |
| S02／完整來源              | 包含 reconstruction 與 verification 使用的全部原始碼                       | p.12     | 另依賴 `plot.py`、\`packages/simulator/\`、設定等                                                                                  | 在乾淨指定環境可重現；額外相依檔案如何打包需釐清。                               |
| S03／排除產物              | 不含實驗 Turtle、診斷產物、Phase 2 資料、Replica 資產或無關建置產物                   | p.12     | 尚未打包                                                                                                                       | ZIP 清單驗查符合；\`ontology/hw1.ttl\` 是指定必交項，不屬被排除的實驗 Turtle。 |
| S04／README、校方規定       | Bonus 註明；遵守校方期限、原創性與格式規定                                        | p.12     | 現有 README 為一般操作文件                                                                                                          | README 對應實際提交；期限與扣分依校方公告，PDF 無統一日期或配分比例。                |

**4. TODO 是否完整涵蓋正式要求**

**演算法範圍大致完整；整份作業範圍不完整。**

必做的反投影、Voxel／normals／FPFH、RANSAC、Point-to-Plane ICP、姿態累積、點雲整合、Mean L2、紅黑軌跡，都能對應 `utils.py` 的 TODO。自製 ICP 已可正式確認為選做，不再是先前僅依註解推定。

但下列事項不會因填完 TODO 自動完成：

- 確認 depth scale 缺欄位的處理契約。
- 讓完整資料真正產生八項因素、合法 seal 及兩種 run。
- 確認 Selected Run 寫入，而非只顯示計算結果。
- 紀錄完整參數、總執行時間、實際評估影格數。
- 兩階段的正式擷取、證據分析、介入、前後比較。
- 場景覆蓋範圍的視覺驗證。
- 英文報告、來源連結、README 與可重現的繳交套件。

此外，\`reconstruct\` Stage 3、4、7、10、12 已有部分呼叫或敘述，不能把每條 TODO 都當作完全空白；也不能只移除 `raise` 就視為完成。

**5. 差異、衝突與應如何處理**

以下「必須修正」指未來必須消除不符合要求的行為或錯誤描述，**不表示本次授權修改檔案**。

| 差異／衝突                      | 核對結果                                                                                                      | 分類                                                    |
| -------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| 標準 ICP 可否使用 Point-to-Point | PDF pp.2–3 的一般介紹允許兩者，但 p.10 評分明列 Open3D Point-to-Plane。摘要採較具體評分要求，正確。                                     | **必須以 Point-to-Plane 滿足必做。**                          |
| depth scale 是否應由 JSON 提供   | PDF p.2 明確要求；實際兩批 JSON 只有 width、height、hfov。writer 也刻意只寫三鍵；\`utils.py:11\` 則有 1000 常數。摘要「等實際可用欄位」弱化了正式要求。 | **摘要需明確標示落差；缺欄位相容方式須確認，不能改動既有資料補鍵了事。**                |
| 自製 ICP 形式                  | docstring 指 Point-to-Point＋Kabsch，TODO 指 Point-to-Plane；PDF 僅要求最近鄰及剛體估計，未指定其一。                            | **使用者決定 Bonus 形式，再統一註解。**                             |
| `z=-depth` 提示              | PDF p.3 使用正的 metric Z 反投影；現有主契約也為 `+Z forward`，負 Z 提示屬另一版本。                                               | **必須統一座標約定，避免重複翻軸。**                                  |
| PDF Selected 指令與寫入行為       | PDF p.8 範例沒有 `--write`；目前程式對 sealed experiment 預設不更新 Turtle。p.10 卻要求 selected run 存在。                     | **必須確保最終有 selected 紀錄；保留 CLI 預設並補明確寫入，或調整行為，留待後續決定。** |
| 介入不限資料篩選，但評分要求 selected    | PDF pp.4–5、8 允許其他介入；p.10 明列 baseline／selected。目前 CLI 只有提供 selection query 才標記 selected。                   | **需向課程確認：純參數介入如何符合 selected 紀錄要求；不能擅自重新定義模式。**        |
| 「全部原始碼」與 ZIP 樹             | p.12 樹未列 `plot.py`、simulator 套件與 YAML，但文字要求所有使用的來源。現有 `api.py explore` 與 `load.py` 依賴它們。                  | **繳交前必須釐清助教是否提供支援檔案、是否允許附加；不可照最小樹打包後假定可執行。**          |
| 因素完整性讀取檢查                  | 先前架構分析／文件容易讓人理解成不完整即拒絕；實際 reader 回傳 `complete=False` 與 errors，未對所有缺漏直接拋錯。                                 | **先前說明需修正；驗收必須明查完整性。**                                |
| RGB／Depth 集合不一致            | 文件說 declaration 拒絕；實際 `_pair_frames` 取交集。                                                                 | **文件描述須修正；驗證不可只看 declaration 成功。**                    |
| 跨缺口 Selected               | `_plan_query_selected` 說明暗示避免跳躍，但實際攤平所有區段，仍配準至前一個被選取影格。                                                   | **註解須與程式一致；是否改處理方式屬使用者的策略決定。**                        |
| 首參考姿態                      | PDF p.4 說每個 capture 的第一相機姿態；骨架以第一個消耗影格為原點。Selected 排除首影格時，兩者可能不同。                                         | **評估前需釐清子集的首參考定義，估計與 GT 必須一致。**                       |
| 時間與完整參數                    | 正式報告要求都有；目前 `_RUN_OUTCOMES` 只有 `mapMeanL2`，Ontology 正式 Parameter 只有 `icpBackend`。                         | **必須建立可追溯紀錄方式；PDF 未強制新增哪些 RDF predicate。**            |
| Bonus 的八項因素                | 缺 fitness／RMSE 會回填 NaN，缺 correspondences 變成 0；文件卻說皆為 NaN。                                                 | **文件須修正；若做 Bonus，需確認比較所需的真實量測契約。**                    |

主要程式證據：[讀取器回傳狀態 (line 550)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:550)、[配對交集 (line 68)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:68)、[選取攤平 (line 29)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/reconstruct.py:29)、[run outcomes (line 2036)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:2036)、[唯一正式 Parameter (line 412)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/ontology/hw1.ttl:412)。

兩份 Markdown 另外應作以下修正或更新：

- 先前架構分析中「沒有正式規格、Phase 定義待確認」已過時；現在已由 PDF pp.2、8–9 確認。
- 摘要將正式繳交樹視為完整清單，卻未指出額外模組相依問題，須補上。
- 摘要正確指出 152／213 是參考圖資料量，不是規定張數。
- 摘要正確指出介入不限篩選、自製 ICP 不取代必做、範例門檻不是評分標準。
- 摘要記載的磁碟空間與之前檢查值不同，屬不同時間的環境紀錄；都不是 PDF 規範，本次未重新量測。

**6. 自動評分與可重現性風險**

PDF p.10 僅說「可能使用自動化評估」，沒有提供隱藏測試、數值容差或最低 Mean L2 門檻。以下是依目前程式推導的風險，不是宣稱老師一定如此測試。

1. **合法 Turtle 不等於符合 Data Integrity。**\
   仍須驗證 declaration、seal、所有因素與兩種 run。\`is_assessed\` 只看 MACHINE marker；\`read_experiment\` 不保證 baseline／selected 都存在。[api.py (line 1597)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:1597)
2. **封存保護宣告文字，沒有保護整個實驗環境。**\
   seal 是宣告文字的 SHA-256；未涵蓋影像、GT、相機 JSON、程式與完整參數。改變資料或 voxel size 後，seal 仍可能通過。[api.py (line 329)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:329)
3. **不能用零、NaN 或空集合代替沒有執行的量測。**\
   reader 的數值檢查接受可轉為 float 的值，NaN／Inf 也可能通過結構檢查。這不代表已符合「實際 pipeline measurement」。正常資料與退化配準應分別檢查，不能把無內點 RMSE 為零解讀為完美配準。[api.py (line 529)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:529)
4. **完整因素數量以預期批次為準，不能悄悄縮小 N。**\
   對 \\(N\ge1\\) 的完整批次，現有架構預期：

   \\[ 2N+6(N-1)=8N-6 \\]

   191 張對應 1,522 筆。若讀取失敗，CLI 仍按原始配對清單要求完整量測，會中止封存；不能偷偷忽略影格再宣稱全批次完整。[reconstruct.py (line 161)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/reconstruct.py:161)
5. **Selected 不能修改原始 baseline 因素證據。**\
   新的子集配對可能跨越原始缺口；原始相鄰 pair 的因素不等於新 pair 的因素。需保留此差異，不能直接把原始 ICP 指標當成 Selected 新配準的量測。
6. **同模式 run 更新會取代舊結果。**\
   同一實驗最多保有目前 baseline／selected 節點；反覆改條件寫同模式會喪失歷次結果，尤其會造成舊因素搭配新參數的解讀混亂。[api.py (line 700)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/api.py:700)
7. **影格數與評估樣本數可能不一致。**\
   `runFrameCount` 取預測軌跡長度；Selected 的 `usedFrame` 卻由要求清單寫入。若跳過影格，可能出現列表與數量不一致；GT 缺列也可能使 evaluated count 更少。[reconstruct.py (line 281)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/reconstruct.py:281)
8. **重現不能只固定一個 seed。**\
   要核對 RANSAC seed 是否真正使用、影格排序、相機參數、實際套件版本及數值後端。PDF 主要支援 Linux，本機是 macOS；參考文獻為 Open3D 0.19.0，本機 0.18.0，這是相容性驗證事項，**不是自動升級理由**。
9. **結果圖片可能與最新數值不同步。**\
   fallback 圖片產生失敗時，CLI 有些路徑只依既有檔案是否存在判斷，可能沿用舊 PNG。未來要檢查圖片確實對應本次 run。[reconstruct.py (line 266)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/reconstruct.py:266)
10. **本機操作成功不等於可攜。**\
    絕對路徑、遺漏相依模組、缺失的 Pixi 測試檔案都會影響乾淨環境驗收。現有 `pixi test` 指向不存在的根目錄 `tests/`，不能拿它的失敗直接判定演算法錯誤。[pixi.toml (line 48)]\(/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/pixi.toml:48)

操作層面仍需保留先前警示：\`clear_existing\` 會刪除指定輸出樹；\`--no-write\` 仍可能寫 PNG；\`explore\` 對已量測實驗會寫 HTML。它們不是唯讀檢查入口。

**7. 未來必須驗證的測試與成功標準**

以下是未來驗收清單，**本次沒有建立或執行測試**。數值容差應依合成案例與執行平台明訂，不冒充 PDF 的隱藏評分標準。

| 測試群組         | 必驗項目                                                | 成功標準                                            |
| ------------ | --------------------------------------------------- | ----------------------------------------------- |
| 反投影          | 已知像素與深度、不同解析度／HFOV、零深度、色彩                           | 三維點符合手算公式；單位只轉一次；無效點排除；點色順序一致；不使用內建 projection。 |
| 前處理          | Voxel、normals、FPFH、空點雲                              | 形狀與數量一致；法向量及特徵有效；退化輸入可明確處理。                     |
| 配準           | 已知剛體變換、初始化、source／target 方向                         | 能恢復合成轉換；旋轉有效；標準路徑確實執行 Point-to-Plane；保留真實指標。    |
| 姿態累積         | 至少三影格、平移加旋轉                                         | 累積順序符合手算；首姿態正確；非只在純平移案例成立。                      |
| 點雲整合         | 相同幾何多視角、\`build_cloud\` 開關                          | 點雲落於共同座標系；開關地圖整合不改變相機軌跡。                        |
| GT 與 Mean L2 | 非零首位置／旋轉、非連續檔名、Selected 子集                          | 同姿態案例誤差近零；已知偏差符合手算；GT 不進入配準；評估列與影格一一對應。         |
| 邊界資料         | 空、缺檔、全零深度、缺 GT、少於足夠配準點                              | 不虛構成功；回傳／錯誤行為明確；不產生假完整的封存紀錄。                    |
| 八項因素         | 每影格兩項、每 pair 六項                                     | 精確對應實際中間結果；總數符合預期；無缺漏、重複、錯誤方向或外來影像。             |
| Turtle／seal  | 序列化往返、修改宣告、run 更新                                   | 可解析；宣告修改被偵測；writer 保留宣告與因素；缺因素、缺 run 另行驗出。      |
| 完整流程         | declaration → baseline → query → selected → explore | 兩個 run 實際存在；選取名單／數量／誤差相符；HTML 與 PNG 對應最新成果。     |
| SPARQL       | 空選取、未知影格、重複、跨缺口、範例邏輯                                | 結果符合查詢意思；空選取不假造 run；跨缺口 metadata 正確。            |
| 重現           | 同資料、程式、參數與 seed 重跑                                  | 影格與因素數相同；數值在事先說明的容差內；保留版本與時間測量範圍。               |
| Phase 1／2 品質 | 軌跡及場景覆蓋                                             | 兩階段都有真實結果、主要空間可檢視；保留比例與覆蓋損失一併解釋。                |
| 圖片／報告資料      | 顏色、座標、去天花板、時間與表格                                    | 紅估計／黑 GT；時間為實測；圖片、表格與 run 條件一致。                 |
| 繳交重現         | 乾淨解壓縮、依賴、根目錄及排除清單                                   | 無本機絕對路徑依賴；可依 README 重現；ZIP 結構及內容符合確認後的規範。       |
| Bonus，若選做    | 自製核心、退化對應、結果與耗時                                     | 不借 Open3D ICP 取代自製核心；有與標準後端的實際比較。               |

PDF pp.7–8 的範例查詢也應做邏輯檢查：第一個 `FILTER NOT EXISTS` 會**排除** `VoxelizedPointYield > 50000` 的影格；第二個排除 `ICPInlierFitness < 0.05` 的影格。它不是「保留高點數」的自然語意，也不是老師指定的最佳門檻。首張沒有前一 pair、非有限值如何參與查詢，都要實際確認。

**8. 仍保留給你決定的選項**

在正式規範範圍內，下列事項尚未選定：

- 是否進行 Bonus，以及自製 ICP 的形式。
- 觀察 baseline 後採用何種介入：影格選取、前處理、配準設定或其他資料使用方式。
- voxel size、對應距離、RANSAC／ICP 收斂條件、是否採用 robust loss，以及測試範圍。
- SPARQL 條件、門檻、保留影格與跨缺口處理策略。
- Phase 2 路線、視角、重疊、影格數與擷取批次。
- 實驗數量、比較組合、重跑次數與取捨分析。
- 總執行時間的計時邊界，以及完整參數／證據的保存方式。
- 要向老師／助教確認的規範歧義：depth scale 缺欄位、純參數介入與 selected 的關係、Selected 首參考姿態、額外相依來源的繳交方式。

必做 Point-to-Plane、手寫反投影、GT 僅供評估、完整因素與封存、Baseline／Selected 紀錄，以及英文 PDF 等，則已由正式規範確定，不再列為可自由省略的選項。