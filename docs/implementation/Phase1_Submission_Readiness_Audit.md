# Phase 1 Submission Readiness Audit — F1前置完整性停止

日期：2026-11-19（臺灣）。**F1未完成，F2／F3未啟動，不標示Phase 1 Final Closeout完成。** 本次先讀老師13頁原PDF、Snapshot與既有驗收／程式來源，再進行唯讀SHA核對；發現第三個未核准中繼檔路徑異動，依本次停止規則停止。沒有修復核心、修改排除政策、產生報告圖片、重跑配準、擷取Phase 2、撰寫英文最終報告或建立ZIP。

## 1. 權威來源與已完成的閱讀

最高依據為`docs/assignments/HW1_3D Scene Reconstruction.pdf`（13頁）；全文已抽取閱讀，實際渲染並檢視第12頁Submission。PDF pp.2–5規定重建、GT及八因素，pp.6–8規定正式工作流程，pp.10–11規定Point-to-Plane／Data Integrity／圖表與報告，p.12 §5.1規定ZIP。

已檢視`main`及`snapshot/pre-implementation`的核心差異、現有核心與相關測試、README、Pixi、config／simulator相依，以及M1、M2前置／正式、M3.0、M3.1、M3.2驗收與研究計畫。M0／初始需求的依據為`docs/assignments/`中的架構分析、規範對照、需求矩陣與交接規劃，沒有假稱存在獨立的`M0_Acceptance.md`。

最新M3.2的`resume_04/final_provenance.json`、`final_scientific_audit.json`、`closing_preservation.json`及歷史停止鏈已檢視；不重新呼叫已停止的M3.2 `verify`或`finalize`。歷史文件中的「尚未實作／未執行」以各文件當時階段解讀，不覆寫成今日狀態。

## 2. 阻擋項：第三個未授權SHA差異

歷史依據：`research_outputs/m32_20261118_suite_01/resume_04/protected.before.json`，899項。

|項目|實際結果|
|---|---|
|差異路徑|`research_outputs/m32_20261118_suite_01/.DS_Store`|
|歷史SHA-256|`801b6bba5acfd71c5a5d0fc36442c2258c75108455f431f021d66029c24e1fb9`|
|目前SHA-256|`3dc8cb90f936202424e02d95fe4db736e45d7fe2b05ae4b4675c91b6aa0268db`|
|檔案狀態|既存一般檔案，`file`辨識為Apple Desktop Services Store|
|核准例外？|否；不可把它等同於`research_outputs/.DS_Store`|
|899項清單差異|僅此一路徑；其餘898項相符|
|M3.2最終產物manifest|79項全數相符|
|本次起始清單|1888項；本次唯讀稽核期間未發現其中任何檔案異動|

原護欄實際拋出：

```text
RuntimeError: Protected files changed: ['research_outputs/m32_20261118_suite_01/.DS_Store']
```

本次沒有發現上述清單範圍內的額外科學產物損壞；但**未授權的OS中繼檔仍使既有完整性政策失敗**，不能自行排除、刪檔、復原或更新歷史SHA來放行。新的1888項當下清單只供保全，不能取代歷史接受值或消除既有差異。不推測變更時間與寫入來源。

已另存`research_outputs/phase1_closeout_audit/`：

- `F1_stopped.json`：真實差異、存在狀態、原／新SHA、未開始F2／F3及未重建等狀態。
- `F1_failure.traceback.txt`：此次原始護欄Traceback。
- `unapproved_suite_DS_Store_current.bin`：目前檔案bytes；未持有的最早原始bytes不能由SHA還原。
- `protected.before.json`、`metadata_checks.jsonl`：起始保全與兩個已核准精確路徑的檢查紀錄。
- `authorization.md`：本次Closeout原始授權。
- `audit_attempt.py`：本次唯讀稽核腳本原樣保存。原腳本於`scripts/`啟動，停止後移置此處作執行來源證據；未作為已完成、已測試的正式工具提交。

## 3. PDF符合性與必做程式碼矩陣（停止前靜態盤點）

下表區分「看到實作及既有證據」與「本次F1完整驗收」。因SHA護欄先行停止，未執行本次完整測試或後續機器化逐項驗收；不能將既有235項通過改稱本次新測試結果。

