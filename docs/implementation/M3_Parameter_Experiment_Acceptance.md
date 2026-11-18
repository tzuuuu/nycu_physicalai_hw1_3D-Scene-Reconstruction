# M3.2 Registration Parameter Experiment：已執行結果與系統停止驗收

日期：2026-11-18（臺灣）。**原訂七條件尚未全部執行，不申請完整B＋C驗收通過。** 本輪在明確核准的新政策下，沒有重跑B0／B1；依序完成B2、C1、C2的完整191張正式重建。C2後置作業的全檔SHA護欄發現 `experiments/.DS_Store` 改變，觸發系統／完整性停止，C3、C4未啟動。

累計5次正式嘗試：4個完整重建成功、1個Failed Registration，另2個Not Executed。**Success在本文件表示重建完整返回並有真實官方成果，不等於姿態正確；C2另有尚未通過全檔完整性護欄的明確註記。** 無額外候選、重試、跳幀、GT補正、核心修改、D、Phase 2、Bonus或最終英文報告。

B0最初序列化停止與B1配準停止的原驗收文字，分別保留於 `M3_Parameter_Experiment_B0_Stop_Record.md`、`M3_Parameter_Experiment_B1_Stop_Record.md`；研究目錄的原停止檔、traceback、不完整JSON、部分因素、位姿前綴及資源紀錄均未改寫。

## 1. 規範、授權與執行前確認

本輪重新閱讀原13頁PDF，核對pp.2–5的反投影／配準／GT／八因素、pp.6–8官方實驗流程、pp.10–11演算法與成果要求，並檢視第10頁渲染；同時核對交接MD、M3.2 Plan／Acceptance及M2、M3.0、M3.1紀錄與目前程式／測試。

執行前唯讀驗證：

- 原始RGB與Depth皆精確1..191；GT標頭(191,7)，相機內參／深度換算不變。
- capture SHA仍為 `22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`。
- `utils.py`、`reconstruct.py`、`api.py`、Ontology、load／plot與pixi設定／lock，均與suite保存的教師核心SHA相同。
- 原M2／M3.1完整workspace、Turtle、Seal、baseline／selected子圖、B0有效1522因素及B1未封存宣告與失敗證據均核對。原始553／恢復前613／B1開始前642個受保護檔案當時全數一致。
- Open3D0.18.0、NumPy1.26.4、OpenCV4.8.0.76、RDFLib7.1.4、SciPy1.13.1、Panel1.4.5、Bokeh3.4.3、Habitat-Lab0.3.3與既有環境一致；Python3.9、OMP_NUM_THREADS=1，不安裝或升級依賴。
- B2、C1–C4 workspace與研究輸出尚不存在；main乾淨、無remote；snapshot/pre-implementation仍為 `291209750bd8ecf84f337112c9b92307e6be192a`。

## 2. 新排程政策與工具驗證

新增B級 `scripts/m32_sensitivity.py`，擴充既有獨立紀錄／比較工具，**未更動老師核心或正式CLI**。先通過198項完整測試（5.31s），以 `dc0cc16` 提交後才開始正式執行。

新授權另存 `research_outputs/m32_20261118_suite_01/resume_02/authorization.json`，綁定原suite、`suite_stopped.json`、`resume_failed.json`、前次 `resume_authorization.json` 的SHA；B0／B1仍禁止重跑。

- 真實配準失敗須同時符合：正式核心的RANSAC／ICP錯誤格式、失敗配對與回傳量測、恰一次重建、連續且完整的部分觀測、無RSS異常、未封存宣告與保全驗證。符合後可記為Failed Registration並繼續下一個既定條件。
- 只比對錯誤文字不夠；任一量測不吻合、未知例外、資源或SHA異常，均寫入新的 `resume_02/system_stopped.json` 並停止。
- 每個終態另存status receipt及證據SHA，作為下一條件排程依據。B1有合法負面終態，不以偽造的成功Baseline放行。
- 比較工具保留失敗列，Mean L2只彙整完整重建；未執行、失敗及全流程完整性分開揭露。

