# M3.1：Phase 1 單一影格排除消融實驗

**結果：流程與證據驗證通過，但改善假說未獲支持。** 僅排除104後，新的103→105仍產生近180°姿態錯解，ICP局部平移誤差達3.5081364 m。正式Selected Mean L2為 **4.200397987245927 m**；共同190張的Baseline為3.1855556038742154 m，Selected增加約 **31.86%**。結果完整保留，沒有追加刪幀或調參。完成M3.1後停止，等待人工確認。

## 研究身分、假說與控制

本次明確標記為 **Exploratory Ablation**。第104張的選擇曾參考M3.0的GT誤差定位，**不是事先建立、完全不依賴GT的通用影格篩選規則**。假說為：排除104、將103直接配準105，可能避開原103→104的錯誤姿態；預先揭露跨幀轉向約20°、105有效深度較少，新配對可能失敗。

唯一資料介入：保留原始 `eval/_data/first_floor/` 的1–103、105–191，共190張；原始首張1保留且置於第一位。沒有改寫RGB、Depth、GT、內參或深度換算；沒有建立第二組介入、參數搜尋、Phase 2或Bonus。

正式實驗沿用 `experiments/p1_baseline_20261118_map005_s0_01/`。核心、CLI、API、Ontology、`pixi.toml`、`pixi.lock` 在前置驗證中逐byte比對正式Baseline執行commit `7fbe9042f3bdfff59a9188a05b4f02eb23ac1f0a`，完全相同。此次執行commit為 `911736e6de7d6d8e7f563740feced1ef1183c37a`，差異為新增獨立工具、查詢、測試與既有紀錄；未修改教師程式。

| 設定 | Baseline與Selected固定值 |
|---|---|
| Capture／內參／深度 | 同一樓層原始191組；512×512、HFOV 90°；uint16毫米，讀取時除1000一次 |
| Backend | Open3D Point-to-Plane ICP |
| Registration voxel／map down_voxel | 0.05 m／0.05 m |
| RANSAC seed | 0；每對均由既有函式設定 |
| Normals | radius=0.1 m、max_nn=30 |
| FPFH | radius=0.25 m、max_nn=100 |
| RANSAC | mutual=True；distance=0.075 m；edge checker=0.9；n=3；max_iteration=100000；confidence=0.999；不估尺度 |
| ICP | distance=0.075 m；100 iterations；relative fitness/RMSE=1e-6；缺法向量時才用radius=0.15 m、max_nn=30 |
| 地圖 | build_cloud=True；既有ceiling margin=1 m |
| GT | 僅於重建回傳後評估；固定首姿態與軸向，不做最佳旋轉、平移、尺度擬合 |
| 環境 | Python3.9.23、Open3D0.18.0、NumPy1.26.4、OpenCV4.8.0.76、SciPy1.13.1、RDFLib7.1.4；完整版本見preregistration.json；OMP_NUM_THREADS=1 |

來源雜湊延用M2定義並重新驗證為 `22270c4923745ffdf9b3a1fbe98bf311ac05721a54e37eec6ff3c16a59e227c2`。計算雜湊只讀取檔案bytes，不把GT陣列提供給配準。

## 官方SPARQL與正式執行

新增且納入Git的查詢：`experiments/p1_baseline_20261118_map005_s0_01/queries/exploratory_ablation_exclude_104.rq`。

```sparql
PREFIX hw1: <http://taica.course/hw1/ontology#>
PREFIX exp: <http://taica.course/hw1/experiment/>
SELECT DISTINCT ?frameIndex WHERE {
  exp:p1_baseline_20261118_map005_s0_01 hw1:onBatch ?batch .
  ?batch hw1:hasFrame ?frame .
  ?frame hw1:frameIndex ?frameIndex .
  FILTER (?frameIndex != 104)
}
ORDER BY ASC(?frameIndex)
```

先由獨立前置工具呼叫原CLI，完整stdout保存在 `research_outputs/m31_20261118_preparation_01/query.stdout.csv`：

```bash
.pixi/envs/habitat/bin/python api.py query \
  experiments/p1_baseline_20261118_map005_s0_01 \
  --query-file experiments/p1_baseline_20261118_map005_s0_01/queries/exploratory_ablation_exclude_104.rq \
  --format csv
```

