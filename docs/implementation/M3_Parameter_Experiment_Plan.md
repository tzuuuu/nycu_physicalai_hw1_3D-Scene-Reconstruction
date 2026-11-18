# M3.2：Registration Parameter Intervention 可行性分析與實驗設計

日期：2026-11-18（臺灣）。狀態：**僅完成分析與規劃，所有候選實驗均未執行**。Phase 1 保持開放；本文件不構成實驗執行、核心修改、Phase 2、Bonus 或最終英文報告的授權。

## 1. 結論、研究範圍與依據

建議先核准 **B：Registration Pipeline Scale**，固定 `v={0.05,0.03,0.08}` m、seed=0；接著 **C：RANSAC Seed Sensitivity**，固定 v=0.05 m、seed={0,1,2,3,4}。共同的 v=0.05／seed=0 僅新執行一次，因此兩組合計 **7 次完整191張正式重建**。這是有限候選敏感度研究，不是搜尋最佳值。每個條件都使用新的官方宣告、Turtle、Seal、因素與 FullBatch baseline run，不回寫既有 workspace。

B 不需修改程式，但不是單獨改點雲解析度：現有一個 v 同時控制 voxel、normal／FPFH 半徑、RANSAC 距離與 ICP 距離。C 不需修改程式；seed 每對重設，不是整段共用一條連續隨機流。以上只有「日後核准後可以使用現有介面」的可行性，**目前沒有執行授權**。

延伸 D 提議只把 RANSAC confidence 從0.999改為1.0，保持100000次上限，以檢查錯誤高內點解是否造成過早停止。這需額外的受控核心／CLI修改提案與核准；本次不實作。它不能消除幾何對稱本身。

### 已核對來源

