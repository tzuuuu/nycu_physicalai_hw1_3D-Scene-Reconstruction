# Physical AI HW1 — Phase 1 Final Handoff

日期：2026-11-19（臺灣）。本文件是Phase 1結案後唯一的正式交接入口；歷史驗收文件作為證據保留，不被取代或改寫。

**Phase 1 — Experiment Accepted / Submission Readiness Audited / Report Assets Prepared / Handoff Complete**

狀態須分開解讀：正式實驗階段完成、必做程式碼稽核完成、Phase 1報告素材與交接完成；**最終ZIP尚待完成**。本次沒有撰寫最終英文報告、正式打包、Phase 2擷取、Bonus或Experiment D。此為技術結案，完成後停止並等待人工驗收；不代表Phase 2已獲執行授權。

## A. 作業規範與程式碼

### A1. 權威依據與必要實作

最高依據為`docs/assignments/HW1_3D Scene Reconstruction.pdf`。完整PDF符合性矩陣、程式行號、Snapshot差異與測試證據見[Phase1_Submission_Readiness_Audit.md](Phase1_Submission_Readiness_Audit.md)最新R1–R4；後方歷史部分保留前次停止時狀態。

|PDF要求|頁碼|實際實作與驗收|
|---|---|---|
|手寫Depth Unprojection|2–3、10|本批內參、NumPy Pinhole，毫米僅在讀檔邊界換算一次；不使用Open3D投影代替|
|Voxel／Normals／FPFH|2–3、10|Open3D降採樣，normal=2v/30鄰點、FPFH=5v/100鄰點|
|RANSAC→Point-to-Plane ICP|3、10|真實FPFH匹配／RANSAC初值、指定Open3D Point-to-Plane；失敗不填假矩陣|
|Trajectory／Map／GT評估|3–4、10|current→previous矩陣右乘累積；首相機參考；GT僅於評估，無最佳擬合；Mean L2與紅估計／黑GT|
|Data Verification|4–8、10|八項真實因素、Declare→First-Pass→Explore→Query／Selected；Turtle與Seal驗證|
|圖表與報告|11–12|Phase 1素材已備；Phase 2、跨階段比較、三題英文問答與report.pdf尚待後續工作|
|ZIP|12 §5.1|根目錄指定檔案及所有必要來源；排除實驗TTL與生成產物；額外相依安排未定|

**沒有發現必做演算法缺漏。** 所有老師原utils註解依token序列逐字、依序保留。唯一保留`NotImplementedError`的是Optional `my_local_icp_algorithm`；未選做，不得混入必做Open3D成果。

固定核心／環境：Python3.9.23、Open3D0.18.0、NumPy1.26.4、OpenCV4.8.0.76、SciPy1.13.1、RDFLib7.1.4、Panel1.4.5、Bokeh3.4.3、Habitat-Lab0.3.3、OMP_NUM_THREADS=1。RANSAC為1.5v距離、edge0.9、n=3、max_iteration100000、confidence0.999；ICP為1.5v距離、100次、fitness／RMSE容差各1e-6。所有正式Phase 1地圖down_voxel=0.05 m。

### A2. 原始Snapshot與核准差異

`snapshot/pre-implementation`保持`291209750bd8ecf84f337112c9b92307e6be192a`。相對Snapshot：

- `utils.py`：既有必做TODO與helper實作，280行新增／7行移除，提交6a8121a至1922c1c可追溯。
- `reconstruct.py`：已核准C級`--down-voxel`擴充（32c1e7d），10行新增／1行移除；預設None與原旗標相容，三條CLI路徑及位姿／因素不變性測試通過。
- `api.py`、`load.py`、`plot.py`、`ontology/hw1.ttl`、`pixi.toml`、`pixi.lock`與Snapshot相同；本次未修改核心。
- 研究scripts、tests、MD、query為獨立輔助；三路徑OS中繼檔政策只在明確授權下啟用，預設嚴格驗證器未全面放寬。

### A3. Ontology與實驗Turtle

`ontology/hw1.ttl`是必交TBox，可保留原檔納入未來ZIP；`experiments/<name>/<name>.ttl`是生成／學生宣告的實驗紀錄，PDF明確排除於ZIP，不得合併入Ontology。

