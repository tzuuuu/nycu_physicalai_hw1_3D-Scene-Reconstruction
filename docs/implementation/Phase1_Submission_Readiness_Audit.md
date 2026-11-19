# Phase 1 Submission Readiness Audit — F1恢復驗收

日期：2026-11-19（臺灣）。**F1程式碼／研究資料稽核完成；未發現必做演算法缺漏或正式成果損壞。最終ZIP尚未就緒。** 剩餘項目屬README、相依打包安排、助教確認及Phase 2／報告待辦，依本次授權可接續F2與F3。未修改教師核心、Ontology、Pixi或正式資料，未進行新的正式配準。

## R1. 恢復授權與歷史保全

三個精確OS中繼檔路徑為`experiments/.DS_Store`、`research_outputs/.DS_Store`、`research_outputs/m32_20261118_suite_01/.DS_Store`。新增第三路徑的功能必須明確傳入授權SHA及精確清單；舊兩路徑流程不會自動擴大，預設`verify_hashes`仍嚴格比對。每次記錄路徑、原／目前SHA、存在狀態、一般檔案／符號連結狀態及授權SHA；缺檔、目錄、符號連結、第四路徑與科學檔案差異仍停止。未刪除、復原或修改任何`.DS_Store`。

政策先寫失敗測試再實作，46項相關測試通過後以`3b9d687`獨立提交。新紀錄位於`research_outputs/phase1_closeout_audit/resume_01/`，`authorization.json`引用原`F1_stopped.json`、Traceback、原manifest／provenance與bytes保全的SHA。第三路徑歷史SHA `801b6bba5acfd71c5a5d0fc36442c2258c75108455f431f021d66029c24e1fb9`及停止時SHA `3dc8cb90f936202424e02d95fe4db736e45d7fe2b05ae4b4675c91b6aa0268db`皆保留；本次逐次SHA另存日誌，不回寫歷史值。

原部分稽核全文另存`resume_01/F1_partial_audit.before.md`且以SHA綁定，原停止證據完全保留。以下舊部分內容亦以歷史區段保留。

## R2. PDF符合性與必做程式碼最終矩陣

權威PDF、Snapshot及主要來源已於前次F1閱讀；本次依同一未變更核心與實際資料完成核對。頁碼採PDF印刷頁碼（共13頁）。

|必做要求／TODO|PDF|現有程式|本次證據與結論|限制|
|---|---|---|---|---|
|手寫Pinhole反投影／深度尺度|2–3、10|`utils.py:18`、`:285`|合成反投影、shape／色彩／單次尺度換算測試通過；未用Open3D投影替代|原內參未明示scale，沿用既有毫米編碼，須報告揭露|
|Voxel Downsampling|2–3、10|`utils.py:104`|真實Open3D合成前處理測試通過|地圖降採樣不等於配準尺度|
|Normals／FPFH|3、10|`utils.py:127`、`:136`|2v/30、5v/100與特徵／法向量測試通過|存在特徵不保證幾何可辨識|
|RANSAC粗配準|2–3|`utils.py:149`、`:380`|真實合成配準測試、既有正式190對觀測／八因素核對|本次沒有對一樓重跑配準|
|Open3D Point-to-Plane ICP|3、10|`utils.py:162`、`:195`|指定估計器、初始化、法向量、有限值及零對應測試通過|不是Optional自製ICP|
|逐對變換／軌跡連乘|3–4、10|`utils.py:398`–`:444`|受控矩陣組合、真實合成Pipeline與正式位姿證據通過|current→previous右乘；不以GT補正|
|場景整合／去天花板|2–4、11|`utils.py:448`、`:234`、`:471`|真實合成建圖、map副本不影響位姿／因素；正式PNG保全|實際涵蓋率不由點數推定|
|Mean L2／固定首相機／GT僅評估|4、10|`utils.py:478`|非零首姿態、非連續編號、缺GT、已知偏差與整合測試通過|無最佳旋轉／平移／尺度擬合|
|紅估計／黑GT|2、10–11|`utils.py:573`、`:584`、`:611`|LineSet配色測試與合成PNG通過；正式來源SHA不變|F2才進行新圖視覺驗收|
|八項真實Pipeline因素|5、7、10|`utils.py:371`、`:414`；`api.py:1000`|六個M3.2完成條件各1522筆且與同次觀測相符；M2因素保持|B1無完整封存；Selected新對因素另存，不冒充Baseline因素|
|Baseline／Selected|7–8、10|`reconstruct.py:121`、`:212`；`api.py:638`|M2原Baseline子圖及排除Selected後RDF雜湊與加入前相同；Selected精確190張排除104|M3.2每個新條件為自己的FullBatch，非假造Selected|
|Declare／Explore／Query／Seal|4–8、10|`api.py:847`、`:2258`、`:2221`、`:340`、`:1560`|既有正式Turtle經API解析；Seal、因素完整性與Query測試通過|不重跑Explore覆寫舊plots|
|Optional Bonus|10–11|`utils.py:208`|唯一保留NotImplementedError為`my_local_icp_algorithm`|未選做，非必做缺漏|