真正執行命令（專案根目錄）：

```bash
OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/m32_sensitivity.py initialize

OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/m32_sensitivity.py run --condition B2

# B組比較完成後，C1使用相同入口與 --condition C1。
# 後續預定C2→C3→C4以check=True依序啟動；C2系統停止後其餘沒有啟動。
```

每次經官方 `api.py declare`、未修改的 `reconstruct.py` 首次全批量測與評估，再 `api.py explore`、`api.py query`。由同一次正式CLI的唯讀return觀測保存191個位姿、190對粗／細矩陣與八因素，不替換函式／矩陣、不提供GT初值；未封存首次重建自動寫baseline，沒有虛假selected。GT僅在重建返回後進入官方評估及離線分析。

## 3. 七組狀態與完整191張Mean L2

|條件|v (m)|Seed|實際狀態|Mean L2 (m)|限制／失敗|
|---|---|---|---|---|---|
|B0|0.05|0|Success|3.174055104788|完整191張|
|B1|0.03|0|Failed Registration|無完整值|70→71 RANSAC零對應|
|B2|0.08|0|Success|0.274959466593|完整191張|
|C1|0.05|1|Success|0.155696709607|完整191張|
|C2|0.05|2|Success†|3.165352438552|全檔SHA護欄：.DS_Store|
|C3|0.05|3|Not Executed|未執行|系統停止後未啟動|
|C4|0.05|4|Not Executed|未執行|系統停止後未啟動|

† C2重建、正式評估、Turtle／Seal／1522因素與Explore／Query已完成；但finalize在全檔SHA檢查停止，沒有寫出成功 `integrity.after.json` 或終態receipt。獨立停止後審計可驗證其科學證據，不把該審計當成解除原護欄或整組驗收通過。

B1無完整191張Mean L2；C3／C4沒有實驗值。無效值不填0、不與不同影格數的平均混比。保留原M3.1的190張Selected=4.200397987245927 m作歷史脈絡，不混入本研究191張排名。

## 4. 連動參數與固定變因

| 條件 | v (m) | Normal radius (m) | FPFH radius (m) | RANSAC驗證／Distance Checker (m) | ICP distance (m) | Seed |
|---|---:|---:|---:|---:|---:|---|
| B0 | 0.05 | 0.10 | 0.25 | 0.075 | 0.075 | 0 |
| B1 | 0.03 | 0.06 | 0.15 | 0.045 | 0.045 | 0 |
| B2 | 0.08 | 0.16 | 0.40 | 0.120 | 0.120 | 0 |
| C1–C4 | 0.05 | 0.10 | 0.25 | 0.075 | 0.075 | 1、2、3、4（3／4未執行） |

全部固定：完整191張原始影格；normal max_nn=30、FPFH max_nn=100；RANSAC mutual=True、edge checker0.9、n=3、不估尺度、max_iteration100000、confidence0.999；Open3D Point-to-Plane ICP、max_iteration100、fitness／RMSE容差各1e-6；map down_voxel=0.05 m、build_cloud=True、ceiling margin1 m。法向量正常由2v前處理取得，ICP缺法向量的3v回退不是本次正常路徑。Seed按既有程式每對重設。

## 5. 103→104局部誤差及全序列錯誤

|條件|RANSAC旋轉 (°)|ICP旋轉 (°)|RANSAC平移 (m)|ICP平移 (m)|
|---|---|---|---|---|
|B0|176.074504313|179.778159121|1.352138805|0.946959929|
|B1|未到達|未到達|未到達|未到達|
|B2|1.481139775|0.793844775|0.465103836|0.018675483|
|C1|0.539919085|0.171590394|0.348820685|0.265884493|
|C2|172.158898863|179.776546688|1.253175719|0.946915449|
|C3|未執行|未執行|未執行|未執行|
|C4|未執行|未執行|未執行|未執行|

下表嚴重錯解採計畫事先固定的局部旋轉誤差>150°，欄位列current frame；>90°位置在本次已完成四組也相同。這是離線描述，不控制配準或選幀。

