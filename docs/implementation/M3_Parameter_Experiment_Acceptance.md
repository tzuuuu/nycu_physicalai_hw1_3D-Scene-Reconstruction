# M3.2：恢復B0後置作業、B1配準失敗與再次停止紀錄

日期：2026-11-18（臺灣）。**整體未完成，不申請七組實驗驗收通過。** 使用者明確核准「恢復後置作業與剩餘六組」後，已成功完成B0缺少的官方Explore／Query及後置驗證，沒有重跑B0；接著僅啟動B1一次，於70→71發生真實RANSAC零對應失敗。依原定「遇到配準失敗即保留證據並停止」規則，B2與C1–C4均未啟動。

累計新正式重建**嘗試2次、完整成功1次**：B0原先一次完整191張，B1本輪一次中止。沒有增加候選、重試搜尋、跳過失敗配對、修改核心或啟動D／Phase 2／Bonus／英文報告。

原B0序列化停止的完整紀錄已另存 `M3_Parameter_Experiment_B0_Stop_Record.md`；原不完整JSON、原traceback、原 `suite_stopped.json` 與停止後離線審計均原樣保留。本文件更新目前狀態，不把先前失敗從研究紀錄移除。

## 1. 恢復授權、工具與執行順序

本輪新增B級 `scripts/m32_resume.py`，並擴充既有獨立實驗工具的恢復銜接：

- 不刪除或改寫原停止標記；在同一suite另存 `resume_authorization.json`，綁定原suite與停止檔SHA，記錄使用者授權原文及僅剩B1、B2、C1、C2、C3、C4。
- B0缺少的歷史比對、Explore、Query、官方成果快照與完整性證據，存入 `resume_01/B0_postprocess/`。不重新執行原失敗finalize，不覆寫其不完整JSON。
- 後續條件依B0新後置證據放行；B0重建入口仍被拒絕。新失敗寫入 `resume_failed.json`，所有後續條件再次被鎖定。
- 新條件preregistration保存真正執行commit，另保留原suite建立commit。演算法與原始資料SHA不變；只改獨立紀錄／分析工具，未改老師核心、CLI、API、Ontology或依賴。

恢復工具完整測試 **185 passed in 5.54s**，先以 `ac5495f` 提交後才執行。涵蓋既有真實合成RGB-D／正式CLI／Seal／同次觀測／GT時序，以及恢復授權綁定、禁止重跑B0、新失敗停止護欄。

實際命令（工作目錄為專案根目錄）：

```bash
OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/m32_resume.py recover

OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/m32_resume.py run --condition B1
```

`recover`只驗證／分析既有B0證據並呼叫官方 `api.py explore`、`api.py query`。B1透過 `api.py declare` 建立全新workspace，事先登記假說／控制／參數後，經 `record_command.py` 的相同RSS護欄，呼叫既有 `m32_experiments.py observe`；內部執行未修改的正式 `reconstruct.py`：

```bash
.pixi/envs/habitat/bin/python reconstruct.py \
  --experiment experiments/p1_m32_20261118_b_v003_s0_01 \
  --version open3d --voxel-size 0.03 --seed 0 --down-voxel 0.05 --no-vis
```

仍是 `runpy`＋`sys.setprofile` 唯讀call／return觀測，不替換演算法、參數、矩陣或對應點。GT不傳入重建；B1未到正式評估階段，沒有完整Mean L2。

## 2. 七條件比較表與目前可得結果

| 條件 | Registration voxel (m) | Seed | 完整191張Mean L2 (m) | 103→104 RANSAC旋轉誤差 (°) | ICP旋轉誤差 (°) | 狀態 |
|---|---:|---:|---:|---:|---:|---|
| B0／C的seed0 | 0.05 | 0 | **3.174055104788137** | 176.0745043 | 179.7781591 | 原重建完成；本輪補完官方後置流程 |
| B1 | 0.03 | 0 | **無：配準失敗** | 未到達 | 未到達 | 70→71 RANSAC零對應，正式核心中止 |
| B2 | 0.08 | 0 | 未執行 | 未執行 | 未執行 | 依停止規則未啟動 |
| C1 | 0.05 | 1 | 未執行 | 未執行 | 未執行 | 同上 |
| C2 | 0.05 | 2 | 未執行 | 未執行 | 未執行 | 同上 |
| C3 | 0.05 | 3 | 未執行 | 未執行 | 未執行 | 同上 |
| C4 | 0.05 | 4 | 未執行 | 未執行 | 未執行 | 同上 |

