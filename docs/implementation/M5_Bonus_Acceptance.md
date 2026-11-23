# M5 Bonus：自製 ICP 實作與四組重建驗收

日期：2026-11-19（臺灣）。狀態：**自製核心、四組重建、歷史比較與報告素材完成；四組各一次，沒有額外 Open3D、seed 或 voxel 重建。最終英文 report.pdf 與繳交 ZIP 尚未製作。**

本次使用者確認一樓最佳採 C1；原 Open3D ICP 不得刪除或改寫。規劃與方法詳見 [M5_Bonus_Plan.md](M5_Bonus_Plan.md)。較早交接文件中的「Bonus 未實作」是其當時歷史狀態，本文件記錄這次新增成果，未改寫歷史證據。

## 實作與原 ICP 保全

- `utils.my_local_icp_algorithm` 完成 Point-to-Point ICP：cKDTree 最近鄰查詢、0.075 m 距離過濾、Kabsch SVD與反射校正、左乘增量、最終對應與Fitness／RMSE重新計算、明確失敗回報。
- v=0.05 m、最多60次、平均內點距離絕對變化 < 1e-6 m、至少10組對應；退化支撐拒絕。單次固定目標只建一次樹，不建立全點對距離矩陣。
- SciPy提供索引／查詢，NumPy提供SVD；ICP核心自行組成，未呼叫Open3D ICP。保留教師原有TODO註解並補充採用Point-to-Point的說明。
- `local_icp_algorithm` 的說明、註解、程式碼逐字保持。原文字保存在 `research_outputs/m5_bonus_01/original_local_icp_algorithm.txt`，SHA綁定於plan，另有逐字比較測試。
- `reconstruct()`只開通合法`my_icp`分支與自製失敗檢查；正式預設仍是Open3D。`reconstruct.py`、`api.py`、Ontology及Pixi未修改。
- GT只在重建完成後評估；首相機固定、current→previous矩陣右乘累積，不以GT重新擬合軌跡。

## 四組實際結果

全部配準voxel及地圖voxel均為0.05 m。C1 seed=1，其餘seed=0。二樓Selected沿用原sparse-v1的204個索引，沒有使用新因素重新選幀。

|條件|影格|歷史Open3D Mean L2(m)|自製Mean L2(m)|歷史記錄時間(s)|自製worker時間(s)|自製ICP合計(s)|
|---|---:|---:|---:|---:|---:|---:|
|一樓Baseline|191|3.174055105|3.311659411|286.378044|327.497501|37.206668|
|一樓C1|191|0.155696710|0.409296607|301.956052|334.586786|37.768441|
|二樓Baseline|320|0.070258452|0.607971606|220.751497|264.268851|35.227153|
|二樓sparse-v1|204|0.044872589|0.347112042|163.365969|190.338741|25.581903|

四組自製版本的Mean L2與本次記錄時間皆高於相應歷史Open3D結果。這是本次實驗觀察；Point-to-Point／Point-to-Plane目標、60／100次預算、停止條件、歷史時段及觀測邊界不同，不能全部歸因於純粹實作效率，亦不宣稱統計顯著性或純ICP加速比。歷史沒有純ICP計時，不填推估值。

自製重建函式時間依序314.404672、321.478018、243.882403、167.005967秒，含讀取、前處理、RANSAC、ICP、地圖整合及觀測，止於完整地圖匯出前。ICP計時包含驗證、陣列準備、樹建立、搜尋、SVD與最終指標，保留Python profile觀測成本。worker另含匯入、宣告／查核、匯出、評估、圖像與Turtle。Preflight、後續Explore／分析／報告繪圖不計入worker。

程序樹RSS取樣峰值依序0.798157、0.933731、0.947296、0.844681 GiB；每0.5秒取樣，四次監測皆passed、exit=0，watchdog正常解除。3 GiB是取樣護欄，不是作業系統硬上限，也不保證捕捉瞬間峰值。

## 比較與可支持的結論

**配準初值控制。** 四組190／190／319／203對，共902對RANSAC初值，與各自歷史來源逐元素完全一致，最大差0。共同前處理與初值受到控制；ICP形式與預算仍未分離，不能聲稱單一因素的獨立因果效果。

**局部RMSE不代表軌跡準確。** 四組自製平均歐氏ICP RMSE依序0.020181519、0.020104013、0.018607169、0.019449239 m，皆低於對應歷史平均值0.020875943、0.020875893、0.019343976、0.020180158 m，但Mean L2全部較高。這支持內部最近鄰殘差不保證真實全域姿態準確；這些RMSE也不是Point-to-Plane的平面目標函數值。