Ontology共313 triples，RDF/Turtle解析與API載入通過，八項因素定義完整可讀；與Snapshot SHA完全相同。教師詞彙中`QualityFactor`、`appliesTo`、`overProperty`沒有獨立主詞宣告，現有API正常；若助教另要求嚴格詞彙宣告，須確認而非自行補寫。Seal保護宣告bytes，不等同鎖住所有PNG、參數或後續run；獨立SHA保全仍必要。

### A4. 最終ZIP未決清單

|項目|分類／風險|後續方案與核准點|
|---|---|---|
|四個py、Ontology、report.pdf、README|A：PDF p.12明列必交|根目錄直接放，不多包外層；report.pdf尚未撰寫|
|plot.py|B：Explore必要本機模組|最小來源測試確實匯入失敗；需額外包含，不能只複製示意檔案|
|packages/simulator與configs|B：load／Phase 2擷取相依|需保留來源與pyproject、設定，或另訂核准取得方式|
|Pixi editable path|B：目前引用simulator與dependencies/habitat-lab/habitat-lab|確認第三方tree打包／外部取得安排；變更Pixi須另核准|
|SPARQL .rq原始碼|B：Selected重現必要|向助教確認純query目錄位置；不附生成實驗TTL|
|README|提交版尚未完成|補Selected --write、query、資料放置、版本、map voxel、Bonus未做、來源與排除清單；目前未修改|
|Pixi test task|既有三個引用測試檔不存在|提案改到真正pytest入口，等待設定修改核准；實際python -m pytest正常|
|研究工具／tests／MD|C：非全部為原CLI必要|按重現與source links選擇，不把大型研究目錄整包加入|
|Experiment TTL、PNG／HTML診斷、Capture、Replica、.pixi／build|D：生成產物或明確排除|圖嵌入report.pdf即可，勿附整套原始診斷／環境|
|各參數workspace只有FullBatch|正式M2／M3.1已有Baseline＋Selected；M3.2純參數條件獨立保存|PDF允許其他介入，但若助教要求每份敏感度TTL都含Selected，需釐清；不得偽造Selected或擅改模型|
|Linux乾淨環境|PDF主要支援平台，尚無本輪跨平台安裝驗收|目前macOS合成與Import通過不等於Linux已測；留至提交準備驗證|

上述皆保持未解決，不因SHA例外或素材完成而標示通過。必須等人工決定相依打包與助教疑義；本次沒有建立正式ZIP。

## B. 實驗研究歷程

### B1. M2：原始Baseline

研究問題：完整一樓191張可否依官方流程重建並產生真實因素／Seal？原始全解析地圖有資源風險，經核准加入map-only down_voxel；5／10／20張對照確認不改位姿、因素與Mean L2，再完成正式Baseline。

正式Experiment為`p1_baseline_20261118_map005_s0_01`。191張、Mean L2 **3.174055104788137 m**、1522因素、有效Seal與FullBatch。完整程序286.378044 s、峰值RSS0.830322 GiB。流程完整，但後段紅黑軌跡明顯分離。原CLI未保存同次完整點雲／位姿；原生PNG可用，不能事後假稱它已有新的完整點雲匯出。

### B2. M3.0：103→104唯讀診斷

以同來源／同核心／同設定的診斷執行保存190對矩陣與191位姿，完整Mean L2與正式M2相同、1522因素逐筆相符；這是相符診斷來源，不是原M2同次位姿。

103→104：RANSAC旋轉誤差176.074504°，ICP後179.778159°；平移誤差1.352139→0.946960 m。第104張L2跳至0.988960 m；後續小局部運動沿錯誤累積姿態傳播，最大L2於160達10.697682 m。局部ICP內部殘差改善沒有救回真實姿態。

### B3. M3.1：Frame 104單次消融

設定只排除104，保留首影格1，實際新配對為103→105，並用官方SPARQL及--write保存Selected。這是曾參考M3.0 GT定位的Exploratory Ablation，不是完全不依賴GT的通用選幀規則。

Selected190張Mean L2 **4.200397987245927 m**；Baseline共同190張 **3.1855556038742154 m**，惡化約31.86%。新103→105仍錯：RANSAC旋轉178.476380°、ICP179.827009°、ICP平移誤差3.508136 m。末張L2達18.248518 m；刪104沒有改善，未追加刪幀。