B1不是成功的70張子集實驗：它仍宣告完整191張，只是未能完成。**不以部分影格平均取代完整191張Mean L2，不將失敗值填0或移出候選表。** C只有共用B0 seed0，無法提供五seed平均、樣本標準差、中位數或範圍，也沒有挑選最小GT誤差seed。

## 3. B0恢復後置驗證

B0唯一正式重建仍是 `860e842` 版本所執行；本輪 `ac5495f` 僅處理既有結果。

| 核對項目 | 結果 |
|---|---|
| 歷史M2／新B0完整Mean L2 | 均3.174055104788137 m，差0.0 m |
| 八因素與歷史比較 | 1522／1522按官方精度完全相同，0不一致 |
| B0／M3.0相符診斷完整位姿 | 最大逐元素差0.0；歷史位姿來自M3.0，不假稱M2原始CLI保存過位姿 |
| 新B0 Turtle／Seal／因素 | 官方Turtle合法、Seal通過；complete=True、expected=measured=1522、pending=0、errors=[] |
| B0 Run | 唯一FullBatch baseline、191張、儲存mapMeanL2=3.174055；沒有Selected |
| 官方Explore | 退出碼0，5.324861 s；dashboard、timelines、distributions、tradeoff四份HTML實際產生 |
| 官方Query | 退出碼0，精確取得1..191、無重複／遺漏；未變更Turtle |
| B0重建呼叫累計 | 仍1次，沒有本輪重跑 |
| 原B0失敗JSON與停止證據 | SHA不變，沒有修補／覆寫 |

上表「Turtle」指本機正式語意實驗檔。B0歷史比對與新後置完整性位於 `research_outputs/m32_20261118_suite_01/resume_01/B0_postprocess/`；原始B0研究目錄新增的 `analysis/` 是重建後離線分析，非重建重跑。

103→104局部結果仍為：RANSAC平移誤差1.3521388050 m／旋轉176.0745043127°；ICP平移0.9469599292 m／旋轉179.7781591207°。190對中，粗／細旋轉誤差>150°及>90°皆只有該對。全域最大L2在160為10.6976822192 m，末張5.7959826609 m。B0沒有改善翻轉。

## 4. B1的實際失敗與部分證據

正式核心錯誤：

```text
RuntimeError: RANSAC failed for 70->71: fitness=0.0, RMSE=0.0, correspondences=0
```

失敗發生於 `utils.py:409` 既有有效性檢查，並非本次工具JSON異常或RSS超限。當次console在70→71標記後記錄：mutual filter只保留6369個互惠候選，Open3D回退原匹配集合。此警告與失敗有同次配對關聯，但**尚不足以證明回退是唯一原因**。

| 70→71實際量測 | B0：v=0.05 | B1：v=0.03 |
|---|---:|---:|
| 第70張RawPointCount | 262144 | 262144 |
| 第71張RawPointCount | 215448 | 215448 |
| 第70張VoxelizedPointYield | 24837 | 62331 |
| 第71張VoxelizedPointYield | 31947 | 80385 |
| RANSAC Fitness | 0.9797477071 | **0** |
| RANSAC Inlier RMSE (m) | 0.0360172955 | **0，零對應時無有效殘差，不是完美配準** |
| RANSAC Correspondences | 31300 | **0** |
| ICP Fitness（B1未接受） | 0.9979966820 | 0.9815637246 |
| ICP RMSE (m；B1未接受) | 0.0260294204 | 0.0197792464 |
| ICP Correspondences（B1未接受） | 31883 | 78903 |

