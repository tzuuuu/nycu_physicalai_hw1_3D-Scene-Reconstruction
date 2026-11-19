# M4.2 — P2-A First-Pass Baseline 正式驗收

日期：2026-11-19（臺灣）。

**M4.2 — P2-A Baseline Accepted / Scientific Results Preserved / Report Assets Verified / Complete / Stopped**

工程準備完成、全部必要 Preflight 通過、使用者另行授權的一次重跑已成功完成，正式 Turtle、Seal、八項因素與 FullBatch Baseline Run 驗證通過。本文件確認 Baseline 技術驗收，不代表已量出全樓層表面的絕對完整率。未開始 P2-B、P2-C、其他 seed／voxel、Experiment D、Bonus、最終英文報告或 Submission ZIP。

## 1. 授權、執行歷史與來源

M4.1 正式來源為 [恢復驗收](M4_Phase2_P2A_Capture_Acceptance_Resume.md) 與其 Frozen Manifest／Provenance；原始停止及自我雜湊缺陷紀錄不變。另參照 [Phase 1 交接](Phase1_Final_Handoff.md)、[Phase 2 計畫](M4_Phase2_Capture_Plan.md) 與作業 PDF。

必須區分下列歷史，不將本次成功冒稱從未失敗或只有一次程序啟動：

1. 原工程提交 `dcb88fc` 的首次 Terminal Preflight 有24項測試通過、3項清理測試失敗，未啟動正式重建。macOS對已終止但未回收的群組重複送SIGKILL可能回傳EPERM；經最小案例／先紅後綠測試修正，輔助工具提交為 **`37f3bef6d4596f69c4685e4a647afd386f1ed2bd`**。只有確認全為殭屍程序，或核心確認群組已不存在，才能接受這種EPERM；存活或資訊不足仍停止。
2. `m42_preflight_20261119T073112Z_21735c0c` 通過後，第一次正式執行遭使用者誤按鍵盤中止；記錄為 KeyboardInterrupt，最後開始244→245，已取得243對完整配準回傳。無完整Mean L2、回傳地圖、Seal或Baseline Run；不能稱為配準失敗或完整成功。原收據誤標「重建前停止」的事實也保留於封存稽核。
3. 使用者明確要求清除中止產物並再執行一次。先逐檔驗證封存，再移除兩個中止的正式路徑；證據位於 `research_outputs/m42_interrupted_attempt_01/`，重跑授權位於 `research_outputs/m42_retry_after_interrupt_01/authorization.json`。沒有刪除原始Capture或歷史科學成果。
4. 本次成功執行使用 `m42_preflight_20261119T073845Z_38de4a1b`；13項必要檢查全部通過，其中原生自我測試 **31 passed、0 failed、0 skipped**。執行時main乾淨、HEAD為37f3bef，Snapshot仍為 `291209750bd8ecf84f337112c9b92307e6be192a`。這是一次明確另行授權的重跑，非自動反覆嘗試。

初始工程證據、監測器修正證據分別保留於 `research_outputs/m42_engineering_01/`、`research_outputs/m42_monitor_cleanup_fix_01/`。歷史Ready／Manifest／失敗Preflight不改寫；教師核心、Ontology、Pixi與Capture不變。

## 2. 正式設定與成果

正式Experiment：`experiments/p2_114753116_a01_baseline_01/`。

正式來源：`eval/_data/second_floor/114753116/P2_A_01`，原始RGB／Depth各320張，GT與內參各1份，共642項Frozen Scientific SHA。使用全部原影格1..320、原首相機參考，不先選影格。

|項目|驗收結果|
|---|---|
|Floor／影格／相鄰對|2／320／319|
|Registration voxel／RANSAC seed|0.05m／0|
|ICP／執行緒|Open3D Point-to-Plane／OMP_NUM_THREADS=1|
|地圖降採樣|每影格地圖副本0.05m，不改配準點雲|
|八因素|2×320＋6×319＝2554筆，與同次Observer逐筆一致|
|Mean L2 Distance|**0.07025845236530649m**，約7.03cm|
|L2中位數／p95|0.06924077146919774m／0.1929482532833787m|
|最大L2|0.28314248670728553m，第320張|
|完整重建worker時間|220.751497秒|
|其中重建函式觀測時間|207.318515709秒；Observer額外觀測計時約0.525915282秒|
|結果驗證／Explore／圖表worker時間|15.232126375秒，與重建時間分列|
|正式程序樹RSS取樣峰值|1,198,620,672 bytes，約1.116GiB；438筆取樣|
|後處理程序樹RSS取樣峰值|901,513,216 bytes；31筆取樣|
|退出／監測|兩個worker皆exit=0、reason=null，watchdog均於負載結束後解除|
|正式Turtle／Seal／Baseline|合法、Seal驗證有效、唯一FullBatch Baseline Run，320張|
|官方Explore／Query|4份HTML已產生；唯讀官方Query精確回傳1..320，TTL未變|

重建worker時間包含匯入、同次觀測、完整輸出、正式評估、原生圖片、封存與Baseline寫入；不包含Preflight與後續獨立結案。不同歷史runtime邊界不可直接當成純演算法加速。GT只供離線描述／評估，未作RANSAC初值、挑選影格或結果最佳擬合。

## 3. 同次完整保存與保全

正式產物：`research_outputs/m42_p2_a01_baseline_01/`。獨立結案與視覺檢查：`research_outputs/m42_p2a_closeout_01/`。