|條件|RANSAC>150°|ICP>150°|最大L2 (m)|末張L2 (m)|末張全域旋轉 (°)|地圖點數|
|---|---|---|---|---|---|---|
|B0|[104]|[104]|10.697682|5.795983|179.829626|2725240|
|B2|[]|[]|0.622966|0.449369|1.796567|2553898|
|C1|[]|[]|0.347128|0.255761|0.682926|2559601|
|C2|[104]|[104]|10.677933|5.755900|179.851053|2725952|

B0／C2嚴重錯解皆僅出現在103→104，後續連乘傳播到全域軌跡；B2／C1未出現同級翻轉。B2最大ICP局部旋轉誤差為103→104的0.793845°，但104→105仍有0.543665 m局部平移誤差，故不能宣稱地圖完全正確。B1未到103→104，不能回答細尺度能否修復原翻轉。

## 6. B組：Registration Pipeline Scale敏感度

B組原3個候選均已有一次終態：B0與B2完整成功、B1配準失敗。候選內完整重建完成數為2／3；這不是對未見資料或隨機試驗成功機率的估計。

- B2相對B0，完整191張Mean L2由3.1740551降至0.2749595 m，降低 **91.3373%**；103→104初值從176.07°錯解變為1.48°，ICP後0.79°，支持「整套尺度改變可影響該次幾何匹配及錯解」的假說。
- 改v同時改點數、normal／FPFH鄰域、RANSAC與ICP距離。不能把改善單獨歸因於較大FPFH半徑或較寬ICP門檻，也不能推論越粗越好。
- B1保留更多點，卻在70→71零RANSAC對應，顯示較細／較多點不保證完成。沒有增加第三個細尺度或改seed重試。
- B2只有seed0一次；本研究未對0.08測多seed，因此**不能宣稱0.08具有跨seed穩定性或已找到通用最佳值**。
- 同範圍地圖顯示B2後段紅軌跡較接近黑GT、嚴重反向錯位減少；仍有殘餘位移、重影與缺口。原始觀測均191張不等於實際地圖正確覆蓋100%，沒有量測完整樓層表面覆蓋率。

## 7. C組：Seed敏感度（部分結果，尚缺seed3／4）

固定v=0.05，已取得seed0、1、2的完整結果：3.1740551048、0.1556967096、3.1653524386 m。Seed1避免原翻轉，0與2仍近180°，支持抽樣敏感性；三組都能完整重建，所以「可完成」不代表精度良好。

|統計（僅已完成seed0、1、2）|數值 (m)|
|---|---|
|mean_m|2.165034750982|
|sample_std_m|1.740143229016|
|median_m|3.165352438552|
|min_m|0.155696709607|
|max_m|3.174055104788|
|range_m|3.018358395181|

樣本數n=3，標準差ddof=1；**不是原訂五seed統計**，seed3、4為Not Executed，不放入數值分母、不稱為配準失敗。以已嘗試seed計為3／3完成，以原計畫計為3／5已有結果，兩種分母須明確區分。C2另有全檔SHA護欄註記。最小值僅作描述，不選seed1當作可泛化改善策略、不把它換到B2或自動追加組合。

## 8. 八項因素與判讀限制

四個完整成功重建各有真正同次Pipeline的1522因素：RawPointCount／VoxelizedPointYield各191；其餘六項各190。所有因素與同次return觀測按官方儲存精度逐筆核對。B1只有562筆部分觀測（含失敗對），不冒充完整封存因素。

下表為官方因素序列平均；點數以count表示、RMSE以m表示，其餘為比例：