|要求／原始TODO|PDF頁|目前位置|停止前觀察與既有證據|本次未解決事項|
|---|---|---|---|---|
|手寫Pinhole Back-projection|2–3、10|`utils.py:18`、`_read_rgbd:285`|NumPy網格、有效深度、公尺換算、手算XYZ；既有`test_depth_unprojection.py`、`test_capture_inputs.py`|本次回歸未跑；原capture缺明示depth_scale，沿用已核准毫米契約須於報告揭露|
|Voxel Downsampling|2–3、10|`utils.py:104`|Open3D voxel_down_sample；既有`test_point_cloud_preprocessing.py`|本次逐項驗收未完成|
|Normals與FPFH|3、10|`utils.py:127`、`:136`|2v／30鄰點、5v／100鄰點；既有前處理測試|本次逐項驗收未完成|
|RANSAC Global Registration|2–3|`utils.py:149`、`:380`|FPFH真實配準、固定seed與幾何checker；既有`test_registration.py`與正式紀錄|來源guard停止，未執行新配準|
|Open3D Point-to-Plane ICP|3、10|`utils.py:162`、`:195`|Point-to-Plane、100次上限、粗配準初值；既有配準測試|本次回歸未跑|
|Pairwise Transform／Trajectory Composition|3–4、10|`utils.py:398`、`:412`|current→previous，右乘累積；既有`test_reconstruction.py`|本次逐項驗收未完成|
|Scene Map Reconstruction／去天花板|2–4、11|`utils.py:448`、`:234`、`:471`|地圖副本整合與原ceiling helper；正式PNG已存在|圖片視覺驗收屬F2，未啟動|
|Mean L2／首相機／GT僅評估|4、10|`utils.py:478`|float64、固定軸向／原首姿態、無最佳擬合；既有`test_trajectory_evaluation.py`|本次完整來源驗收未完成|
|紅估計／黑GT軌跡|2、10–11|`utils.py:573`、`:584`、`:611`|LineSet與PNG fallback可見指定配色；既有軌跡測試|本次圖片驗收未啟動|
|八項Pipeline-grounded Factors|5、7、10|`utils.py:371`、`:414`；`api.py:1000`|真實callback與RegistrationResult；既有完整1522因素紀錄|本次因素隔離／逐筆驗證尚未完成|
|Baseline／Selected流程|7–8、10|`reconstruct.py:121`起、`:212`起；`api.py:638`|M2與M3.1已有正式Baseline／Selected，負面結果保留|本次Canonical RDF子圖核對尚未執行完成|
|Declare／Explore／SPARQL／Seal|4–8、10|`api.py:847`、`:2258`、`:2221`、`:340`、`:1560`|API來源及歷史正式產物可追溯|本次API載入與Ontology驗收尚未完成|
|Optional Bonus ICP|10–11|`utils.py:208`|`my_local_icp_algorithm`保留NotImplementedError；未選做|不是必做程式碼缺漏；本次不實作|

**靜態檢視未發現必做TODO仍以NotImplementedError阻斷；不能在F1未完成時保證全部必做程式碼已完成最終驗收。** 原TODO註解仍保留，不能只搜尋TODO字串就判未實作。API `declare`產生的敘述TODO屬各實驗預測，不是演算法缺漏。

## 4. Snapshot差異與CLI相容性

Snapshot固定為`291209750bd8ecf84f337112c9b92307e6be192a`；本次起始main為`27e5c614533385c4d1deee3c0d302e2c54b58a36`。

|範圍|相對Snapshot的既有差異|分類|
|---|---|---|
|`utils.py`|280行新增、7行移除；必做TODO實作、capture讀取helper與必要驗證|既有A級實作，提交6a8121a至1922c1c可追溯；本次不修改|
|`reconstruct.py`|10行新增、1行移除；math、旗標驗證及兩處參數傳遞|已核准C級修改`32c1e7d`|
|`api.py`、`load.py`、`plot.py`、`ontology/hw1.ttl`、`pixi.toml`、`pixi.lock`|與Snapshot無差異|本次未修改|
|`scripts/`、`tests/`、驗收MD、可重現.rq|獨立研究／測試／紀錄新增|B級輔助，不取代正式CLI|

`--down-voxel`預設None，正有限數驗證，首次與sealed／Selected呼叫皆傳入utils；省略時保留原地圖行為，registration voxel／seed預設未變。既有`tests/test_cli_down_voxel.py`涵蓋三路徑的None／0.05、非法值及真實合成Pipeline不變性；本次未重跑，無新CLI變更。

## 5. Ontology、正式Turtle與實驗隔離（未完成驗收）

`ontology/hw1.ttl`是教師TBox定義檔，PDF p.12明確必交；`experiments/<name>/<name>.ttl`是各實驗宣告／量測／run紀錄，PDF p.12明確排除於ZIP。不得將後者合併入前者。

Ontology與原Snapshot無差異，原碼可見Batch、Frame、Experiment、ReconstructionRun、Factor／SingleImageFactor／DepthPairFactor、必要Properties及八項QualityFactor定義；現有API提供RDFLib載入、因素與參數讀取。既有正式執行已通過載入，但本次F1在SHA核對停止，尚未重新完成語法／API驗收，不宣稱新增通過。Ontology註解的write-once敘述與CLI可寫Selected／sealed run的行為差異為既知限制；不在本次修改。