同workspace新增Selected後，全TTL SHA預期改變，但Declaration／Seal、Baseline Run子圖與排除Selected後RDF皆保持。Baseline的1522因素不被Selected覆寫；Selected實際1514因素、189對矩陣保存在獨立研究目錄。兩組1–103位姿相同，共同188對矩陣相同，支持差異起於新鄰接配準，而非後續每對都變壞。

### B4. M3.2：Registration Pipeline Scale與五Seed

所有原訂條件各嘗試一次；B0同時作C組seed0，不新增假獨立觀測。

|條件|v (m)|Seed|完整影格／結果|Mean L2 (m)|總程序時間 (s)|峰值RSS (GiB)|
|---|---|---|---|---|---|---|
|B0|0.05|0|191，完整|3.174055104788|305.895459|0.863235|
|B1|0.03|0|70→71 RANSAC失敗；無完整值|—|290.755403|0.484528|
|B2|0.08|0|191，完整|0.274959466593|91.218485|0.922440|
|C1|0.05|1|191，完整|0.155696709607|301.956052|0.879028|
|C2|0.05|2|191，補充科學審計通過†|3.165352438552|299.157768|1.042709|
|C3|0.05|3|191，完整|0.221466815796|305.920728|0.812973|
|C4|0.05|4|191，完整|3.366709232590|306.577317|0.814331|

† C2原finalize因OS中繼檔停止；獨立補充審計確認191張／190對／1522因素、參數、Turtle／Seal及來源SHA，但`original_finalize_succeeded=False`。原停止及後續ps權限／收尾重複寫入停止皆保留。

B1較細尺度在70→71出現RANSAC零對應，僅有70張已接受位姿前綴與562筆部分觀測；無完整Mean L2或地圖。核心雖曾算出ICP數值，整條配準鏈仍被拒絕，不拿ICP當 fallback。

B2相對B0 Mean L2降低91.3373%，103→104不再同級翻轉；但v同時改變點數、normal／FPFH鄰域及距離門檻，不能獨立歸因於任一參數，也不能宣稱0.08是通用最佳值。

C組seed0..4全部完成，Mean L2平均2.016656060267 m、樣本標準差1.670897484447 m、中位數3.165352438552 m、範圍3.211012522983 m；seed0／2／4在103→104有>150°旋轉錯解，seed1／3沒有。5／5完成與3／5重大錯解並存；這是有限樣本描述，不能選最低GT誤差seed1當通用策略。

每條件一次時間量測，背景負載／快取與歷史時段不完全一致，不能宣稱顯著效能優勢。時間含CLI啟動、重建、評估、PNG／Seal與觀測；不含後續Explore／Query與離線分析。RSS持續監測保留3 GiB護欄，C3／C4實際597／598筆取樣。完整設定、局部誤差及SHA表見M3_Parameter_Experiment_Acceptance.md。

## C. 最終研究發現：觀察與假說分開

|資料直接支持|尚未證實／不可擴張的結論|
|---|---|
|103→104重大姿態錯解經連乘影響後段軌跡；後段局部誤差小仍可有大全域誤差|最初是哪組FPFH候選／法向量機制觸發錯解尚未證明；不能把傳播機制等同感測來源原因|
|刪104後新103→105仍嚴重錯配且共同樣本Mean L2更差|不能說所有選幀都無效，也不能說104完全無影響；新轉角、視野、深度支撐同時變動|
|B1保留較多點仍失敗|不代表所有細voxel都失敗；只有v0.03、seed0的一次結果|
|B2改整套尺度改善本次結果|不能宣稱較大voxel必定更好或跨seed穩健；未測0.08多seed|
|固定v0.05下5個seed有3個重大錯解，2個較準|不能宣稱seed1或3可泛化，也不能以最低GT seed替換Phase 2設定|
|103→104 ICP的Fitness提高、RMSE下降仍近180°錯；不同尺度平均RMSE不等於GT精度排名|內部一致性不驗證物理姿態唯一性；不能用單一Fitness／RMSE當真實精度保證|

B2／C1／C3的地圖與紅黑軌跡較接近，仍有殘餘偏移、孔洞與重影；B0／C2／C4及Selected的錯誤地圖不得修復後冒充原結果。觀測保留不等於地圖正確涵蓋全部房間。