|因素|B0|B2|C1|C2†|
|---|---|---|---|---|
|RawPointCount|249540.3089005|249540.3089005|249540.3089005|249540.3089005|
|VoxelizedPointYield|19943.7172775|8302.7172775|19943.7172775|19943.7172775|
|CoarseRANSACFitness|0.9227953|0.9341015|0.9250392|0.9223018|
|CoarseRANSACRMSE|0.0269385|0.0411192|0.0273371|0.0272988|
|CoarseRANSACCorrespondences|18514.0789474|7797.0105263|18546.2526316|18508.5421053|
|ICPInlierFitness|0.9236870|0.9314186|0.9242447|0.9236882|
|ICPInlierRMSE|0.0208759|0.0300806|0.0208759|0.0208804|
|ICPInlierCorrespondences|18525.6421053|7781.1947368|18531.7210526|18525.6894737|

RawPointCount四組相同；B2平均voxel yield約8303點，B0／C各約19944點。B2粗／細RMSE較高但GT誤差較低，說明不同點集與門檻下的內部殘差不能直接排名真實姿態。C1與C2整體平均Fitness相近，卻有截然不同的翻轉與Mean L2；只看全序列因素平均會掩蓋單一災難配對。完整逐幀／逐對CSV、因素摘要及官方時間序列圖均保留。

## 9. Runtime、RSS與資源

|條件|總程序時間 (s)|reconstruct含觀測 (s)|CPU user/system (s)|峰值RSS (GiB)|峰值RSS (bytes)|退出碼|
|---|---|---|---|---|---|---|
|B0|305.895459|293.751107|291.937289 / 2.855139|0.863235|926892032|0|
|B1|290.755403|無正常回傳|275.254486 / 3.035104|0.484528|520257536|1：配準失敗|
|B2|91.218485|79.691431|87.968107 / 1.810149|0.922440|990461952|0|
|C1|301.956052|290.213978|296.470614 / 3.671016|0.879028|943849472|0|
|C2|299.157768|287.339602|293.463405 / 3.825274|1.042709|1119600640|0|
|C3|未執行|未執行|未執行|未執行|未執行|未執行|
|C4|未執行|未執行|未執行|未執行|未執行|未執行|

RSS護欄全部維持3 GiB，已嘗試五組均未觸發。B1時間是失敗前的嘗試，不可直接與完整191張比較。B0仍引用其原執行時間，本輪沒有重跑；其恢復Explore時間另在歷史紀錄保存。其餘總時間含子程序啟動、正式重建、評估／PNG／Seal／Run及觀測驗證，不含後續Explore、查詢與離線圖表。CPU為CLI觀測區間，並非完整系統負載；RSS另有0.5秒取樣序列。

B2本次總時間較短，但只有每條件一次量測，歷史B0與本輪的背景負載／快取未完全一致，不宣稱經統計驗證的效能提升。map下採樣始終固定0.05；地圖點數變化還受位姿與minY天花板裁切影響，不當作品質分數。

## 10. C2系統停止、Turtle與SHA保全

C2正式子程序退出0；Turtle、declaration bytes、Seal、191張FullBatch Baseline、1522因素、191位姿／190對矩陣與官方原始Mean L2均有效；Explore四份HTML與Query亦在停止前成功產生。`finalize`隨後於全檔SHA檢查拋出：

```text
RuntimeError: Protected files changed: ['experiments/.DS_Store']
```

`file`確認該檔案為Apple Desktop Services Store，屬資料夾中繼資訊；無證據顯示它參與任何重建。實際寫入來源未追查，不武斷歸因於某個操作。**即使差異僅為OS中繼檔，原護欄仍確實失敗；未排除該檔案、改寫原SHA、刪除停止鎖或續跑C3／C4。**

| 保護清單 | 全部項目 | 未變項目 | 差異 |
|---|---:|---:|---|
| 原suite | 553 | 552 | 僅experiments/.DS_Store |
| 本輪resume_02開始前 | 669 | 668 | 同上 |
| C2開始前 | 792 | 791 | 同上 |

該檔原SHA：`c58b7c32125c5542846c1a020beff62119d939b6320db407c45f801705e3a6ad`；審計時SHA：`4eacb80ef42c2fba48a71ba7b7bf62db1964908e72fe0216ab0b0465ebb191ad`。停止後另存當下bytes及完整差異清單。不能宣稱所有舊檔案SHA全數不變；**可以確認這三份清單中其他全部檔案，以及原capture、教師核心、原M2／M3.1的Turtle／Seal／baseline／selected均未變**。