實測190列，無重複，與「1..191僅排除104」的完整升冪清單逐項相同；首張1、末張191，沒有其他遺漏。另以原 `frames_from_sparql_query()` 核對相同結果。正式CLI再次讀取同一查詢，輸出兩個segments：1..103(103)、105..191(87)。實際仍連成同一條軌跡，沒有在第二個segment重設姿態；觀測紀錄確認新配對為103→105。

正式入口及參數如下，**必須加 `--write`**；未加時sealed experiment預設不回寫run：

```bash
.pixi/envs/habitat/bin/python reconstruct.py \
  --experiment experiments/p1_baseline_20261118_map005_s0_01 \
  --selection-query experiments/p1_baseline_20261118_map005_s0_01/queries/exploratory_ablation_exclude_104.rq \
  --version open3d --voxel-size 0.05 --seed 0 --down-voxel 0.05 \
  --no-vis --write
```

為在**同一次正式執行**取得新配對與全域位姿，新增B級獨立工具 `scripts/m31_ablation.py`。它以 `runpy.run_path(..., run_name="__main__")` 執行上述未修改的 `reconstruct.py`，將相同旗標設為argv。使用標準Python `sys.setprofile`，只讀取 `preprocess_point_cloud`、`local_icp_algorithm`、`reconstruct`、評估函式的return事件；沒有替換函式、改動局部變數、插入配準初值或重用Baseline轉換。測試已將觀測結果與原生callbacks逐值比較。工具不接收GT作為配準輸入，GT仍由正式CLI在重建之後評估。

實際啟動命令與M2相同的外層資源監控如下；已保存完整argv、stdout/stderr、時間及每0.5秒RSS：

```bash
.pixi/envs/habitat/bin/python scripts/m31_ablation.py prepare \
  --output research_outputs/m31_20261118_preparation_01

MPLCONFIGDIR=/tmp/physicalai-m31-matplotlib \
.pixi/envs/habitat/bin/python scripts/record_command.py \
  --output research_outputs/m31_20261118_official_command_01 \
  --rss-limit-gib 3 -- \
  .pixi/envs/habitat/bin/python scripts/m31_ablation.py observe \
  --preparation research_outputs/m31_20261118_preparation_01 \
  --output research_outputs/m31_20261118_official_observation_01

MPLCONFIGDIR=/tmp/physicalai-m31-matplotlib \
.pixi/envs/habitat/bin/python scripts/m31_analysis.py \
  --output research_outputs/m31_20261118_analysis_01
```

真正 `utils.reconstruct()` 呼叫次數為 **1**，成功處理190張、189對。觀測工具於重建return時即保存預測中心與地圖取樣，再讓原CLI進行GT評估、輸出圖片與 `api.write_run()`。共有190個frame events、189個pair events，對應 **1514筆本次實際因素**；新103→105的矩陣及六項因素全部由本次實際配準取得。前置紀錄另以獨占建立的執行標記禁止同一準備目錄重跑；本次未觸發任何重試。

## 數值結果與共同影格比較

| 指標 | Baseline | Selected：僅排除104 |
|---|---:|---:|
| 正式重建／評估張數 | 191／191 | 190／190 |
| 正式Mean L2 (m) | **3.174055104788137** | **4.200397987245927** |
| 共同190張Mean L2 (m) | **3.1855556038742154** | **4.200397987245927** |
| 影格保留比例 | 100% | 99.4764398% |
| 第105張全域L2 (m) | 0.7503015 | 3.5183045 |
| 第191張全域L2 (m) | 5.7959827 | 18.2485176 |
| 第105張全域旋轉誤差 (°) | 179.6760501 | 179.6173914 |
| 第191張全域旋轉誤差 (°) | 179.8296257 | 179.8782716 |
| 全程序時間 (s) | 286.378044 | 337.811952 |
| 程序峰值RSS (bytes／GiB) | 891551744／0.830322 | 902840320／0.840836 |

共同影格比較增加 **1.0148423834 m（31.8576%）**。正式191與190張平均數的樣本不同，因此以共同190張的增加作主要比較。Selected的官方評估原始值、離線重算與Turtle序列化精度一致，Turtle中存為 `4.200398`。