M3.1離線GT定位觀測支撐代理：0.1 m格網下34637格→34615格，保留99.9364841%，僅104提供22格。這只描述原始觀測支撐，**不是實際樓層涵蓋99.94%或重建準確率99.94%**；本次不重算／不將GT參考地圖寫回正式成果。

## D. Future Work（只交接，不實作）

1. **逐對Registration Success Rate**：獨立測全部190個原相鄰配對，固定條件，記錄成功／拒絕、因素與資源。B1前69對成功不代表69／190的全序列成功率；不能把未知後段算失敗。
2. **Failure-aware Frame Selection**：以非GT品質／失敗訊號事先定義規則，限制跨缺口、保留首影格，重估新鄰接並在共同影格比較；不能直接略過失敗矩陣串接。需新設計與授權。
3. **Robustness vs Accuracy**：有效回傳、完成率、失敗位置與完整GT誤差／地圖品質分開報告；可完成不等於準確。
4. **RANSAC參數／confidence研究**：將自適應早停作可否證假說，不把對稱錯解誤認為只是迭代不足。confidence目前寫死於核心，任何修改與D實驗須另核准。
5. **跨資料集泛化**：預先固定條件、多seed／未見資料及不同幾何支撐比較；不以現有一樓GT挑選部署參數。

## E. 最終報告素材與來源

素材根目錄：`research_outputs/phase1_report_assets/`。共21張：18張離線重繪（300 dpi）、2張正式原生PNG逐bytes複製、1張既有局部診斷圖複製。來源、Experiment、設定、影格數、Mean L2、視角／軸向／裁切、尺寸、SHA及限制均列在`manifest.json`；英文Caption在`captions/figure_captions.md`。這些是素材，不是英文最終報告。

|素材|位置|可用於報告章節|
|---|---|---|
|M2正式Baseline原圖|`single_runs/M2_baseline_native.png`|Phase 1 Baseline Results，須保留原生稀疏／視角限制|
|M3.1 Selected|`single_runs/Selected_topdown.png`、`M31_selected_native.png`|Frame 104消融與負面結果|
|B2、C1、C3|`single_runs/B2_topdown.png`、`C1_topdown.png`、`C3_topdown.png`|尺度／seed改善個案；不能選作泛化最佳設定|
|B0、C2、C4|`single_runs/B0_topdown.png`、`C2_topdown.png`、`C4_topdown.png`|負面條件與重大翻轉，原生PNG索引在`data/native_png_index.json`|
|Baseline／Selected|`comparisons/A_baseline_selected_errors.png`、`A_baseline_reference_vs_selected_maps.png`|共同190張比較與同範圍幾何參考；後者左圖明示B0控制組|
|B組完整候選|`comparisons/B_maps.png`、`B_mean_l2.png`|Registration Pipeline Scale，B1清楚標失敗而非0誤差|
|C組全部5seed|`comparisons/C_maps.png`、`C_mean_l2.png`|完整分布與穩定性，B0僅作seed0一次|
|全序列／局部誤差|`diagnostics/per_frame_l2.png`、`local_registration_errors.png`、`pose_flip_103_104.png`|Data Verification、變換鏈與翻轉分析|
|八項因素|`diagnostics/B_eight_factors.png`、`C_eight_factors.png`|原生閾值／點集的時間序列；B1部分觀測明示未封存|
|已存在局部點雲診斷|`diagnostics/existing_pair_cloud_projections.png`|RANSAC／ICP／GT參考的局部診斷；不是整層地圖|
|數值與設定|`data/run_comparison.csv`|Mean L2／Frame Count／Runtime／設定表；B1的70只表示接受前綴，沒有完整評估值|

**原M2來源限制必須保留**：沒有其原同次完整點雲／位姿，不能新產生精確原M2 Top-down或共同視角密集地圖。原PNG已完整保留；等尺度A地圖比較使用清楚標示的B0相符控制組作補充，不能冒稱原M2點雲。A誤差圖的Baseline軌跡來自相符M3.0診斷，原始完整Mean L2及共同190張值在圖說皆揭露。沒有為補圖重新執行RANSAC／ICP或整層點雲整合。

所有新場景圖使用已裁天花板的保存取樣；固定首相機、X右／Y下／Z前，Top-down投影到X/Z；原生PNG保留既有diag(1,-1,-1)顯示軸。比較組共用X/Z界線、等比例、9萬個等距索引顯示上限、相同點樣式與紅黑軌跡。保留錯誤擴張區域、不以GT擬合、裁掉錯誤或修圖。因保存來源本身已stride取樣，不能恢復失去的細節；不假稱原生圖也有300 dpi新資訊。

