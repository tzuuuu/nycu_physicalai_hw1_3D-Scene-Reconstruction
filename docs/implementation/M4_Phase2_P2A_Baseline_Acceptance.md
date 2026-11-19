# M4.2 — P2-A First-Pass Baseline 工程交付與待執行驗收

日期：2026-11-19（臺灣）。

**工程工具已實作；沙箱內可執行的測試及資料檢查已通過。原生程序樹監測驗證、完整 Preflight 與正式 First-Pass 尚待 Mac Terminal 執行。M4.2 實驗尚未驗收。**

本次使用者已授權工程準備與所有必要 Preflight 通過後的一次正式重建，不需再次分階段授權。Codex 實際呼叫 `/bin/ps` 遭 `Operation not permitted`，因此依授權採方案 B；這是沙箱限制，不代表使用者 Mac Terminal 也無權限。沒有降低護欄、反覆請求同一權限、建立正式 Experiment 或執行正式配準。

正式來源為作業 PDF、Phase1_Final_Handoff、M4_Phase2_Capture_Plan、M4.1 原停止／恢復驗收、凍結科學 Manifest 及最終 Provenance。原始 Snapshot 固定 `291209750bd8ecf84f337112c9b92307e6be192a`。不修改教師核心、Ontology、Pixi、原 Capture、既有 Observer、歷史 Manifest 或歷史 `verify_hashes`。

## 單一 Mac Terminal 啟動命令

完整貼上以下一行；不要單獨執行 reconstruct.py，也不要手動建立正式輸出目錄：

```bash
cd /Users/alyssa/Documents/Codex_Workspace/physicalai_hw1 && OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 pixi run --locked -e habitat python scripts/m42_baseline.py run
```

使用目前登入帳號，不需 sudo。Runner 會先確認乾淨 main、工程提交 SHA、Snapshot、凍結 Capture、歷史科學資料、環境版本、磁碟與記憶體、原生監測權限、全部合成測試及完整地圖容量。原生監測測試必須零略過、零失敗；任何必要項目不通過都不建立正式宣告。無需手動拼接腳本或自行判斷何時移除護欄。

每次 Preflight 使用新的 `research_outputs/m42_preflight_<UTC>_<隨機識別>/`，保存逐項 JSON 與測試報告。正式輸出固定 `research_outputs/m42_p2_a01_baseline_01/`；只有 Preflight 全數通過後才獨占建立。該目錄一旦存在即為不可重入的一次性鎖，即使宣告或配準失敗也不自動重跑。正式 Experiment 固定 `experiments/p2_114753116_a01_baseline_01/`。若 Terminal 也無法讀取程序樹，Runner 保留失敗 Preflight 並停止；不得繞過。

正常執行會自動保存正式結果、驗證、英文圖表素材與停止狀態，更新本文件並停止。結果文件更新會使 Git 顯示本文件變更，這是預期產物；Runner 不會自動提交正式執行後的文件。核心來源與歷史科學資料會在更新此文件之前重新嚴格驗證。工程提交與精確來源見 `research_outputs/m42_engineering_01/readiness.json`。

## 固定正式條件

|項目|值|
|---|---|
|Capture|`eval/_data/second_floor/114753116/P2_A_01`；全部原始1..320張|
|Experiment／Floor|`p2_114753116_a01_baseline_01`／2|
|相鄰配準／預期因素|319對／2×320＋6×319＝2554|
|Registration voxel／RANSAC seed|0.05m／0|
|ICP|Open3D Point-to-Plane|
|Map-only voxel|每影格地圖副本0.05m；不改配準點雲|
|執行緒／RSS護欄|OMP_NUM_THREADS=1／程序樹3GiB|

這是預先固定的 Baseline，並非已證實的最佳參數。GT 不參與初值、影格選取或參數調整；只於離線資料描述與正式評估使用。失敗不補 Identity、不換 seed、不略過影格重試、不製造完整因素或 Seal。

## 工具與驗證範圍