最新M3.2 manifest 79項相符，支持既有驗收與科學審計產物仍未變。歷史證據記錄：

- M2 Baseline 191張、3.174055104788 m；M3.1在同workspace新增190張Selected、4.200397987246 m。
- 新增Selected使全TTL SHA預期改變，須比對原Declaration／Seal、Baseline子圖與排除Selected後RDF，不可要求其全檔SHA等於M2最初版本。
- M3.0是相符診斷執行，未保存正式M2原同次位姿／完整點雲；不可把診斷來源或B0地圖冒充原M2保存點雲。
- B0／B1／B2／C1／C2／C3／C4有各自workspace；B0與C組seed0共用一次run。B1未封存、無完整地圖；C2原finalize停止與新審計成功須分開保留。
- 既有M3.2收尾重複verify的FileExistsError停止也保持；本次沒有再次執行該入口。

以上為已讀歷史證據與SHA保全結果，**尚不是本次完整的workspace／run／因素隔離驗收**。

## 6. ZIP相依靜態分析與README待辦

|類別|項目|判定|
|---|---|---|
|A：PDF明確必交|`load.py`、`reconstruct.py`、`utils.py`、`api.py`、`ontology/hw1.ttl`、`report.pdf`、`README.md`|ZIP根目錄直接放指定結構，不多包一層|
|B：正式執行相依|`plot.py`|`api.py:2299`的explore會匯入plot；僅複製示意四個py不足以提供完整Explore|
|B：正式擷取相依|`packages/simulator/`及其pyproject、`configs/second_floor.yaml`|load.py延後匯入simulator並使用default config；`--help`可成功不代表完整擷取相依齊全|
|B：環境相依|`pixi.toml`／`pixi.lock`、其中引用的`dependencies/habitat-lab/habitat-lab`本機來源|目前使用兩個editable path；若省略而仍使用原設定，環境建立可能缺路徑，須確認打包／外部取得方式|
|B／待助教確認|SPARQL `.rq`來源|Selected可重現需要query原始碼；不需夾帶生成TTL。是否允許保留experiments下純queries或改放獨立來源目錄需確認|
|C：研究輔助|獨立研究／繪圖scripts、測試、驗收文件|不全是正式CLI必要相依；依報告來源需求與助教格式決定，不自動全包|
|D：明確排除|生成Experiment Turtle、diagnostics／報告PNG素材、Phase 2 Capture、Replica資產、build／cache／本機環境|不納入正式ZIP；必要圖嵌入report.pdf不等於將原始診斷目錄一起打包|

第三方套件包括NumPy、Open3D、OpenCV、SciPy、Pillow、RDFLib，以及Explore的Panel／Bokeh；capture另需Habitat-Sim／Magnum、simulator與相關設定／相依。環境檔應作重現來源，不打包`.pixi/`二進位環境。PDF以「全部必要原始碼」補充示意清單，但沒有明定第三方editable tree與額外目錄的具體格式，須向助教確認，不能假定可任意增刪。

README目前是一般環境／擷取／Declare→Reconstruct→Explore指南，尚需最終繳交版本補齊：保留首影格的Selected query與`--write`實際命令、原始資料取得與放置、map-only down_voxel與固定版本、Phase 1來源與限制、Optional Bonus未實作、必要額外相依與乾淨環境重現步驟、報告與素材位置及排除清單。README指向的docs若未打包也需處理。`pixi.toml`的test任務仍指向不存在的三個舊測試檔案；這是既有測試入口／準備度問題，不是已發現的演算法TODO缺漏，本次不修改。

`report.pdf`與Phase 2成果依本次限制尚未製作；ZIP不可能在此時視為可直接繳交。原計畫的暫存目錄最小來源Import／CLI測試，因F1完整性護欄先停止而未執行。

## 7. 階段驗收、測試與停止

- F1：前置SHA停止；保留本文件與獨立停止證據，尚未完成全部驗收矩陣的動態核對。
- F2：未啟動，`research_outputs/phase1_report_assets/`未建立；沒有圖片或英文Figure Caption的新成果，也沒有視覺驗收聲稱。
- F3：未啟動，`Phase1_Final_Handoff.md`未建立；不以不完整證據宣告Handoff Complete。
- 本次沒有執行新測試或正式重建。既有235 passed in 6.82s僅為先前M3.2紀錄。
- 已核准例外仍精確限定`experiments/.DS_Store`與`research_outputs/.DS_Store`；其程式及測試未修改。
- 保持main與原Snapshot；只提交本F1停止稽核MD，研究保全產物維持忽略；無大型產物入Git。

**需人工決定第三個精確路徑差異的處理方式，才能另行恢復F1；本次不擴大授權、不進入F2／F3或Phase 2。**