B2後置全檔保全676個、C1後置738個當時皆通過。原三個歷史停止／授權檔仍與本輪authorization綁定的SHA一致；新增的 `resume_02/system_stopped.json` 保存C2停止traceback。B0、B1開始標記累計各仍只有一次；C3／C4沒有workspace、輸出或執行標記。

C2不回頭重跑finalize或覆寫既有因素檔，僅在獨立 `research_outputs/m32_20261118_system_stop_audit_01/` 做唯讀驗證與分析；該摘要明列 `full_workflow_complete=False`。一次離線分析啟動因新父目錄尚不存在在mkdir處停止，後以獨立審計工具先建立父目錄；此啟動錯誤亦留有說明，沒有額外重建、讀GT補正或改寫正式成果。

## Discussion and Future Work Candidates

### 1. Registration Success Rate（只規劃，未實作）

目前pipeline在第一個無效粗／細配準即中止。B1可確認70→71失敗，前69對被接受，**無法推論71之後所有原始相鄰配對的成功率**。不能用69／190當「全序列逐對成功率」，亦不能用前綴成功比例代表整批。

未來可建立獨立、唯讀的逐對Registration診斷工具，對全部190個原始相鄰RGB-D配對分別測試預先固定的voxel／seed，記錄每對粗／細成功狀態、失敗位置、因素與資源，統計Registration Success Rate。失敗對不串接成全域軌跡；獨立逐對測試不冒充正式完整重建，也不能替代本研究已封存或失敗的紀錄。**本次沒有建立或執行此工具。**

### 2. Failure-aware Frame Selection（只規劃，未實作）

未來可研究非GT的配準品質／失敗訊號，預先定義選幀規則，再透過官方SPARQL與Selected Reconstruction驗證。必須重新估計保留影格間的新配對、保留首參考、報告保留影格比例與地圖覆蓋，並在共同影格上公平比較Mean L2。

不能直接跳過失敗矩陣後拼接後續轉換，不能用GT挑失敗影格，也不能將選幀的效果混同純voxel介入。M3.1只排除104仍使新103→105翻轉，是不能假設刪幀一定有效的既有反例。本輪沒有新選幀規則、沒有新Selected、沒有改原M3.1。

### 3. Reconstruction Robustness vs Accuracy

Robustness可包含非GT的有效配準回傳率、完整重建完成率、失敗配對位置與數量；Accuracy包含成功完整重建的191張Mean L2、離線局部旋轉／平移誤差與地圖幾何品質。兩者應分開，再共同解釋。

本研究B1未能完成，沒有完整精度；B0與C2雖完整完成卻有近180°錯解與高Mean L2。B1失敗對ICP曾有高Fitness，也不能替代被拒絕的RANSAC→ICP鏈。未來可能出現已完成前綴／局部誤差較低、整批卻中止的條件；不能只在成功組排名而隱藏完成率。另須將C2的系統中繼檔護欄停止與演算法失敗分開，不能把系統未啟動C3／C4算作低配準穩健性。

### 4. B1技術限制與失敗分析

v=0.03保留更多voxel點：前71張yield加總約為B0同影格的2.469倍，第71張80385點對B0的31947點；原始有效點數相同。與此同時normal radius從0.10縮到0.06 m、FPFH從0.25縮到0.15 m、RANSAC及ICP距離由0.075縮到0.045 m，max_nn仍30／100。

70→71的RANSAC零有效對應；當次mutual-filter剩6369互惠特徵候選後回退。這是與失敗相關的實際觀察，不足以將失敗歸因於任何單一參數、回退或幾何成因。既有核心先算ICP後才檢查粗／細結果，因此ICP曾從RANSAC返回的單位初值產生Fitness約0.98156及78903個對應；該對仍被正式核心拒絕，未接受或累積。0 RMSE伴隨零RANSAC對應不是完美配準。預處理71張不等於成功完成71張軌跡；只有前70張的已接受位姿前綴，**不能將部分影格誤差冒充完整191張Mean L2**。