完整測試 **247 passed in 16.18s**，包含現有小型合成RGB-D／RANSAC／ICP回歸與新增精確政策測試，均在暫存測試資料上；沒有對正式191張Capture執行配準、Declare或重建。命令與輸出保存於`resume_01/tests.log`。老師原始utils註解經token序列核對全部逐字、依序保留；保留TODO字樣不是未實作證據。

`--down-voxel`現有13案測試通過：省略None／0.05在首次、sealed Baseline與Selected皆正確傳遞；非法值先拒絕；map-only取樣不改位姿、八因素或Mean L2。相對Snapshot的差異仍僅已核准`32c1e7d`的10行新增／1行移除；其餘公開CLI預設未變。utils的280新增／7移除屬既有必做實作與helper；api、load、plot、Ontology、Pixi與Snapshot相同，本次未改。

## R3. Ontology、實驗隔離與SHA結論

Ontology RDF/Turtle解析成功，共313 triples、16個明示Class、46個明示Property；API精確載入八個QualityFactor定義與一個`icpBackend`參數。`ontology/hw1.ttl` SHA仍為`4a3d52dd838d8feae9bba042ca9bcd594e7f4de081fbdbaa3bbc290a84339258`，與Snapshot完全相同，可保留原檔作為未來ZIP的必交項；**這不等於整包ZIP已可繳交**。

原教師TBox中`QualityFactor`、`appliesTo`、`overProperty`被引用但沒有獨立主詞宣告；現有解析／API及全部正式成果正常，PDF沒有逐名要求新增這三個宣告。本次不自動視為必做程式碼缺漏，也不修改Ontology；若助教要求更嚴格封閉詞彙檢查，須另行確認。原註解宣稱sealed不可重跑，與API可寫Selected／sealed run的既有行為差異同樣保留為限制。

- 原Capture仍精確191組，GT header=(191,7)，SHA `22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`；教師核心與鎖定環境SHA與原suite一致。
- 原M2／M3.1 TTL目前SHA `bba92ffc4a031772a8b1b6bc80dc3056b0c103a1b0382784c3c82d4edc3eb4b6`。加入Selected前後Declaration／Seal皆`3306cd6f0729b45b9583edcf31772df314b18347487621dc1b2eec84c8e09ab5`；Baseline子圖皆`ebf1bc5d48ad83ac86d8def01dd96993454295558638b1cf6de9fa627af1805b`；排除Selected後RDF皆`ea7828f4427bf18873e69a449181b2dd1906f136b3b768916ff3b7097c3ad8af`。
- Baseline仍191張／儲存Mean L2=3.174055；Selected精確1..191排除104、190個usedFrame／儲存4.200398。原始float64值與共同190張比較見M3.1驗收，沒有把序列化精度差異當作不一致。
- B／C六個完成條件皆191張、1522因素、有效Seal，與同次return觀測逐筆相符；各自的Factor occurrence集合互斥。B1仍原未封存宣告／配準失敗；B0共用C seed0，無重複run。
- 最新M3.2 79項manifest、899項前置清單在三個精確例外範圍下通過；本次1898項起始來源檔案於F1前後保持。M3.0診斷、M3.1證據與全部歷史停止／授權包含在保全中。
- M3.2最後收尾FileExistsError停止仍保留；C2原finalize失敗與補充科學審計通過仍分開記錄。未呼叫舊恢復入口解除停止或補造receipt。