Baseline正式CLI當時沒有保存逐幀位姿；共同190張與個別位姿沿用M3.0完整相符的診斷軌跡，**不是本次重新執行Baseline**。M3.0的191張平均與正式值完全相同，1522筆因素相符；本次再次核對所使用的中心與轉換鏈一致，保留這個來源限制。Selected逐幀位姿則直接來自本次正式CLI，沒有另做Selected診斷重跑。

本次純重建函式時間（含return觀測）為 **317.742185 s**，外層337.811952 s另含啟動、查詢、保存地圖取樣、正式評估／PNG、Turtle寫入與驗證。觀測回呼內量到約1.404321 s，但不涵蓋全部profiler dispatch成本，不能據此扣除成「完全無觀測的速度」。M2沒有同樣觀測、字型快取狀態也不同；本次執行中另有一次合成測試短暫並行，背景負載未嚴格控制。因此時間與RSS均如實列為當次實測，**不把全部時間差歸因於排除104，也不宣稱效能改善**。3 GiB護欄未觸發，0.5秒取樣峰值893878272 bytes，退出碼0。

## 新103→105配對與翻轉

本文箭頭依影格時間順序命名；配準矩陣實際將目前105的相機座標轉到前一個保留影格103的相機座標，與GT相對位姿採相同方向。

GT的103→105中心平移約0 m、旋轉19.9999979°。本次預測ICP平移3.5081364 m、旋轉量179.8570056°。

| 新配對量測 | RANSAC | ICP |
|---|---:|---:|
| Fitness | 0.4616513163 | 0.7069850844 |
| Inlier RMSE (m) | 0.0357464027 | 0.0342009757 |
| Correspondences | 5664 | 8674 |
| 相對平移誤差 (m) | 3.5878044768 | **3.5081363678** |
| 相對旋轉誤差 (°) | 178.4763801067 | **179.8270089851** |

ICP相對RANSAC初值改變1.2843065 m、41.6293149°；Fitness及對應數提高、RMSE稍降，但物理姿態仍嚴重錯誤。這再次顯示內部配準一致性不等於真實位姿正確。原Baseline的103→104與104→105結果沒有被拿來當作103→105量測。

Selected唯一接近180°的**局部旋轉誤差**位於新配對103→105；此後105–191的87張全域旋轉誤差都接近180°，最大179.9783051°。這裡以>150°作描述性檢查並提供原始最大值，沒有用此條件控制配準或選幀。新配對的旋轉殘差軸約 `[0.9916,0.01575,0.1286]`，與M3.0原失敗對的殘差軸不同，因此不宣稱兩次是完全相同的旋轉解；兩者都屬嚴重錯解。

190張的兩條軌跡在1–103的完整4×4位姿最大差為 **0**。與Baseline共同存在的188對，RANSAC與ICP矩陣最大逐元素差均 **0**，1128個pair因素亦完全相同；190張保留影格的兩個單幀因素也逐值相同。只有原103→104、104→105被一個新103→105取代。故本次後段差異可定位到新的鄰接配準，並非後續每個pair重新隨機失敗。

純離線檢查 `D=P_selected105 inverse(P_baseline105)` 後，所有105–191的保存位姿均滿足 `P_selected_i≈D P_baseline_i`，最大矩陣殘差約7.1e-15。這只是在解釋轉換鏈差異，**D沒有被用來補正任何軌跡**。因新的錯誤姿態及位置不同，後續相同局部運動在不同共同座標方向傳播，最終L2達18.2485 m。

## 第105與191張的全域姿態

以下為「相機→原始首相機」影像座標（X右、Y下、Z前）。四元數順序為 `(qx,qy,qz,qw)`；q與−q代表同一旋轉。完整4×4矩陣見 `global_pose_details.json`、`poses_offline.npz`。

| 影格／來源 | 相機中心XYZ (m) | 旋轉四元數xyzw |
|---|---|---|
| 105 Baseline診斷 | (3.937482, 0.728617, −7.575752) | (0.991945, −0.002827, 0.126336, −0.008709) |
| 105 Selected實際 | (5.010601, 0.779843, −10.798966) | (−0.125346, −0.003339, 0.991939, 0.018269) |
| 105 GT評估 | (3.760643, 0, −7.603983) | (0, 1, 0, ≈0) |
| 191 Baseline診斷 | (5.822515, 0.569567, 0.147966) | (−0.528887, −0.009436, 0.848618, 0.006040) |
| 191 Selected實際 | (3.112358, 0.920013, −18.519814) | (0.849062, −0.018156, 0.527930, 0.007294) |
| 191 GT評估 | (0.096457, 0, −0.545768) | (0, 0.422618, 0, 0.906308) |