**一樓103→104。** Baseline的RANSAC旋轉誤差176.074504°；自製ICP後176.306192°，未救回錯解。歷史Open3D後179.778159°也未救回。C1該對RANSAC為0.539919°，自製後0.670734°、歷史Open3D後0.171590°。逐張曲線亦顯示C1在此之前已逐步累積較多誤差，不能把所有差異都歸於單一配對。

**二樓密度比較。** 在相同204索引上，自製完整批次Mean L2為0.609551477 m，自製Selected為0.347112042 m；歷史Open3D相同指標為0.071709497與0.044872589 m。自製後端也觀察到降低密度組誤差較低、記錄時間較短，但完整批次用了更多影格，這不是相同資訊量比較，亦不代表所有場景降低密度都有益。

**終止原因。** 902對皆有有效支撐；899對達平均距離變化停止條件，3對達60次更新上限（C1、二樓Baseline、Selected各1對）。有效回傳不等於每對均達收斂條件，也不等於GT姿態正確。

**地圖目視。** 一樓Baseline後段紅黑軌跡明顯分離；C1布局較接近GT，但自製版仍見邊界與軌跡偏移。二樓兩組可辨識中央連接與多段邊界，自製版軌跡分離、邊界偏移／散開較明顯。沒有逐房間路線註記或完整表面GT，不編造房間名稱、絕對完整率或所有表面皆已涵蓋的結論。

## 實驗紀錄、完整產物與歷史保全

|新實驗|新Run|封存因素|
|---|---|---:|
|`experiments/bonus_f1_baseline_01/`|Baseline|1522|
|`experiments/bonus_f1_c1_01/`|Baseline|1522|
|`experiments/bonus_f2_baseline_01/`|Baseline＋Selected|2554個Baseline因素|

四組同次觀測共7224筆，其中Selected的新1626筆保存在自己的Observer，不覆寫封存的2554筆Baseline因素。新增Selected前後declaration bytes相同，移除Selected子圖後的圖同構；沒有用Turtle解析器的空白節點臨時ID錯判改動。

主目錄：`research_outputs/m5_bonus_01/`。四個條件各保存 `observation/map_points.npy`、`map_colors.npy`、`camera_poses.npy`、`positions.npy`、`pairwise_ransac.npy`、`pairwise_icp.npy`、原始因素／配對／計時JSONL、原生圖與同次Turtle快照。四組完整去天花板地圖點數依序2,822,856、2,538,660、2,149,788、1,406,769；不是未降採樣深度像素數或全樓層完整率。

受保護1282個既有檔案於執行前、各組結束及離線分析後皆SHA相符。保護範圍包含兩批輸入、所有既有experiments、必要歷史研究來源、Ontology、Pixi與凍結規則。原始／歷史成果未覆寫。新二樓共享PNG更新前，Baseline圖片與Turtle已另存於本次Baseline輸出。

一樓原M2沒有同次完整點雲或位姿；比較保留原生圖，軌跡／RANSAC採先前核對相符的M3.0診斷並在圖中標註，未冒稱原M2完整地圖。C1歷史地圖只有stride保存樣本。二樓歷史兩組有同次完整地圖。共同視角圖使用固定首相機、共同X/Z範圍與等比例，沒有GT擬合或裁掉錯誤軌跡。

## 圖表、報告素材與測試

- `analysis/comparison.csv`：完整誤差、時間、指標、記憶體、RANSAC一致性與設定表。
- `analysis/per_frame_l2.csv`、`pairs.csv`、`frame103_104_diagnostics.csv`：逐張與逐對證據。
- `analysis/summary.json`、`selected_preservation.json`、`sources.json`、`manifest.json`：比較、共同索引與來源查核。
- **報告圖片使用 `report_assets/figures/`**：22張，含四組地圖／原生對照、3D、八因素、跨條件地圖、逐張L2、疊代數與記錄時間。英文圖說為`report_assets/figure_captions.md`。
- 原分析四張3D草稿的高度軸標籤裁切，原圖保留；`scripts/m5_report_assets.py`只從保存地圖重新排版顯示，沒有配準、融合或改變點／位姿。其餘18圖逐bytes複製，修正後四張均已目視確認標籤完整。
- 完整回歸測試301 passed、6 skipped；該6項為沙箱無ps權限的原生監測案例，後續取得權限後監測套件16項全通過（含這6項）。另新增非單位初值與離群值2項測試，自製套件最終12項通過。跨這些執行共涵蓋309個不同案例，不冒稱為一次完整309測試執行。
- 合成官方CLI涵蓋Custom Baseline→Selected、Seal／因素保留、完整同次保存；核心測試涵蓋已知剛體、左乘更新、反射、離群值、退化／不足支撐、非法輸入、不呼叫Open3D ICP及原函式逐字保全。未執行第三方或互動擷取測試。

本次Bonus技術工作與比較素材完成。最終英文報告整併、提交README整體整理與ZIP仍屬後續提交準備。