### 5. 是否進一步研究D或結束Phase 1

現有B2與seed1的改善顯示尺度與抽樣值得討論，但未證明RANSAC confidence0.999的自適應早停是主要問題；幾何對稱錯解也可高內點。D可保留為未來受控假說，不能現在修改confidence、增加預算或搜尋seed。

目前建議先人工驗收系統停止與已完成結果，再決定C3／C4是否另行恢復，以及OS中繼檔是否應在未來另列為非科學檔案的紀錄範圍。這是未來工具範圍決策，**不是本輪已放寬的護欄**。若研究時間有限，使用者可選擇以已知限制結束Phase 1，但不能宣稱五seed研究已完成；本輪不自行結束Phase 1或進入Phase 2。

## 11. 產物、比較圖與可追溯性

| 專案根目錄下位置 | 內容 |
|---|---|
| research_outputs/m32_20261118_suite_01/resume_02/ | 本輪授權、669檔案前置SHA、B0／B1終態核對、B2／C1成功receipt及C2系統停止標記 |
| .../resume_02/B_comparison/ | B組完整候選表、成功組逐幀／局部誤差、八因素與地圖；失敗B1明列而不造Mean L2 |
| research_outputs/m32_p1_m32_20261118_b_v008_s0_01/ | B2事前登記、官方CLI／資源、位姿／矩陣、1522因素、Explore／Query、完整性與正式快照 |
| research_outputs/m32_p1_m32_20261118_c_v005_s1_01/ | C1相同證據與完整性 |
| research_outputs/m32_p1_m32_20261118_c_v005_s2_01/ | C2相同正式重建／因素與Explore／Query證據；無成功integrity.after，原例外保留於system_stopped |
| research_outputs/m32_20261118_system_stop_audit_01/ | 停止後獨立七條件CSV、C2離線分析、B／C比較圖、部分三seed統計、OS中繼檔bytes與SHA差異清單 |
| .../B_errors.png、B_maps.png | B0／B2完整191張誤差與同範圍地圖；標明B1失敗 |
| .../C_errors.png、C_maps.png | seed0／1／2完整191張誤差與同範圍地圖；明標seed3／4未執行、C2系統註記 |
| .../C2_analysis/frames.csv、pairs.csv、poses_offline.npz | C2逐幀／逐對離線誤差及固定首相機座標位姿，不做最佳擬合 |

後四列`...`依列意義分別指suite或system_stop_audit目錄。B／C誤差與地圖圖表均已實際檢視。原B1部分因素圖、70張位姿前綴與失敗traceback仍在前輪審計目錄，沒有覆蓋。沒有C3／C4假圖或數值。

## 12. Git、測試與停止點

- `dc0cc16`：新失敗分類／排程政策、固定候選與比較處理；正式B2、C1、C2真正執行commit。提交前完整198項測試通過。
- 原 `860e842`、`ac5495f` 分別為B0、B1真正執行版本；只有獨立工具不同，教師核心與資料SHA始終相同。
- `3ff44a8`：停止後唯讀審計、兩項測試與三組query；另以docs commit更新本驗收與原B1停止紀錄備份。研究結果／Turtle／PNG／HTML／NPY維持忽略，不加入Git；只追蹤工具、測試、MD及可重現query原始碼。
- 停止後完整測試 **200 passed in 5.40s**；新增測試證明可描述.DS_Store差異，但原verify_hashes仍拒絕它，未暗中放寬護欄。`git diff --check`通過。
- 全程main、無remote、不改寫歷史、不動原snapshot；最終commit另由Git紀錄識別。

**維持系統停止。B組三候選已各處理一次；C組僅seed0／1／2，seed3／4尚未執行。本輪沒有重跑B0／B1、沒有新增實驗、沒有解除C2系統護欄。等待人工驗收與下一個明確決策。**