- `scripts/m42_monitor.py`：每0.5秒透過 macOS ps 讀取 PID、PPID、PGID、RSS與狀態，遞迴加總存活後代，亦追蹤主程序退出後仍存活的群組成員；每筆保存各PID與總和、峰值、時間。新工作負載以獨立 session 啟動，經初次監測後才放行。超限／讀取失敗以 SIGKILL 終止本次群組；不對其他群組送訊號。獨立 pipe heartbeat watchdog 在監測器意外退出或失聯時終止負載；監測器也偵測 watchdog 意外退出。watchdog timeout=8秒。
- `scripts/m42_observer.py`：只讀取官方 Python call／return 的局部值，不改函式、RNG、參數或官方 callback；自動支援任意 N。逐筆保存影格因素、配準開始、RANSAC回傳與ICP回傳，保留失敗前綴；完整成功後保存位姿、中心、current→previous RANSAC及ICP矩陣、完整回傳地圖點／色。
- `scripts/m42_integrity.py`：僅對新 M4.2 輸出使用雙層制度。科學與來源逐檔嚴格 SHA；只有檔名 `.DS_Store`、非符號連結的一般檔案、版本1／Bud1檔頭及 file 類型均正確，才另列OS中繼資料狀態、類型及前後SHA。未知新增檔案仍屬嚴格比對範圍。Manifest 不列自身。
- `scripts/m42_capacity.py`：逐影格反投影與地圖專用voxel計數，不做配準、不讀GT；估計正式地圖可保存性。
- `scripts/m42_baseline.py`：整合 Preflight、單次宣告／官方CLI、保護式執行、離線驗證與驗收文件；不重用 M3 的191張正式入口。
- `scripts/m42_results.py`：同次 TTL／Seal／Baseline、所有因素逐筆交叉比對、位姿與pair矩陣、完整地圖SHA及shape驗證、官方Explore、Per-frame L2、八因素、top-down／3D／空間分區圖與比較表。只整理候選研究問題。

測試使用暫存合成 RGB-D，包含觀測前後完整回傳地圖、位置、因素、RANSAC／ICP矩陣、Mean L2與NumPy RNG狀態相同；官方CLI→Seal→Baseline→Explore→圖表的整合流程；實際零支援配準失敗證據；非有限原始回傳值採明確 JSON 標記保留，不轉成假數值。

原生測試包括單程序與退出碼、多子程序加總／父先退出、低門檻超限與整組終止、不影響無關程序、執行中讀取被拒、監測主程序意外退出、watchdog意外退出及部分證據保留。**沙箱未執行原生測試；Runner 在 Terminal 必須全部實測通過。** 最新回歸測試為 **61 passed、6 skipped**（18.19秒，原始記錄見 `regression_release.log`）；位姿dtype／shape／座標／SHA中繼資料增補後，Observer 7項測試另行重測通過；其中6項皆為待Terminal的原生監測測試。詳細原始記錄見工程證據；不可把 skipped 視為 passed。

## 已完成的實測與限制

642項 Frozen Scientific SHA 全部相符，Frozen Manifest SHA 固定 `a626655acee213f67d7b759159fe7b5d658f90d89bb8edfd90a3c50c75634d60`。接受版核心／環境來源相符。M4.1原2699項清單中的2681項非OS中繼資料檔案均嚴格相符；18項Finder中繼資料獨立驗證，其中 `research_outputs/.DS_Store` 有歷史差異，原清單及停止紀錄未改寫。新比較紀錄位於 `research_outputs/m42_engineering_01/historical_preservation.json`。

逐影格未裁切地圖總點數上界3,625,386；XYZ＋RGB float64共174,018,528 bytes。以6份地圖空間加1GiB執行環境／配準／配置餘裕規劃，預算2,117,852,992 bytes，低於3GiB；此容量檢查程序實測高水位431,243,264 bytes。合成200萬點完整NPY輸出已驗證不抽樣，輸出額外高水位增加低於24MiB；不以此宣稱記憶體配置器有硬性上限。

完整回傳地圖採分開、不壓縮NPY串流寫出，float64、(P,3)、首相機座標（X右／Y下／Z前）；每影格地圖副本0.05m降採樣後合併，依官方規則去除 min(Y)+1m天花板帶。這不是原始深度像素未降採樣地圖，也不是15萬點樣本。繪圖最多15萬點且另記stride，正式完整來源不取樣。