## 觀測保留程度與地圖覆蓋限制

輸入有效深度點總數由47662199減為47451796（保留99.5586%）；逐幀0.05 m voxel點數總和由3809250減為3798268（保留99.7117%）。這些是單幀觀測的加總，不是地圖的唯一點或覆蓋率。

另以GT**僅作離線評估參考**，將原始各影格0.05 m map voxel觀測放到固定首相機座標，兩組使用相同天花板評估界線（Y>−0.50403515625 m），以0.1 m固定格網比較觀測支撐。此0.1 m只供評估，**不是更動registration voxel或map down_voxel**。

- 完整191張觀測支撐34637格；排除104後34615格。
- 只有104支撐、其他190張未支撐者為22格；保留原已觀測格網的 **99.9364841%**。
- 此結果支持「只刪一張並未大幅減少此解析度下的觀測支撐」，**不能解讀為實際樓層覆蓋99.94%或地圖正確率99.94%**。沒有完整場景表面GT，也未量測全部房間涵蓋百分比；孔洞、雜訊與格網解析度仍影響此代理指標。

Selected實際合併且裁天花板後有2894142點；以固定stride=20保存144708點供檢視。實際範圍約X=[−3.0263,8.6706]、Y=[−0.4843,2.1232]、Z=[−22.9591,4.7106] m。俯視圖顯示後段被放到錯誤的延伸區域；更多或更廣的點雲不代表更完整的正確地圖。

官方Baseline PNG與Selected PNG並列保留，但各自採自動範圍且原helper只顯示約5000個地圖點，不能用圖片像素面積直接計算覆蓋差。補充圖另以相同座標範圍比較Selected實際地圖取樣與GT定位的保留觀測，顯示錯位。未以GT改寫正式地圖，也未重新估計Baseline配準或建立新Baseline Run。

## Turtle、Seal及既有檔案保全

執行前逐檔備份整個官方workspace（含原TTL、Baseline圖、通用圖、Dashboard HTML與查詢），另保存505個既有來源／實驗檔案SHA。已閱讀並測試API寫入路徑：只替換selected節點指定屬性，Declaration原bytes直接保留；其餘machine graph可能重新排序序列化，因此除全檔SHA外，同時驗證RDF內容。

| 驗證 | 執行前→後 |
|---|---|
| TTL SHA-256 | `5ee9f6c35c61bfe5ccabb068bc4fb18fce54fbd4005465645e925ce5a2192bb6` → `bba92ffc4a031772a8b1b6bc80dc3056b0c103a1b0382784c3c82d4edc3eb4b6`（新增Selected後預期改變） |
| Declaration bytes SHA／Seal | 均為 `3306cd6f0729b45b9583edcf31772df314b18347487621dc1b2eec84c8e09ab5`，完全相同、Seal有效 |
| Baseline Run子圖SHA | 均為 `ebf1bc5d48ad83ac86d8def01dd96993454295558638b1cf6de9fa627af1805b` |
| 排除新增Selected後的整張RDF圖SHA | 均為 `ea7828f4427bf18873e69a449181b2dd1906f136b3b768916ff3b7097c3ad8af` |
| 原始因素 | complete=True，1522筆保留，原Baseline Run仍為191張、Mean L2=3.174055（儲存精度） |
| 新Selected | 真實存在、190個usedFrame、runFrameCount=190、Mean L2=4.200398 |
| Selected機制中繼資料 | spliceCount=1、maxGapLength=1（缺一張，不是角度） |
| 既有檔案差異 | 505個中僅原TTL及通用 `reconstruction.png` 依正式CLI預期更新；其他503個雜湊不變 |
| 原始capture與教師核心 | 均未變 |

原API將selected的selectionMode命名為 `hw1:GoodSegments`；這是既有模式名稱，不代表本次品質通過。正式Turtle仍保存**Baseline的1522筆因素**，不把這些因素冒充Selected新配對的結果。本次Selected的1514筆實際因素與189對矩陣獨立存於研究目錄，未修改Ontology、未覆蓋Baseline因素。正式Selected Run只使用現有API支援的結果與影格／缺口欄位。