現有核心先執行ICP，再一起檢查粗／細結果。RANSAC失敗時返回的初值為單位矩陣，因此ICP曾從該返回初值計算出上述數值；**這不是工具插入的備援初值，也不代表正式配準已成功**。核心隨後拒絕RANSAC結果，沒有把70→71的ICP矩陣累乘到正式軌跡。沒有跳過該對、採用ICP結果接續或改寫矩陣。

部分觀測：71個frame events、70個pair return events；已接受69對，對應影格1..70的軌跡前綴。return觀測含最後被拒絕的一對，故其562筆原始因素值（71×2＋70×6）**不是完整1522筆正式Turtle因素**。沒有拿它們封存成成功實驗。

B1沒有重建正常返回的 `positions.npy`、完整191個位姿、正式評估、合併地圖輸出、PNG、Seal或Baseline Run。唯讀審計另從前69對原矩陣推導70個前綴位姿，明確命名 `offline_accepted_prefix_poses.npy`；沒有求新轉換、讀GT補正、續跑重建或把失敗對加入軌跡。

## 5. 參數與資源消耗

B1除了規劃指定的registration v與其連動量，其他設定均固定：v=0.03 m使normal radius=0.06 m、FPFH radius=0.15 m、RANSAC驗證／Distance Checker與ICP距離皆0.045 m；normal max_nn30、FPFH max_nn100、mutual=True、edge0.9、n3、RANSAC100000／confidence0.999、ICP Point-to-Plane／100／兩容差1e-6。map down_voxel=0.05、build_cloud=True、ceiling margin=1、seed0、OMP_NUM_THREADS=1。

來源資料、內參、深度換算、核心SHA與套件版本皆與M2相同，實際呼叫引數與preregistration保留完整1..191清單。

| 資源／成果 | B0完整成功 | B1失敗嘗試 |
|---|---:|---:|
| 正式子程序總時間 (s) | 305.895459083 | 290.755402875 |
| 純reconstruct wall time，含觀測 (s) | 293.751107208 | 無：異常中止未正常返回 |
| CLI觀測區間CPU user (s) | 291.937289 | 275.254486 |
| CLI觀測區間CPU system (s) | 2.855139 | 3.035104 |
| 程序峰值RSS (bytes／GiB) | 926892032／0.863235 | 520257536／0.484528 |
| 0.5秒取樣峰值RSS (bytes) | 925548544 | 513277952 |
| RSS護欄 | 3 GiB，未觸發 | 3 GiB，未觸發 |
| 子程序退出碼 | 0 | 1 |
| 正式地圖點數 | 2725240 | 無完整地圖 |

B0時間仍為原重建時間，恢復Explore的5.324861 s另外列示，沒有混入重建時間。B1只跑到第71張，故不能用290.76 s／0.485 GiB與完整B0直接宣稱更快／更省資源；尚未執行條件沒有資源量測。CPU不含子程序啟動前的所有成本；RSS為子程序高水位與取樣值，並非完整系統記憶體。

## 6. 敏感度解讀與下一步建議

1. **觀察到的新硬失敗**：v=0.03、seed0在70→71不能產生有效RANSAC結果，而v=0.05、seed0可完成此對與完整批次。這是固定候選的一次實驗結果，足以否定「更細voxel必然使本pipeline更穩定」，不能推出所有0.03執行或其他seed都失敗。
2. B1前71張與B0相同影格的RawPointCount逐筆一致，voxel後點數加總約2.4690倍；更多點並未確保有可接受的粗配準。因normal／FPFH支撐與幾何門檻同時改變，無法獨立歸因於點密度、特徵半徑、互惠回退或更緊距離。
3. B1未到103→104，因此**無法回答0.03能否避免原翻轉**。B2未跑，沒有完整尺度敏感度比較。C未新增seed，沒有seed穩定性結論，不選GT最低seed。
4. **目前不建議直接啟動D**。沒有跨seed或早停次數證據支持「confidence不足」是新失敗或原翻轉的主要原因；增加預算也不能保證排除幾何對稱錯解。D仍需另行核心修改核准，本輪未做。
5. 原M2／M3.1已提供合法完整baseline／selected及負面介入證據。若研究時間有限，可由使用者決定結束Phase 1並接受已知品質限制；但本次未完成B＋C，不能以「七組均驗證」為由建議轉Phase 2。若要續做B2與C，需明確決定是否在保留B1失敗的前提下放行剩餘五組；目前仍按原停止條件鎖定，沒有自行略過B1繼續。