- `observation/camera_poses.npy`：float64 (320,4,4)，首影格相機為固定參考；`positions.npy`：float64 (320,3)，與同次Pipeline回傳中心一致。
- `pairwise_ransac.npy`、`pairwise_icp.npy`：各float64 (319,4,4)，current→previous；索引與真實品質回傳保存在JSONL，位姿為同次ICP矩陣右乘累積。dtype、shape、座標與SHA另存 `trajectory_metadata.json`。
- `map_points.npy`、`map_colors.npy`：各float64 (2,054,529,3)，**同次正式回傳地圖全部點／色**，首相機X右／Y下／Z前。官方去天花板規則為Y > min(Y)+1m；不是未降採樣的原始全部深度像素，也不是15萬點樣本。
- 完整地圖以不壓縮NPY串流保存，不使用大型壓縮緩衝。繪圖另以stride=14顯示146,753點；點數與SHA見 `map_summary.json`，抽樣沒有替代正式地圖。
- 完整地圖點SHA：`6df80b8c8ed4f548f6cac5273fda69825eac023d4c71c5e9740d9b93cf5056e8`；顏色SHA：`786538d79e22a60ea4b250254d35bda561c2ce5ef63ccf73472b9777a67b1bbb`。

本次獨立結案先嚴格驗證原正式Manifest的62項快照（含Runner當時產生的本文件版本），再重新驗證642項Frozen Capture、核心／Ontology／Pixi、1996項執行前受保護科學檔案、中止封存與重跑授權、同次因素／Seal／Run、位姿與地圖SHA。全部通過。Runner原產生文件bytes另存 `m42_p2a_closeout_01/runner_generated_acceptance_original.md`；原Manifest中的文件SHA指向該歷史快照，本次最終文件由新結案Manifest及Git提交另外綁定，沒有覆寫舊SHA讓它假通過。

新M4.2科學來源嚴格比對；`.DS_Store`僅在檔名、一般檔案／非連結、版本1／Bud1檔頭及Finder類型均確認後，另列前後存在狀態與SHA。未知檔案不自動歸入中繼資料。保留所有舊停止與精確例外，不更改全域歷史驗證器。Manifest不雜湊自身。

監測以ps讀PID／PPID／PGID／RSS／狀態，加總整個負載程序樹，保留父程序退出後的群組成員，超限或觀測失效終止本次群組。RSS每0.5秒取樣，正式取樣最大間隔約0.530秒；共享頁可能重複計算，且不能保證瞬間峰值不超限。獨立watchdog失聯timeout=8秒；監測器與watchdog自身不算入科學負載群組。容量規劃不是記憶體硬上限，正式護欄未取消。

## 4. 圖片檢視、缺失與報告素材

已檢視完整俯視、3D、四個空間分區、Per-frame L2與八因素圖。地圖可辨識下端封閉區、中央連通區、低X側寬廣區、右側數個矩形區及高Z端區。這些只是座標／可見幾何描述，不編造房間名稱或逐段路線。

|空間範圍|可見結果與限制|
|---|---|
|低X／低Z|下端邊界與中央進路可辨識；外側留白不能直接當成可到達房間漏建|
|高X／低Z|多段矩形邊界與內部結構可見；仍有留白與稀疏表面|
|低X／高Z|寬廣區與中央連接可辨識；部分邊界呈較散的點帶|
|高X／高Z|上端區與右側分支可辨識；上端紅／黑軌跡的分離最明顯|

下端與中央多數紅色估計軌跡接近黑色GT。L2呈累積漂移，約130–150張上升，297–320張更明顯；最大值在320張。局部配準皆有有效支援，不代表累積誤差為零。最低Coarse／ICP Fitness在第148張，分別0.7389817／0.7323405；這是量測描述，不是自動排除門檻。

留白／稀疏可能來自未觀測、真實空間、遮蔽、深度、去天花板或顯示抽樣，現有圖像不能單獨區分。缺少逐段route_notes與完整表面GT；不宣稱每個可到達房間或所有表面都已正確重建，也不提供絕對完整率。

正式圖表與完整數據：

- 原正式目錄 `figures/reconstruction_top_down.png`、`reconstruction_3d.png`、`spatial_regions.png`、`per_frame_l2.png`、`eight_quality_factors.png`。
- 原3D圖垂直標籤部分被裁切，原檔保留；結案目錄另存 `reconstruction_3d_report.png`，只調整相同地圖／軌跡的顯示視角、軸比例與標籤邊距，未重新配準、修圖補面或擬合GT。新圖已視覺檢查，來源SHA與繪圖參數另存。
- `factors.csv`、`factor_statistics.json`、`per_frame_l2.csv`、`baseline_comparison.csv`、`all_run_comparison.csv`及官方 `plots/*.html` 可供英文報告使用；本階段沒有撰寫最終英文報告。

|Baseline|影格|Mean L2 (m)|記錄時間 (s)|voxel／seed|
|---|---:|---:|---:|---|
|Phase 1 M2|191|3.174055104788137|286.378044|0.05m／0|
|Phase 2 P2-A本次|320|0.07025845236530649|220.751497|0.05m／0|

完整歷史比較含Selected與各條件在all_run_comparison.csv。兩樓層資料、長度、路線及時間邊界不同，不能由此表宣稱演算法改善比例、顯著加速或參數普遍最優。

## 5. 候選研究問題與停止

僅整理候選問題：148張附近較低支援是否與幾何或視角有關？末段297–320在仍有相當對應點時為何漂移增加？稀疏／散邊界與採集視角、深度或繪圖取樣的關係為何？完整問題與限制見正式 `candidate_questions.md` 及結案 `visual_review.md`。未制定選取門檻、未輸出Selected批次、未開始P2-B；未依GT尋找最佳影格或參數。

**工程準備已完成；必要Preflight已通過；另行授權的正式First-Pass已執行且成功；M4.2 Baseline驗收通過並停止。**