21張都已透過聯絡表實際檢視；字體／刻度與點雲對比修訂草稿留在F1恢復目錄，不覆寫正式來源。最終圖例移出地圖，避免遮住房間／角落與軌跡。驗收記錄為`visual_review.json`及`resume_01/F2_acceptance.json`。

可直接使用的Phase 1素材：方法與設定來源、八因素、失敗分析、Baseline／Selected及B／C比較表、英文圖說。仍須等待後續完成：Phase 2 Capture與介入、兩階段比較、英文報告整體敘事與三題問答、最終README及ZIP。PDF未要求為第一題另跑無RANSAC實驗；本次未做該實驗，不虛構答案所需量測。

## F. Phase 2交接、驗收與停止

### F1. 可延續的已驗證方法

- 正式手寫反投影→Voxel／Normals／FPFH→RANSAC→Open3D Point-to-Plane ICP→軌跡／地圖→固定首相機Mean L2流程。
- 八因素逐影格／逐對量測與官方Declare／Seal／Explore／SPARQL流程，保留Baseline及新介入的獨立來源。
- 每次先核對Capture、內參／深度尺度、版本、參數、Turtle、Seal與SHA，保護原始資料；以新workspace防覆寫。Phase 2需保留原capture首影格。
- 官方原圖＋凍結來源離線高解析圖，Estimated紅、GT黑、去天花板、共同座標／視域；GT僅作重建後評估。
- 明確區分Mean L2、影格保留比例、實際房間／連通區域的視覺涵蓋、觀測支撐代理；缺場景表面GT時不填虛構絕對涵蓋率。

### F2. 尚需另訂且核准

Phase 2必須另訂擷取路線、組數、條件、資料保全與介入設計，不自動採用C1的seed1或B2的voxel0.08。`configs/second_floor.yaml`含`clear_existing: true`，未來必須隔離新的output-root；本次不啟動load.py擷取。現有env_test兩張僅為歷史環境測試，不算Phase 2成果。

若需要修正Pixi test task、editable來源安排、Ontology詞彙或大幅改變提交結構，先呈現修正方案與影響並取得人工核准。不得以本次Closeout為新實驗／核心修改的授權。

### F3. 驗收紀錄與可追溯性

F1新恢復紀錄為`research_outputs/phase1_closeout_audit/resume_01/`；原F1停止與部分稽核全文、M3.2 C2／ps／重複verify停止均保留。三個精確OS Metadata例外逐次記錄原／目前SHA、路徑、檔案類型與授權SHA；沒有全域萬用字元，也沒有放行第四路徑。

|階段|實際狀態|驗收證據|
|---|---|---|
|F1|程式碼、Ontology、來源與研究成果稽核完成；ZIP風險未關閉|F1_audit.json、F1_acceptance.json、Readiness Audit最新R1–R4|
|F2|21張可追溯圖片、英文Caption、表格及目視驗收完成；原M2來源限制保留|phase1_report_assets/manifest.json、visual_review.json、F2_acceptance.json|
|F3|本文件完成，研究／素材／Phase 2邊界可交接|本文件與最終Closeout provenance／manifest|
|最終ZIP|未完成、未建立|README、報告、額外相依與助教確認仍待處理|

測試分階段：46項精確政策／相容性測試；F1完整247 passed in16.18s；新增3項純顯示取樣／範圍／有限值測試後，完整 **250 passed in6.83s**。未收集第三方或需互動擷取的simulator e2e，不把未跑項目算通過。沒有正式191張配準或重建的新執行。

Git依F1→F2→F3分階段：`3b9d687`精確政策、`d5c2aac`F1完成、`b717b75`F2繪圖工具；本F3以獨立文件提交。保持main、原Snapshot、無remote，研究／圖片／JSON等大型產物不加入Git；只新增工具、測試與文件。最終提交與SHA由`research_outputs/phase1_closeout_audit/resume_01/closeout_provenance.json`及`closeout_manifest.json`識別。

**Phase 1實驗與本次Closeout工作完成。最終ZIP尚待完成，立即停止並等待人工驗收；不自行進入Phase 2、Bonus、Experiment D或最終英文報告撰寫。**