## 7. 來源與Turtle保全

| 核對項目 | 結果 |
|---|---|
| 原suite受保護檔案 | 553個SHA皆未變 |
| 恢復前既有檔案 | 613個SHA皆未變，包括原B0失敗JSON、停止檔及舊審計 |
| B1開始前所有受保護檔案 | 642個SHA皆未變，包括恢復完成的B0圖表／分析 |
| 原capture整體來源SHA | `22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`，與M2相同 |
| 原M2／M3.1 | 核心、Turtle、Seal、baseline／selected、地圖與圖表保留 |
| B0本輪後置Turtle SHA | `def5c42211c0e38be6d59335200c1fe6337e786c6148ecc9e04d10f2f0ae1629`，Explore／Query不改變Turtle |
| B1 Turtle | 可讀的事先宣告，bytes與執行前相同；未封存，無虛假baseline／selected或補填因素 |
| 原停止與新停止 | 原 `suite_stopped.json` 保留；新 `resume_failed.json` 記錄B1失敗並鎖定後續 |

## 8. 產物與圖表

| 專案根目錄下位置 | 內容 |
|---|---|
| `research_outputs/m32_20261118_suite_01/resume_authorization.json` | 明確恢復授權、原suite／stop SHA、原條件與版本來源 |
| `.../resume_01/B0_postprocess/` | 有效歷史比對、完整性、官方Explore／Query紀錄、B0正式成果快照；本表`...`為同suite |
| `research_outputs/m32_p1_m32_20261118_b_v005_s0_01/analysis/` | 本輪補成的B0逐幀／逐對CSV、完整191張誤差圖與離線摘要 |
| `experiments/p1_m32_20261118_b_v005_s0_01/plots/` | 四份真正官方Explore HTML；原M2/M3.1 plots沒有覆寫 |
| `experiments/p1_m32_20261118_b_v003_s0_01/` | B1未封存宣告、唯讀audit query；不冒充完成的正式實驗 |
| `research_outputs/m32_p1_m32_20261118_b_v003_s0_01/` | B1preregistration、資料／核心SHA、declare、單次執行標記、command／RSS、實際引數／配對、部分事件／矩陣、traceback |
| `research_outputs/m32_20261118_resume_failure_audit_01/` | 唯讀失敗審計、562筆部分觀測、未接受的失敗對原矩陣、70張已接受前綴的離線位姿、SHA manifest |
| `.../B1_partial_failure.png` | 同資料前71張voxel點數對照與B1 RANSAC Fitness／對應數失敗位置；本列`...`為失敗審計目錄 |

B0完整逐幀／局部誤差圖與B1部分失敗圖均已實際檢視。B1圖標明部分序列與原生門檻差異；不將該圖稱為完整191張精度比較。尚無完整B或C比較圖／七組Mean L2；所有未知與未執行項均明列。

## 9. Git與驗收停止點

- `860e842`：原始觀測工具與真正B0執行版本。
- `737a681`、`57ca8b6`、`ad68925`：原B0序列化修正、唯讀審計與原停止紀錄，歷史保留。
- `ac5495f`：本輪恢復工具、授權銜接與測試；真正B1執行版本，也記錄於其preregistration。
- `9176a57`：唯讀失敗審計／兩項合成測試及B1 query；另以docs commit保存本驗收更新與原B0停止紀錄備份，不將大型產物加入Git。

新增失敗審計只分類保存的回傳結果，不呼叫配準；合成測試確認「ICP有結果不代表可接受失敗RANSAC」及「失敗後不可續接」。恢復前完整185項測試通過，新增失敗審計後完整測試 **187 passed in 5.04s**。Git保持main、無remote、不改寫歷史、原snapshot不變，`git diff --check`通過。

**本輪依真實配準失敗停止。B0後置恢復完成，B1負面結果保留，B2與C1–C4未啟動；等待人工驗收與下一個明確決策，不自行開始D、Phase 2、Bonus或英文報告。**