- 老師正式13頁 PDF：`docs/assignments/HW1_3D Scene Reconstruction.pdf`，已直接抽取全部頁面文字並檢視第3頁渲染。pp.2–3允許依分析調整前處理／配準參數；p.4規定GT僅評估及首相機參考系；pp.4–8規定宣告、首次量測、檢視及介入；p.5列八項因素；p.10要求Open3D Point-to-Plane與完整Turtle／Seal／baseline／selected；pp.11–12要求時間、影格數、超參數及成果比較。
- `utils.py`、`reconstruct.py`、`api.py`、`ontology/hw1.ttl`，以及README、環境設定與官方流程說明。**程式行號均以本次工作版本為準**。
- `docs/assignments/PhysicalAI_HW1_Codex_Implementation_Handoff.md`（三級權限、小步commit、正式入口與驗收停止點）、架構分析、規範對照與需求追蹤MD。早期文件中的「核心尚未實作」為歷史狀態，不套用到目前版本。
- `docs/implementation/M2_Baseline_Acceptance.md`、`M3_Diagnostic_Review.md`、`M3_Intervention_Acceptance.md`。
- 本機版本Open3D 0.18.0，與PDF參考0.19.0區分，不升級依賴。版本特定行為另核對官方[全域配準教學](https://www.open3d.org/docs/0.18.0/tutorial/pipelines/global_registration.html)、[v0.18.0 Feature.cpp](https://github.com/isl-org/Open3D/blob/v0.18.0/cpp/open3d/pipelines/registration/Feature.cpp)、[v0.18.0 Registration.cpp](https://github.com/isl-org/Open3D/blob/v0.18.0/cpp/open3d/pipelines/registration/Registration.cpp)。以下幾何推導是研究假說，並非教學已證明本資料的失敗原因。

### 既有證據，不重新定義基準

| 來源 | 影格數 | Mean L2 (m) | 用途 |
|---|---:|---:|---|
| M2正式Baseline | 191 | 3.174055104788137 | 主要歷史比較基準 |
| M3.0相符診斷 | 191 | 同上 | 逐對／逐幀位姿證據；不是正式Baseline原先保存的位姿 |
| M3.1 Selected：排除104 | 190 | 4.200397987245927 | 負面消融結果，保留，不混入191張主要排名 |

原103→104的RANSAC旋轉誤差176.0745043°、ICP 179.7781591°；RANSAC平移誤差1.3521388 m，ICP 0.9469599 m。新103→105仍錯179.8270089851°。因此不把「刪除104」或「ICP增加疊代」直接當成解法。

## 2. 可調參數與修改權限矩陣

權限：A=原教師TODO範圍；B=獨立紀錄／分析／測試／規劃；C=既有核心、公開介面、CLI、Ontology與教師預設設定。**曾以A完成TODO，不表示現在可任意改變已驗收演算法；本輪明確禁止任何核心修改。**「可不改核心」指未來核准實驗後能否只用現有正式CLI；不是本輪執行許可。

相容性欄：**符合**=保持此設定或用現有介面調整，仍符合PDF指定演算法；**有條件**=演算法類型容許，但需核准實作與重新驗證；**禁止**=違反本次控制或正式要求。

| 參數／目前值與實際位置 | 階段與用途 | CLI／不改核心可調？ | 連動、改善與失敗機制 | 時間／記憶體／最終成果影響 | 權限與PDF相容性 |
|---|---|---|---|---|---|
| Registration voxel `v=0.05 m`；`reconstruct.py:88`、`utils.py:125,348,371` | Voxel降採樣；同一降採樣點雲供FPFH、RANSAC與ICP | `--voxel-size`；是，但整組連動 | 小v保留窄邊界，也保留擾動與模糊匹配；大v平滑擾動但刪除唯一結構 | 小v通常增加點數、KD-tree／特徵成本與RSS；改軌跡與地圖位置，地圖採樣密度另固定 | 現有CLI；符合。改預設／解耦需C |
| Normal radius=`2v=0.10 m`；`utils.py:127–134` | 局部共變異數法向量；供FPFH與Point-to-Plane | 無獨立CLI；只能隨v調整 | 小半徑較局部但鄰點不足／法向量不穩；大半徑可能跨牆角；與點距、max_nn相依 | 搜尋成本與法向量品質改變；間接影響粗／細配準，記憶體主要仍隨點數 | TODO明定2v；獨立修改不能稱原契約完全相符，需C級提案，本輪不改 |
| Normal `max_nn=30`；`utils.py:134` | Hybrid搜尋的鄰點上限，不是固定取30點 | 無；否 | 半徑內最多30；增大可平滑也可能跨面，小值易受擾動 | 較多鄰點增加計算／暫存；可改法向量與姿態 | TODO明定30；獨立調整需另核准並處理契約差異 |
| FPFH radius=`5v=0.25 m`；`utils.py:136–141` | 幾何描述子的鄰域 | 無獨立CLI；只能隨v調整 | 小尺度保留局部邊角但平面描述子易相似；大尺度可能納入門框／牆角，也混入遮蔽與不重疊部分 | 描述子數隨點數；搜尋成本受100點上限限制；改匹配池與RANSAC初值 | TODO明定5v；獨立調整需另核准契約差異 |
| FPFH `max_nn=100`；`utils.py:141` | 描述子鄰點上限 | 無；否 | 與5v相依，半徑擴大不保證用到更遠結構，可能先達100點上限 | 增大增加特徵計算；未必增加辨識力 | TODO明定100；另核准，不列B/C的變因 |
| RANSAC mutual filter=`True`；`utils.py:155` | 特徵雙向最近鄰一致性過濾 | 無；否 | 可降低單向歧義，但會失去真匹配；Open3D不足時可能回退單向匹配，True不等於強制全程互惠 | 雙向搜尋有成本；匹配池大小、內點率與耗時一起改變 | 調整仍是FPFH+RANSAC，PDF演算法有條件符合；改核心需另核准 |
| RANSAC maximum correspondence distance=`1.5v=0.075 m`；`utils.py:153–155` | 候選轉換的全點雲幾何驗證距離 | 無獨立CLI；只能隨v調整 | 大門檻易容忍錯面／錯解；太小可排除真匹配及產生零內點；與尺度／量化／擾動相依 | 小門檻未必更快，RANSAC有效假設可變少；Fitness／RMSE定義域也改變 | 現有v連動符合；單獨解耦需C |
| RANSAC Distance Checker=`1.5v=0.075 m`；`utils.py:158` | 對抽樣特徵配對套用候選剛體轉換，檢查距離一致性 | 無獨立CLI；隨v，與上列共用同一`distance` | 不是最大相機平移，也不是FPFH特徵空間距離；與驗證距離目前不能分開 | 越嚴可能更早剔除假設，也可能無解；不保證改善180°錯解 | v連動符合；獨立門檻需C |
| Edge Length Checker=`0.9`；`utils.py:157` | 檢查抽樣配對的邊長比例相容性 | 無；否 | 約需兩邊長比介於0.9與1/0.9；提高至近1更嚴、受擾動更易拒絕。剛體180°旋轉保邊長，無法直接排除 | 改早期拒絕率與時間；記憶體影響小；可改可行假設池 | 維持RANSAC則PDF有條件符合；核心修改另核准 |
| RANSAC seed=`0`；`utils.py:152,384–386`、`reconstruct.py:93` | 控制抽樣隨機性 | `--seed`；是 | 每對呼叫重新seed；同seed換點數／特徵，不代表抽到同一實體點。須固定執行緒與版本 | 無明顯直接記憶體成本；可能大幅改解、早停時間與最終軌跡 | 現有CLI符合；選GT誤差最小seed當策略禁止 |
| RANSAC `ransac_n=3`；`utils.py:157` | 每次剛體估計的配對數 | 無；否 | 三個非共線點理論可定剛體；共線或近共線不穩。增n降低全真抽樣機率`w^n`，也不保證排除對稱 | 增n增加抽樣／估計成本，可能需更多次數；姿態可能改變 | PDF未固定n；改核心有條件，另核准 |
| RANSAC `max_iteration=100000`、`confidence=0.999`；`utils.py:159` | 搜尋預算與自適應早停 | 無；否 | confidence不是「99.9%姿態正確」；錯誤對稱解也可高內點率並觸發早停 | 提高預算／confidence通常延長時間；RSS不按次數線性累積；錯解仍可勝出 | D提案；PDF演算法有條件符合；需獨立修改核准 |
| Coarse estimator=`TransformationEstimationPointToPoint(False)`；`utils.py:156` | RANSAC剛體估計、不估尺度 | 無；否 | 禁止用尺度自由度配合GT；與距離／邊長檢查共同約束 | 目前固定SE(3)，改估尺度會改幾何意義 | 固定符合；本輪禁止替換 |
| ICP max correspondence distance=`1.5v=0.075 m`；`utils.py:348,393–394,195` | 細配準最近鄰接受範圍，與RANSAC初值相依 | 無獨立CLI；只能隨v調整 | 小值可壓制錯對應，也縮小收斂盆地；大值可能跨面；176°錯初值不保證靠縮門檻修復 | 對應數／收斂次數可增可減，零內點須列失敗；軌跡受影響 | v連動符合；解耦需C級介面修改 |
| ICP convergence=`relative_fitness=1e-6, relative_rmse=1e-6, max_iteration=100`；`utils.py:198–199` | 停止條件與疊代上限 | 無；否 | 收緊容差或增加上限只能更充分收斂當前盆地，無全域正確性保證；上限非固定執行100次 | 可能增加時間，點雲主要記憶體不變；可更精確地收斂到錯姿態 | Point-to-Plane保留時PDF有條件符合；修改另核准 |
| ICP缺法向量時radius=`2 threshold=3v=0.15 m`、max_nn=30；`utils.py:181–183` | 只在`has_normals()==False`估計 | 無；否；正常pipeline已有2v法向量 | 正式流程不會每次重估為3v；不能把0.15當Baseline實際法向量半徑 | 正常路徑不生效；異常／獨立呼叫可能增加搜尋成本與改解 | 保持既有回退符合；修改另核准 |
| ICP estimator=`TransformationEstimationPointToPlane()`；`utils.py:197` | 最小化點到切平面殘差，無顯式robust kernel | `--version open3d`（正式唯一可用）；不能CLI加loss | 法向量與幾何可觀測性決定約束；預設損失下離群對應可影響解 | 換loss可改收斂及成本，但不是本輪實驗 | Open3D Point-to-Plane必須固定；Bonus／Point-to-Point不得取代 |
| Map `down_voxel=0.05 m`；`reconstruct.py:91,165–167,264–265`、`utils.py:453` | 每幀地圖副本先下採樣再轉換合併，非全域去重 | `--down-voxel`；是 | 不改cur_down／FPFH／配準；改它不能直接救RANSAC。CLI預設None，但正式M2/M3.1用0.05 | 主要降低地圖RSS／輸出點數，地圖細節改；軌跡應不變 | 現有CLI符合；B/C/D全部固定0.05 |
| `build_cloud=True`；`reconstruct.py:162,259`、`utils.py:451` | 建立整合地圖 | 僅函式引數、無CLI；正式CLI不可切 | 不影響位姿契約；False無完整地圖成果，不用來替代正式實驗 | False通常省記憶體／合併時間；本輪不使用 | 正式固定True；改CLI需C |
| ceiling `margin=1.0 m`；`utils.py:234–245,473` | 合併後依minY裁切，僅影響地圖／顯示 | 函式引數、無CLI；正式流程不能獨立調 | 錯姿態改變minY，可連帶改裁切，固定margin仍不等於固定世界裁切平面 | 點數／視覺覆蓋改，軌跡不改；不能藉裁切掩蓋錯圖 | 固定符合；本輪不改 |
| 影格／鄰接／順序；`reconstruct.py:97,240–253`、`utils.py:258–277` | 決定配對集合 | `--selection-query`；可但本輪不用 | 抽幀產生新配對，破壞191張控制；CLI會攤平segments，非每段重設 | 數量影響資源與覆蓋；M3.1已證實跨幀仍失敗 | 本研究固定1..191；排除／重排禁止 |
| intrinsics、depth_scale、有效深度遮罩；`utils.py:69,74–78,278,295` | 點雲metric幾何與有效點 | 讀原始JSON；缺scale相容1000；無本輪調整介面 | 512×512、HFOV90°；正有限深度，毫米只轉換一次。改校準／尺度直接改問題 | 點數與幾何全面變；可造成人為低誤差 | 原始資料與校準禁止更改；沿用驗收行為 |
| `OMP_NUM_THREADS=1`；`utils.py:2`、`reconstruct.py:7` | OpenMP執行環境／可重現性 | 環境變數可設定；setdefault不會覆寫外部值 | 影響抽樣排程／浮點加總；固定seed也未必跨平台逐byte重現 | 多執行緒可改時間與RSS、數值；本研究明設1 | 固定環境符合；不列實驗變因 |

另查無現行可調的深度截距、統計／半徑離群點濾波、法向量朝向校正、normal correspondence checker、FPFH ratio test、RGB／光度匹配、多尺度ICP、pose graph或回環最佳化。這些是新增演算法，不應列為「已存在的CLI參數」，本輪不添加。`--no-vis`僅跳過互動視窗，仍建圖、評估、產PNG；繪圖取樣與視角只影響呈現，不能當精度介入。擷取YAML的noise/dropout/seed不控制既有一樓資料，不能改YAML就宣稱改變此批配準。

### Open3D行為的兩個必要細節

1. Mutual filter：v0.18.0 `CorrespondencesFromFeatures()`不足互惠對應時會回退原單向集合（見上方Feature.cpp）。M3.1保留了回退警告，尚未可靠定位到103→104，不能直接認定失敗對觸發回退。未來原樣保留stdout、warning與可觀測的pair關聯；最終幾何correspondence count不等於FPFH候選數。
2. ICP容差：名稱雖是relative，legacy v0.18.0 `RegistrationICP()`實作比較相鄰兩次fitness與RMSE的**絕對差**，兩者皆小於門檻才提前停止；不是GT誤差、不是姿態更新角度，也不是RMSE除前一次RMSE的比值。不要套用tensor ICP教學取代本程式的legacy行為（見Registration.cpp）。

## 3. 參數連動與尺度適合性

令registration voxel為v，實際路徑為：

```text
v → voxel_down_sample → 降採樣點與鄰點分布
  → normals(radius=2v, cap=30) → FPFH(radius=5v, cap=100)
  → 特徵候選＋seed＋edge checker → RANSAC
       distance checker = global validation threshold = 1.5v
  → RANSAC初值 → 同一降採樣點雲的Point-to-Plane ICP(threshold=1.5v)
  → 相對轉換連乘 → 軌跡與地圖位置
原始點雲 → map down_voxel=0.05（獨立副本）→ 合併／ceiling margin=1
```

因此若B改善，最多支持「整套尺度改變有幫助」，不能歸因於FPFH半徑、ICP門檻或點數單一因素。max_nn不隨v改；鄰域上限使實際支撐不等於宣告半徑。放大5v未必讓所有點看見更多幾何。

| 條件 | v (m) | Normal radius (m) | FPFH radius (m) | RANSAC驗證／Distance Checker (m) | ICP distance (m) | 缺法向量回退radius (m；正常不使用) |
|---|---:|---:|---:|---:|---:|---:|
| B0／C0控制 | 0.05 | 0.10 | 0.25 | 0.075 | 0.075 | 0.15 |
| B1細尺度 | 0.03 | 0.06 | 0.15 | 0.045 | 0.045 | 0.09 |
| B2粗尺度 | 0.08 | 0.16 | 0.40 | 0.120 | 0.120 | 0.24 |

**保留0.03／0.08，不改候選範圍。** 依既有資料，104深度p10–p90約1.160–1.727 m，fx=512/(2tan45°)=256 px，單像素橫向間距約z/256=4.5–6.7 mm。三個voxel約跨4.5–17.7個這類像素間距，均有降採樣意義，且不接近毫米量化極限。這只是尺度合理性的近似，不是實測雜訊標準差／最佳半徑，也不能代表全部191張的遠近分布。

細尺度FPFH 0.15 m可能留住邊角但看不到足夠大範圍；粗尺度0.40 m可能取得牆角／門框支撐，也可能因100點上限、跨面混合或點數下降失效。0.12 m配準門檻相對近牆已偏寬，故0.08只作粗尺度反向對照，不預測一定更好。更細如0.01會明顯增加成本；更粗如0.15可能抹除必要幾何，目前沒有證據支持擴張候選。

近平面近似下點數可粗估`N(v)∝v^-2`：0.03相對0.05約2.78倍，0.08約0.39倍。若以Baseline最大39638點粗估，約110106／15484點；FPFH本體33個float64約29.1／4.1 MB（不含點、法向量、KD-tree等）。這些僅量級估計；遮蔽、體素邊界、離散曲面與原始262144點上限使比例不精確，不可報成量測結果或直接推成2.78倍總時間／RSS。地圖down_voxel始終0.05，地圖點數不會跟registration v同比例改變；位姿與ceiling裁切仍可能改變輸出點數。

## 4. 103→104的幾何假說

**觀察：**103／104有效深度約89.824%／80.262%，PCA最小特徵值占比約0.01732／0.01399；視野接近平面且非平面支撐有限。錯解已出現在RANSAC。ICP使Fitness由0.6563提升至0.8359、RMSE由0.03372降至0.03109 m，仍錯近180°。殘差旋轉軸近相機Z軸，不能簡化成水平轉向180°；103→105的殘差軸也不同。

**H1：局部描述子／近對稱表面的歧義。** 大片平面上FPFH角度直方圖可能相似，稀少邊角才提供區辨性。對剛體`R,t`，`||Rp_i+t-(Rp_j+t)||=||p_i-p_j||`，因此Edge Length Checker不檢驗上下方向，正確與某些180°假配對都可能通過。Distance Checker又只驗證幾何殘差，不知道物理相機是否翻轉。B可改變保留的邊角及其描述尺度，但若所有尺度仍有相同歧義，仍會失敗。

**H2：Point-to-Plane的局部弱約束。** 殘差`r_i=n_iᵀ(Rp_i+t-q_i)`，線性化Jacobian可寫`J_i=[(Rp_i×n_i)ᵀ,n_iᵀ]`，資訊矩陣`H=ΣJ_iᵀJ_i`。若法向量大致平行，沿平面平移及部分旋轉約束不足；錯解可在另一個盆地有小殘差。PCA只是空間扁平程度，不等同Hessian秩／條件數；目前沒有量到H來證明這是唯一原因。增加ICP次數不能跨越全域姿態歧義。

**H3：抽樣與停止的偶然性。** 若正確特徵對應比例w低，三點全真抽樣機率約`w^3`。理想獨立抽樣下成功機率`1-(1-w^3)^K`，所需次數`log(1-c)/log(1-w^3)`；w=0.05時c=0.999約55259次，w=0.02時約863466次（忽略退化及重複抽樣）。此w是特徵候選的真匹配率，**不是**已輸出的幾何Fitness。C測抽樣敏感性；D測早停。若錯誤對稱解的內部評分更好，再多抽樣仍可能選錯。

H1–H3可以同時成立；深度孔洞／RGB明暗與錯解相關不等於已建立因果。RGB沒有進入本配準的幾何目標。GT只協助既有離線診斷，本研究須揭露此為針對已知失敗案例的探索，不能宣稱未見資料的泛化改善。

## 5. 候選實驗、控制與優先順序

### 共通控制（每一次都固定）

- 原始`eval/_data/first_floor/`完整1..191，190個原始相鄰pair；首張1；不修改／複製加工RGB、Depth、GT或內參，不抽幀、不排序調整、不換capture。
- 沿用已驗收的手寫反投影、512×512／HFOV90°與毫米相容換算；版本open3d、Point-to-Plane、RANSAC初始化與既有轉換累積；不以GT選初值、補正、早停或融合。
- `--down-voxel 0.05`、build_cloud=True、ceiling margin=1；`--no-vis`，但官方PNG與地圖必須產生。
- 除表列變因外，normals cap30、FPFH cap100、mutual=True、edge0.9、ransac_n3、不估尺度、max_iteration100000、confidence0.999、ICP容差兩項1e-6／上限100均固定。
- 同一程式commit與核心SHA、pixi.lock、Python3.9.23、Open3D0.18.0、NumPy1.26.4、OpenCV4.8.0.76、SciPy1.13.1、RDFLib7.1.4；執行前記錄實際版本，任何漂移先記錄偏差，不自動升級。明設OMP_NUM_THREADS=1，資源護欄與觀測工具各次相同。
- 每次獨立新程序、序列執行，避免同時跑測試／重建；盡量相同背景負載。計時包含／排除範圍一致，不以字型快取差異冒充演算法效能差。

### B：Registration Pipeline Scale（第一優先）

| 條件 | v (m) | seed | 新實驗名稱尾碼範例 | 解釋 |
|---|---:|---:|---|---|
| B0 | 0.05 | 0 | `b_v005_s0_01` | 同觀測方法的新控制；不覆蓋／重命名M2 Baseline |
| B1 | 0.03 | 0 | `b_v003_s0_01` | 細尺度，實際派生值見第3節 |
| B2 | 0.08 | 0 | `b_v008_s0_01` | 粗尺度，實際派生值見第3節 |

固定順序B0→B1→B2，不因局部或全域GT結果提前停止／插入其他值。先完成整組，再比較。不做局部103→104試跑後選值，不把控制v=0.05從候選移除。B0若未重現歷史值，保留並調查環境／來源，不能持續重跑到吻合；未解決可重現性問題前暫停後續條件。

可能支持：某尺度同時降低103→104粗／細局部旋轉誤差與191張Mean L2。可能失敗：粗尺度抹掉唯一結構、細尺度特徵不穩、距離門檻太小零內點、寬門檻接受錯平面，或其他pair出現新災難。B僅seed0不能證明跨seed穩健。

### C：RANSAC Seed Sensitivity（第二優先）

固定v=0.05（非B結果最佳值）、其餘設定全同；預先固定seed={0,1,2,3,4}、順序0→1→2→3→4。seed0使用B0相同run，不新增一筆假獨立觀測；其餘4次各一個新workspace，尾碼`c_v005_s1_01`至`s4_01`。這5個seed是有限描述性樣本，無精確成功率或泛化保證。

彙整全部Mean L2的平均／樣本標準差、中位數、最小／最大、完成率；103→104及全190對嚴重旋轉誤差的頻率與位置。最小值只作分布描述，**不將argmin GT seed部署成改善策略**；也不以最佳seed作B各尺度的新基準。若少數seed避免翻轉，支持抽樣敏感性；若全部翻轉，僅代表這5次未避免，不能證明所有seed都失敗。

若日後要宣稱某尺度較穩健，另行核准預先固定的`{0.03,0.05,0.08}×{0,1,2,3,4}`比較（共15條件，重用已完成者且清楚標示），或獨立未見資料驗證；**本輪不自動擴充**。

### D：RANSAC停止條件消融（延後，需修改核准）

假說：錯誤但幾何一致的解可能令自適應搜尋提早結束。D0=`max_iteration100000, confidence0.999`；D1只改`confidence1.0`，使該版實作使用完整100000次預算。v=0.05、seed預固定{0,1,2,3,4}，其他共通控制不變；D0重用C各seed，D1新增5次191張，不挑seed。這不是同時提高max_iteration與改confidence的混合實驗。

數學依據為上述抽樣成功率與自適應K；幾何依據為近對稱的錯解也可能高內點，因此現有confidence並非物理正確性的保證。可能改善搜尋覆蓋，也可能只延長耗時或更穩定選到錯解。不能用D證明近平面歧義已被解決。

目前`utils.py:159`寫死，沒有合法CLI可執行D1。最小未來提案是新增向後相容的confidence引數並由正式`reconstruct.py`傳入，保留預設0.999、其他契約、TODO原文與Point-to-Plane；不以monkey patch、替換Open3D函式或修改局部變數繞過權限。不先指定虛構的新CLI旗標。本輪只記錄提案，實作／測試／實驗須另核准。相較之下，直接改FPFH 5v或normal 2v會違背明示TODO數值契約，故不優先採用。

## 6. 獨立且符合官方流程的實驗保存

### 6.1 必須避開的覆寫路徑

保護完整`experiments/p1_baseline_20261118_map005_s0_01/`，以及既有M2／M3.0／M3.1研究目錄。

- `api.py:112`將run IRI固定為`<experiment>/run/<mode>`；`write_run():638–732`以mode替換相關屬性，不保存同mode歷次歷史。Seal只保護學生宣告bytes，**不鎖定CLI參數、影像、原始碼或run值**。
- sealed實驗無query仍為baseline；帶query才是selected。對舊實驗帶新v／seed再`--write`會把新Mean L2寫入原run，卻保留舊因素，造成混用。
- `--no-write`仍可建圖及覆寫`reconstruction.png`、`reconstruction_baseline.png`／`selected.png`；不是全面唯讀。未封存首次重建自動寫因素、Seal與baseline，無須`--write`且拒絕`--no-write`。
- `api.py explore`會寫plots；多檔比較還會為每份assessed實驗產圖。因此不得把舊workspace傳入新一輪explore，即使Turtle不變，HTML仍可能被覆寫。
- Ontology註解的write-once不得誤讀成程式禁止所有sealed重跑；真正實作允許再次執行與run寫入。需要獨立操作護欄。

### 6.2 每條件一個新宣告，一次首次全批重建

規劃命名`p1_m32_<執行日>_<condition>_<attempt>`，只用合法英數、底線或連字號；實際執行日再確定。每次包含：

```text
experiments/<name>/
  <name>.ttl                 # api.py declare → 正式CLI首次量測／Seal／baseline
  plots/                    # 僅此實驗的官方explore輸出
  queries/                  # 此實驗唯讀因素／影格完整性查詢
  reconstruction.png
  reconstruction_baseline.png
research_outputs/m32_<name>/
  preregistration.json       # before：全部有效值、候選清單、順序、預測、資料／核心SHA
  declaration.before.ttl    # 未封存原宣告bytes
  protected.before.json     # 舊成果、原始資料、環境與核心雜湊
  command/                  # argv、console、execution.json、RSS取樣
  observation/              # 同次CLI的191個全域位姿、190對粗／細矩陣及原始因素
  analysis/                 # 重建完成後才讀GT，CSV／圖／摘要
  official_after/           # 此次TTL、圖片、官方plots的完成快照
  integrity.after.json      # Seal、因素、run、來源與舊成果完整性
  artifacts_manifest.json   # 產物SHA，包含失敗嘗試
```

新的Experiment與factor／run IRI不同，共用原Batch／Frame IRI是Ontology設計，並不互相覆寫。**不複製舊sealed Turtle改名稱、不手寫machine section、不新增虛構Parameter。** 現Ontology唯一定義的Parameter為icpBackend（`ontology/hw1.ttl:412`），`api.py:1340`拒絕未宣告的settingParameter。

所有v、seed、map voxel及派生常數先寫進新宣告的註解／rdfs:label與獨立preregistration；用註解內manifest SHA把Seal與完整參數紀錄連結。封存前完成pipeline／baseline prediction（可寫未知、可能改善或失敗，不倒填預測範圍）。API不會自動把這些註解當執行設定；必須核對argv、函式實際引數與manifest一致。註解未成為可查詢RDF參數的限制須揭露，不修改Ontology來偽裝已支援。

### 6.3 baseline／selected的語意與合規界線

每個候選的新首次全批量測，官方run名稱只能是該實驗的**baseline／FullBatch**；它在研究比較上是「相對M2的參數介入」，不能因名稱baseline就誤稱沒有介入。跨實驗比較用新增研究索引列出歷史M2→B/C/D的關係，不擅用`prov:wasDerivedFrom`串Experiment（既有契約只允許Batch間衍生）。

原M2/M3.1正式workspace已保有合法baseline與selected，兩者完整保留，滿足現有工作流程的兩種run紀錄。新參數敏感度檔預定各有合法首次量測baseline，**不捏造selected、不重跑全選191張只為填欄位**，也不在同一Turtle用不同v／seed讓舊因素對上新run。M3.1的190張selected只作歷史脈絡，不作本研究等樣本主比較。

PDF p.10確實要求baseline／selected；pp.4–8又允許純參數介入。現CLI未提供「參數介入selected＋各run獨立設定／因素」的完整表示。本方案維持既有正式兩run證據，新增條件走官方Declare→First-Pass→Explore→Query，沒有自行改run語意。**不能保證課程若要求每一份敏感度Turtle都同時有兩種run時仍足夠**；若日後有此要求，先向老師／助教釐清或另提最小C級資料模型／流程方案，不先執行假selected來填空，也不宣稱整份作業已最終驗收。

## 7. 未來核准後的正式CLI與觀測方法

**以下僅供審查，這一輪未執行。** 以B1為例；B0/B2/C依第5節逐條替換名稱、v、seed，不從結果生成下一組值。所有命令工作目錄為專案根目錄。

```bash
pixi run --locked -e habitat python api.py declare \
  --name p1_m32_YYYYMMDD_b_v003_s0_01 \
  --data-dir eval/_data/first_floor --floor 1

# 人工／獨立工具先補好新宣告的假說、預測與完整參數註解，再驗證及留存。
# 未封存首次重建自動建立因素、Seal與baseline，不加selection-query／no-write。
OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/physicalai-m32-matplotlib \
.pixi/envs/habitat/bin/python scripts/record_command.py \
  --output research_outputs/m32_p1_m32_YYYYMMDD_b_v003_s0_01/command \
  --rss-limit-gib 3 -- \
  .pixi/envs/habitat/bin/python reconstruct.py \
  --experiment experiments/p1_m32_YYYYMMDD_b_v003_s0_01 \
  --version open3d --voxel-size 0.03 --seed 0 --down-voxel 0.05 --no-vis

pixi run --locked -e habitat python api.py explore \
  experiments/p1_m32_YYYYMMDD_b_v003_s0_01

pixi run --locked -e habitat python api.py query \
  experiments/p1_m32_YYYYMMDD_b_v003_s0_01 \
  --query-file experiments/p1_m32_YYYYMMDD_b_v003_s0_01/queries/audit.rq \
  --format csv
```

官方唯讀影格核對query範本（另設因素身分／完整性查詢，不拿此query做重建選幀）：

```sparql
PREFIX hw1: <http://taica.course/hw1/ontology#>
PREFIX exp: <http://taica.course/hw1/experiment/>
SELECT DISTINCT ?frameIndex WHERE {
  exp:p1_m32_YYYYMMDD_b_v003_s0_01 hw1:onBatch ?batch .
  ?batch hw1:hasFrame ?frame .
  ?frame hw1:frameIndex ?frameIndex .
}
ORDER BY ASC(?frameIndex)
```

上列原生CLI已能產生官方因素與Mean L2，**但沒有完整保存逐對矩陣與逐幀旋轉**。因此完整實驗執行前仍需B級獨立觀測工具：參照M3.1的`runpy`＋`sys.setprofile` return事件方案，呼叫同一未修改的正式CLI並唯讀保存返回值，不替換函式、不改局部變數、不提供GT。資源監控外層仍用record_command；正式重建只能呼叫一次，不能原生跑完再診斷重跑當成同次位姿。

`scripts/m31_ablation.py`目前硬編舊workspace、190張、query且要求Selected尚不存在，**不可直接重用執行**；`m3_diagnose.py`也不是正式新實驗宣告的替代品。新工具未在本次建立，不在文件假造已可用的observe命令。未來先完成其獨立介面與必要的合成測試（參數傳遞、191張、一次呼叫、只讀觀測、拒絕覆寫），再經核准執行；以上原生CLI是其必須保持的實際argv契約。所有B/C條件使用相同觀測成本。

### 前後保全與失敗規則

1. 執行前唯讀驗證RGB與Depth集合皆精確1..191、GT列數191、來源hash；不得只依兩集合交集或runFrameCount就宣稱資料完整。量測剩餘磁碟，包含備份與每條件plots約數十MiB、地圖／位姿／console；不因空間不足刪舊成果。
2. 對原workspace全目錄、所有舊研究產物、原始資料、核心與lock製作SHA清單及必要備份；核對原Seal與baseline／selected子圖。備份與新監控輸出不加入自身保護清單。新輸出目錄採獨占建立，既有名稱立即拒絕；單次執行標記避免重入。
3. RSS護欄沿用3GiB、0.5s取樣；所有條件一致。失敗保留console、部分觀測、資源與原因，不自動放寬護欄／跳幀／改v。若0.03超限，列為resource-limited，Mean L2不可比較；增加資源預算須另核准。
4. CLI／監控／評估任一失敗均列清單。不得把不完整的1522因素、未完成191張或零內點當成功。禁止在原目錄續寫／覆蓋；技術性重試須新attempt並記錄理由，不因GT差而重跑。
5. 結束核對所有舊檔案SHA完全不變，原Seal、baseline及selected仍相同；新因素、Mean L2與位姿同源；保存新完成快照與manifest。若檢查失敗，停止後續實驗，保留證據。

## 8. 預定評估指標與比較判讀

所有候選結果欄目前皆為「未執行」，沒有新Mean L2、時間或資源量測。

| 層次 | 必存指標／方法 | 比較限制 |
|---|---|---|
| 主要結果 | 正式191張Mean L2、相對M2及新B0的差值／百分比；保留率100%、輸入／消耗／評估數各191 | 不額外SE(3)／Sim(3)最佳擬合；不拿190張直接作同集合比較 |
| 局部幾何 | 全190對RANSAC與ICP各自的旋轉／平移誤差；103→104、104→105重點，並檢查所有新失敗 | 時間箭頭i−1→i，實際矩陣為current→previous；新研究不包含103→105配對 |
| 全域傳播 | 每幀L2與旋轉誤差、95–120放大、最大／末張誤差及影格；粗→細修正角與位移 | 避免只修104而其他pair變壞；位置Mean L2不能單獨驗證旋轉正確 |
| 嚴重錯解 | 預先用相對旋轉誤差>150°統計全190對粗／細次數與位置；另列完整連續角度、>90°次數 | 描述性統計，非配準輸入／選幀／品質Pass/Fail；不看結果後換定義 |
| 八項因素 | RawPointCount／VoxelizedPointYield各191；CoarseRANSACFitness／RMSE／Correspondences、ICPInlierFitness／RMSE／Correspondences各190；原精度CSV與官方精度Turtle | 共1522筆；yield是點數不是比例；B的閾值與點集改變，Fitness／RMSE／correspondences不能直接作同定義精度排名 |
| 可比配準支撐 | 可另用固定0.05 m評估點雲、距離0.075 m，套用已估矩陣計算同門檻幾何殘差／比例（離線、不求新轉換） | 額外診斷不是替換八因素；同樣可能被對稱錯解欺騙 |
| 幾何支撐 | 選定95–120與全序列摘要：鄰點數分布、達cap比例、法向量／特徵有效性；可離線依已保存對應分析H的奇異值 | 需先固定離線分析實作；不可用這些事後調參，不把PCA等同Hessian |
| Runtime | 同次純reconstruct wall time與外層程序總時間分開；explore／離線分析另計；記錄觀測、PNG、封存邊界 | 不把舊M3.0 build_cloud=False耗時當新正式建圖基準；單次量測不宣稱顯著效能優勢 |
| 資源 | process peak RSS bytes/GiB、0.5s RSS序列、CPU user/system time、輸出磁碟bytes、退出碼／護欄原因 | record_command現有支援RSS／總時；CPU時間需未來獨立觀測補記，未量測不能填0 |
| 地圖 | 正式去天花板圖、紅估計／黑GT、同座標範圍俯視／側視；合併點數、範圍、錯位／重影／缺口 | 191張觀測相同不保證正確空間覆蓋；錯圖擴張不是改善，minY裁切可能不同 |
| 離線覆蓋代理 | 可沿用M3.1固定0.1 m格網與共同裁切界線的GT定位觀測支撐；各條件觀測相同理應一致 | 非房間全覆蓋率、非配準正確率；不得把GT地圖寫回成果。正式估計圖另作固定視域比較 |

定義：離線先將GT與預測完整姿態置於同一首相機與影像軸座標。`T_GT(i→i−1)=inv(P_GT,i−1) P_GT,i`；旋轉誤差`acos(clip((tr(R_GTᵀ R_est)−1)/2,−1,1))`，平移誤差`||t_est−t_GT||₂`。GT運算前轉float64，遵循M3.0精度修正；Mean L2使用官方同一影格對應與軸向。Turtle七位有效數字與原始float64分開保存，驗證時以API `_storable`比較，不用儲存精度差異推翻一致性。

判讀事先固定：B若僅Fitness上升或RMSE下降而姿態／Mean L2不改善，假說不獲支持；若103→104正確但全序列變差，列為局部成功、整體失敗；若Mean L2降低但旋轉災難仍在，不能宣稱翻轉已解決。C以整組分布與失敗頻率解釋，不挑最佳seed。所有條件與失敗完整列在同一研究索引，未執行／中止不能從分母消失。

## 9. 原始PDF逐項驗證與未來停止點

| PDF要求 | 未來驗證證據 |
|---|---|
| pp.2–3手寫反投影、Voxel／Normals／FPFH、RANSAC→ICP | 核心SHA與已驗收commit一致；正式argv及實際派生引數核對；B/C不改核心 |
| p.10 Open3D Point-to-Plane | `version=open3d`與估計器實際呼叫；不使用Bonus |
| p.4 GT僅評估／首相機系 | CLI重建返回後才載入GT；只做固定首姿態／軸向轉換，不GT初始化、補正或最佳擬合 |
| pp.4–7事先宣告與全批首次量測 | 官方declare產生新workspace；預測與manifest在執行前封存；191張與1522因素唯一身分逐筆驗證 |
| pp.6–8 Turtle、Seal、Explore、SPARQL | 以api.read_experiment核對complete、expected=measured1522、pending0、errors=[]；新experiment explore及query真實輸出；不更新舊plots |
| p.10 baseline／selected紀錄 | 保全原正式兩run；新條件首次量測baseline；純參數selected的模型限制依6.3揭露，不假稱已消除規範歧義 |
| pp.10–12品質、可重現性與指標 | 191張Mean L2、地圖／軌跡、八因素、時間與超參數；來源／版本SHA、資源、失敗及全部候選結果 |

建議核准順序：先B級的通用唯讀觀測與防覆寫工具，再B三條件（含新控制）；再C四個額外seed。B可用現有CLI、具尺度幾何依據且不動教師核心；C辨識是否只是隨機抽樣幸運。D在B/C後另審核心修改與額外5次成本，不將新增工具授權視為核心修改／實驗授權。

完成本文件後停止。下一步需使用者明確核准實際實驗範圍；**尚未建立新實驗宣告、尚未跑候選配準、尚未產生M3.2數值成果，亦未開始Phase 2、Bonus或英文報告**。

## 10. 本輪文件驗證與Git

本輪只新增本MD，屬B級規劃；未修改核心、CLI、API、Ontology、lock、capture或既有成果。作業PDF閱讀／渲染中間檔僅在暫存目錄。文件以原始碼行號、派生值算術、候選去重數量、保護檔案SHA及`git diff --check`檢查；不為純文件變更執行含配準的測試套件。

Git維持main、無remote、不改寫歷史，`snapshot/pre-implementation`維持既有快照；只stage此文件並以單一有意義的小步docs commit保存。後續觀測工具、實驗與分析應各自獨立commit／驗收，不與本次規劃混在一起。

本輪唯讀驗證實測：551個受保護檔案SHA全數未變；原正式Turtle通過Seal解析，complete=True、expected=measured=1522、pending=0、errors=[]；baseline仍191張／儲存Mean L2=3.174055，selected仍190張／4.200398。未執行任何重建或配準測試。