`reconstruction_baseline.png`及原Dashboard保持不變；CLI更新通用圖並新增 `reconstruction_selected.png`。原通用Baseline圖已備份，執行後TTL與Selected圖另存 `analysis_01/official_after/`，避免未來其他授權實驗覆蓋目前結果。原M2 Dashboard是歷史Baseline檢視，本次沒有重跑Explore覆寫它，不將其當作已包含Selected的新Dashboard。

## 產物與驗證

| 位置 | 證據 |
|---|---|
| `research_outputs/m31_20261118_preparation_01/` | 實驗前登記、完整官方檔案備份、Turtle／Seal／Baseline子圖SHA、505檔案清單、官方query CSV與stderr、單次執行標記 |
| `research_outputs/m31_20261118_official_command_01/` | 真正執行命令、console、execution.json、0.5秒RSS取樣；兩次Open3D回退警告762／460完整保留，未擅自指定影格來源 |
| `research_outputs/m31_20261118_official_observation_01/` | 實際函式參數、190個中心、189對粗／細矩陣及因素、地圖點數／取樣、官方原始評估值、單次呼叫證明 |
| `research_outputs/m31_20261118_analysis_01/` | 共同190張逐幀誤差、Selected逐對誤差、1514筆實際因素CSV、離線GT與完整位姿、覆蓋代理格網、完整摘要與Turtle驗證、正式結果備份 |
| `analysis_01/common_frame_comparison.png` | 共同190張L2、對數刻度及全域旋轉誤差對照 |
| `analysis_01/selected_relative_errors.png` | 所有Selected配對RANSAC／ICP的局部平移及旋轉誤差 |
| `analysis_01/trajectory_comparison.png` | 固定首姿態座標的Baseline／Selected／GT軌跡 |
| `analysis_01/official_map_comparison.png` | 原官方兩張地圖／軌跡圖片並列 |
| `analysis_01/selected_map_reference.png` | Selected實際地圖取樣與離線GT定位觀測的同範圍比較 |
| `analysis_01/global_pose_details.json` | 第105、191張的Baseline診斷／Selected實際／GT完整4×4矩陣與四元數 |
| `analysis_01/post_splice_transform_check.json` | 後段位姿差異的純離線代數檢查，未套用補正 |
| `analysis_01/final_integrity.json`、`analysis_01/artifacts_manifest.json` | 完成後再次驗證來源／Seal／原Baseline、實際參數、單次執行與產物SHA清單 |

上表 `analysis_01/` 縮寫均指 `research_outputs/m31_20261118_analysis_01/`。5張比較圖均已實際檢視。所有正式結果與研究產物均未加入Git。

```bash
.pixi/envs/habitat/bin/python -m pytest -q
# 163 passed in 12.94s
git diff --check
```

新增9項測試涵蓋：真實SPARQL在合成191張圖上的精確選取、拒絕額外排除／重複／錯序、唯讀觀測與真實callbacks一致且不碰GT、正式API寫入後保全原sealed Baseline並能偵測Baseline遭改寫、離線格網負座標與共享觀測。合成資料均在pytest暫存目錄，不是正式實驗。

Git持續於main，`snapshot/pre-implementation`仍為 `291209750bd8ecf84f337112c9b92307e6be192a`，沒有新增remote或改寫歷史。`911736e`保存查詢、前置／觀測工具與測試；`3736858`保存離線分析與覆蓋測試；另以文件提交保存本驗收紀錄。查詢可追蹤，正式TTL、PNG及研究產物維持既有忽略規則。

## 結論與停止點

此次受控單次消融**未能避免翻轉，反而造成更差的共同影格Mean L2與末張誤差**。資料支持「排除104並不足以解決這個局部配準問題，103→105也有錯解風險」。它不能證明104完全無影響、所有抽幀都會失敗，或近平面／深度缺失已被確認為唯一原因；角度、視野與幾何支撐在新配對同時改變，不能獨立歸因於20°或105的缺深度。

**M3.1工作完成，負面結果保留，停止等待使用者確認。未排除105／106或其他影格，未調整任何配準參數，未進行第二組Intervention、Phase 2或Bonus。**