機器化結果：`resume_01/F1_audit.json`、`ontology_vocabulary_notes.json`與`metadata_checks.jsonl`。原兩路徑之外的第三路徑是本次明確新增授權；沒有第四路徑放寬。

## R4. ZIP與README準備度：仍有未解決事項

PDF p.12 §5.1明確要求根目錄含四個Python、Ontology、report.pdf與README，並要求全部必要原始碼；排除生成Experiment Turtle、diagnostics、Phase 2 Capture、Replica及無關建置產物。**Ontology TBox必交、生成實驗TTL排除，不能用全域*.ttl規則刪除Ontology。**

|分類／項目|本次實證|處理方案與影響|狀態|
|---|---|---|---|
|A：PDF明列七個檔案|原始PDF p.12已檢視|維持根目錄示意、不多包外層資料夾|格式已釐清；report.pdf尚未撰寫|
|B：`plot.py`|在暫存最小來源目錄`import plot`實際ModuleNotFoundError；加入plot後api／utils／plot可匯入、API載入8因素|額外包含原plot.py，否則Explore不完整；不需改API|確定必要，相依打包待核准|
|B：simulator／configs|load.py延後匯入simulator並使用config；`load --help`可成功但不代表可擷取|保留packages/simulator（含pyproject）與configs，或另訂經核准的取得步驟|Phase 2及ZIP安排待辦|
|B：Pixi本機editable|pixi.toml引用packages/simulator及dependencies/habitat-lab/habitat-lab|需保留來源tree或另行核准調整安裝方式；不得只省略路徑|環境／第三方來源打包待助教確認|
|B：SPARQL .rq|Selected重現依賴真實查詢原始碼|可提案保留純queries或移至獨立來源目錄；不可夾帶生成TTL|額外目錄格式待助教確認|
|C：研究scripts／tests／MD|非全部都是原CLI的執行相依|依source links／重現需求列清單，不整包研究目錄|最終清單待核准|
|D：生成產物|正式TTL、PNG、HTML、NPY、診斷與本機環境|PNG素材供嵌入report.pdf，不直接附整個資產目錄；不打包.pixi|明確排除|
|README|一般安裝／擷取／Declare→Explore指南仍可讀，但未涵蓋最終提交|補Selected --write、query、資料放置、版本／map voxel、未做Bonus、相依與排除清單；本次只列待辦|未完成，不標通過|
|Pixi test task|現有task指向三個不存在的舊測試檔案|提案改用實際pytest入口；會修改Pixi，須另核准。本次使用python -m pytest成功247項|既有設定缺陷保留，未修|
|Ontology詞彙註記|三個用詞未獨立明示宣告，但API與Snapshot一致|若助教要求schema嚴格化，須另核准，不能擅改|確認事項保留|

暫存最小來源`reconstruct.py --help`、`load.py --help`皆退出0；測試沒有建立實驗或擷取。這只驗證小型Import／CLI，不是跨平台乾淨機器的完整安裝驗收。Linux為PDF主要支援平台；目前macOS鎖定環境的通過不等於Linux已驗證。README指向docs的連結也須於打包時保留或改寫，不能形成斷鏈。

本次未修改README、Pixi、Ontology或提交結構。`report.pdf`、Phase 2成果、兩階段比較、三題英文問答與正式ZIP均留待後續核准。F1確認沒有核心／科學資料的重大阻擋，因此可繼續F2素材與F3交接；**Submission Readiness Audited不代表Submission Package Ready**。

---

## 歷史：前次部分稽核與停止（原文保留，最新結論以上方R1–R4為準）

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