RSS是0.5秒取樣的保守程序樹加總，共享頁可能重複計算；不能保證瞬間峰值絕不超限。watchdog失聯保護最多約8秒，監測器及watchdog自身在科學負載群組之外。容量與可用記憶體只是執行前估算／快照，正式執行仍須啟用護欄。

## 正式結果與停止狀態

|層次|目前狀態|
|---|---|
|工程原始碼、測試、整合Runner|已建立並提交；沙箱可執行項目已測|
|完整必要Preflight|尚未通過；原生權限／程序樹實測待Terminal|
|一次正式First-Pass|未執行；正式Experiment與輸出目錄尚不存在|
|正式成功或失敗|尚無實驗結果|
|M4.2實驗驗收|待處理；不能把工程交付視為正式實驗成功|

尚無正式Mean L2、2554筆因素、正式Seal或完整二樓重建圖。合成圖只用於工程驗證，不冒充正式重建結果。正式成功後的區域圖以地圖象限呈現；缺少逐段route_notes，不能編造房間名稱或絕對全樓層完整率。房間涵蓋與缺失仍需根據正式圖像及人工路線記錄解讀。

至此交付方案B。未開始P2-B、P2-C、新seed／voxel實驗、Experiment D、Bonus、最終英文報告或Submission ZIP。

## Terminal 第一次執行後的工程修正（2026-11-19）

第一次 Terminal Preflight：`research_outputs/m42_preflight_20261119T072234Z_3bc540ab/`。原生 ps 權限已通過；必要自我測試為 **24 passed、3 failed、0 skipped**，其餘必要檢查通過。因此未建立正式宣告／Experiment／一次性輸出目錄，**正式 First-Pass 尚未執行，單次額度未使用**。原失敗 Preflight 與原工程證據完整保留，不改成通過。

三項失敗均發生在終止後的重複清理：首次 SIGKILL 成功，監測器已寫出原始停止原因；finally 再次對只剩未回收殭屍程序的群組送 SIGKILL 時，Darwin 回傳 EPERM。沙箱最小案例及先紅後綠的回歸測試已重現此行為，不能把該 EPERM 直接解讀成第一次無法終止程序。

修正僅影響輔助監測器：收到 EPERM 後，必須成功讀取程序表並證明群組成員全部是殭屍程序，才記為 `no_live_members_verified`；若程序表沒有該群組，還必須以 signal 0 取得 ESRCH，證明群組已不存在。**仍有存活成員、必要資訊缺失、程序表不可讀或真正權限拒絕皆不放行。** 每次終止嘗試新增 `termination.jsonl`，保存原始錯誤、驗證成員與處理結果；停止原因先寫入磁碟，再嘗試清理。watchdog 終止失敗也保留明確失敗收據。

修正證據獨立放在 `research_outputs/m42_monitor_cleanup_fix_01/`，包含原 Preflight／原工程清單SHA、舊版原始碼副本、red／green回歸與新來源版本。pytest暫存原生測試目錄已被後續pytest保留政策清除；已讀取的診斷值以明列來源的擷取紀錄保存，不冒稱完整原始檔副本。原持久化測試輸出、XML及Preflight均未修改。

新版固定來源改由該新目錄的 `readiness.json` 綁定；原 `m42_engineering_01/readiness.json` 不覆寫。上方單一 Mac Terminal 命令維持不變；再次執行時先在新 Preflight 目錄重做全部必要實測，必須零失敗、零略過，才會使用尚未動用的一次正式重建授權。**新版原生監測完整測試仍待 Terminal 驗證，不宣稱已通過。**

新版沙箱回歸：**65 passed、6 skipped in 18.66s**，見新修正證據目錄 `regression_verified.log`／XML。最小缺陷測試先得到1 failed、2 passed，再修正至通過；新增案例另確認存活子程序、無法讀取程序表及必要PID缺失都不會被EPERM例外放行。預防措施是保留這組Darwin重複終止回歸，並繼續要求完整原生測試作正式執行門檻。
