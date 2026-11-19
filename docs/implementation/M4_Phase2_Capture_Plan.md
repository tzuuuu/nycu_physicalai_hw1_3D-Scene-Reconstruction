# M4.0 — Phase 2 二樓擷取環境檢查與實驗規劃

日期：2026-11-19（臺灣）；student_id：**114753116**。

**本文件為規劃與唯讀前置檢查交付。未啟動二樓正式／暫存 Capture、Declare、重建、Bonus 或英文報告。M4.0 完成後停止，等待人工驗收；M4.1 由使用者在 Mac 親自操作，M4.2 另行授權。**

## 1. 依據與老師要求對照

直接閱讀老師原始 `docs/assignments/HW1_3D Scene Reconstruction.pdf` 全 13 頁，並渲染檢視 p.9 §3.4；文字擷取／渲染使用 macOS PDFKit，暫存位於 `/private/tmp/m4_assignment.txt`、`/private/tmp/m4_pdf_p9.png`。以原始 PDF 為最高依據，舊摘要不取代正式要求。

另閱讀 Phase1_Final_Handoff、Phase1_Submission_Readiness_Audit（包含目前及歷史限制）、M1、M2、M3 驗收／實驗保全規範、原始交接規劃，以及 `load.py`、`configs/second_floor.yaml`、`packages/simulator/simulator/{config,engine,effects,replay,viewer,__init__}.py` 與相關測試。M0 制度依原始交接規劃；沒有獨立 M0 驗收文件可冒稱已讀。

|正式要求|本次／後續落實|
|---|---|
|§3.4 p.9：二樓 apartment_0，由學生自行導航採集 RGB-D／相機姿態|M4.1 使用官方 load.py、既有二樓 config，獨立學號版本目錄；不以既有 GT replay 代替|
|§3.4：w/s、a/d、c/Space、q/Escape；記錄擷取路徑、路線、張數|第 3、6、8 節列出操作及人工路線紀錄；不憑空假定有俯仰鍵|
|§3.4、§3.2 pp.6–8：採集後 Declare → 完整 First-Pass → 檢視因素 → 證據導向介入|M4.1 結構檢查不等於正式 First-Pass Data Verification；P2-B 只列候選，規則及 SPARQL 等 M4.2 後決定|
|§4 p.10：手寫反投影、Normals／FPFH、RANSAC、**Open3D Point-to-Plane ICP**|沿用已驗收核心；不能用一般段落允許 Point-to-Point 的敘述降低評分段落要求|
|§4：合法 Turtle、完整八因素、Seal、Baseline／Selected run|M4.2 建立新 workspace，驗證 2N＋6(N−1)=8N−6 筆因素；Selected 是後續工作，不在本次偽造|
|§4 p.11：主要房間、連通區域、角落的 Scene Coverage|人工區域清單與代表影格；點數／張數不當作涵蓋率；無表面 GT 不宣稱絕對百分比|
|§2.1.4 p.4、§4：首相機參考系、Mean L2、紅 Estimated／黑 GT、必要時去天花板|GT 僅作離線資料描述及重建後評估；不用於配準、選較準影格、參數最佳化或軌跡擬合|
|§4 pp.11–12：張數、時間、超參數與兩階段比較|記錄每組實際條件與限制，不以不同路線的 Mean L2 直接排名演算法|
|§5 p.12：英文 report.pdf、全部必要來源；不包 Capture／Replica／生成 TTL／diagnostics|本次只準備來源可追溯性，最終英文報告、README／ZIP 的舊待辦仍保留，未執行|

PDF 二樓示意為 213 張，**不是張數下限或本次目標**。120～200 張是本專案暫定範圍，以品質與涵蓋為優先。

## 2. 本機環境實證與尚未驗證範圍

|項目|2026-11-19 檢查結果|
|---|---|
|平台|macOS 26.7.1，arm64；M4 機型依既有人工驗證／交接；本次 CPU 型號 sysctl 被沙箱拒絕，未將其列為新實測|
|鎖定環境|`pixi run --locked -e habitat python load.py --help` 退出 0；未觸碰 prepare_capture_dirs|
|相依匯入|既有 `.pixi/envs/habitat/bin/python` 匯入成功：Python 3.9.23、Habitat-Sim 0.3.3、Pygame 2.6.1／SDL 2.32.56、NumPy 1.26.4、OpenCV 4.8.0、YAML|
|場景|`replica_v1/apartment_0/habitat/mesh_semantic.ply`（209899678 bytes）與對應 navmesh（32744 bytes）存在；未載入 Renderer|
|磁碟|當下 df 約剩 23 GiB；啟動前重測。200 組未壓縮 RGB＋uint16 Depth 約 250 MiB，實際 PNG、紀錄及後續重建額外占用須另外預留|
|互動環境|舊交接記載曾人工成功；**本次沒有開視窗、建立 Engine 或存任何模擬影格，故目前互動擷取尚未重新驗證**|
|二樓舊測試資料|目前 `eval/_data/second_floor/` 不存在，Phase 1 最後 protected 清單也未列 env_test。使用者本次確認「我已經把上次測試的二樓資料刪除了」；記錄為使用者先前刪除，不尋回、不重建、不冒稱本次保全了不存在的檔案|
|已知警告|Pixi 無法讀部分使用者快取時採內建 detector，help 仍成功；不重裝／更新 lock。PDFKit 初次 Swift module cache 受限，改用 `/private/tmp` cache 後成功，無核心更動|

結論：靜態設定、資產存在、相依匯入與安全 help 通過，具備啟動前提；**不能據此宣稱 Cocoa/OpenGL／鍵盤／PNG 實際寫入全已通過**。Python 匯入測試未呼叫 `pygame.init()`。正式流程的 engine → viewer 匯入順序須維持，不手動先開 Pygame 再建立 Habitat。

### 如需額外互動測試，先另行核准

本次不執行。候選測試：核准後以 `tempfile.mkdtemp(prefix='physicalai-m4-ui-', dir='/private/tmp')` 建立獨立根目錄，衍生 config 只改 `output.clear_existing=false` 與 root，保留正式相機／效果；人工測 w、s、a、d 各一次、停穩後 c／Space 共兩張、q 正常結束，再唯讀檢查兩組 PNG／GT／內參。不得使用正式路徑或 env_test，測完保留測試證據，不自動清理。

實際允許寫入範圍應限定新暫存樹內的 config、命令／版本／console、`capture/{rgb,depth}/*.png`、`GT_pose.npy`、`intrinsics.json`、驗證／SHA；作業系統與依賴可能嘗試讀寫快取，若超出沙箱須另行列明。需要可見桌面 Cocoa/OpenGL、鍵盤焦點及該新目錄寫入權限；不需要螢幕錄製、輔助使用、相機／麥克風或網路權限。由 Codex 代為啟動仍須使用者先核准測試方案；本次未提出強制核准門檻，使用者可選擇驗收計畫後直接親自做 M4.1。

## 3. 實際控制與保存時機

來源：`load.py:run_interactive`、`engine.py:make_cfg`。

|按鍵／事件|實際行為|
|---|---|
|w／s|每次 KEYDOWN 前進／後退 **0.2 m 命令步幅**；碰撞／navmesh 可能使實際位移較少或為零|
|a／d|每次 KEYDOWN 左／右轉 **6°**；15 次為 90°、30 次為 180°；須分段觀察／採集|
|c／Space|同一保存功能；count 先加 1，立即寫 rgb/N.png、depth/N.png，將目前 color sensor 世界姿態加入記憶體清單；不是連續錄影|
|q／Esc|結束迴圈，將清單寫為 float32 `GT_pose.npy`，印出張數；其後 report_zone_coverage、釋放 Pygame／Engine|
|視窗關閉事件|走正常迴圈結束，通常也會寫 GT；正式作業優先使用 q／Esc 並確認 Terminal 保存訊息|
|其他按鍵|忽略；**無 look_up/down、滑鼠俯仰、側移、升降或互動改 FOV**|

相機 `orientation=[0,0,0]` 固定水平；鳥瞰視圖朝下只供預覽，不能作為操作相機俯仰實驗。預設 agent 起點 `[0,1,-1]`，初始面向 −Z；相機在 agent 上方 1.5m，初始名義 sensor 位置 `[0,2.5,-1]`。可達性／移動後高度以 M4.1 實際畫面及資料確認，不將設定高度當作已驗證的樓層幾何。

**逐次「移動／轉向 → 放開 → 等畫面更新 → 再按 c → 核對 Terminal captured frame」**。事件批次內可能先處理移動再處理 c，但 `frame,sensor_state` 在整批事件之後才更新；混按可能存到前一畫面。建議等畫面穩定至少約 0.2 秒再拍，避免長按連發；此等待只為更新，不選擇閃爍最亮／最暗時刻。`fps=30` 是預覽更新上限，不是自動每秒拍 30 張，移動步幅不隨 fps 改變。

GT 只在正常互動函式結尾保存；Ctrl-C、強制結束、原生崩潰／磁碟錯誤可能留下 PNG 但缺 GT。沒有自動 checkpoint／續拍功能；每次從 1 開始，失敗批次封存並換新版本，不能再次以相同輸出啟動。`save_frame` 沒有檢查 `cv2.imwrite` 布林回傳值，Terminal 張數不是磁碟成功保證，採集後必須獨立稽核。

## 4. 原始資料契約與所有關鍵設定

`--output-root` **直接取代** config 的 `output.root`，不自動附加學號／批次名稱；相對路徑以目前工作目錄解析。`prepare_capture_dirs` 只使用該 root，巢狀 `<學號>/<條件版本>` 與後續 `--data-dir` 相容。

```text
eval/_data/second_floor/114753116/P2_A_01/
  rgb/1.png ... N.png
  depth/1.png ... N.png
  GT_pose.npy
  intrinsics.json
```

|輸出|實際格式與解讀|
|---|---|
|RGB|512×512、3 通道 uint8 PNG；程式內 RGB 轉 BGR 交給 cv2 寫檔，讀取 cv2 時為 BGR，不能再錯置色彩|
|Depth|512×512、單通道 uint16 PNG，`clip(depth_m*1000,0,65535).astype(uint16)`；儲存值為毫米，除 1000 轉公尺；0 無有效回傳。不是畫面上 8-bit Depth 預覽；毫米截斷不代表原始量測精度為 1 mm|
|GT_pose.npy|正常 N>0 為 float32 (N,7)，第 i−1 列對應 i.png；世界 color sensor `[x,y,z,qw,qx,qy,qz]`，位置公尺、四元數 w 在前。不是 agent 中心、不是 4×4 矩陣。零張時現有程式會存 shape=(0,)，應拒絕|
|intrinsics.json|**恰三欄** `width:512,height:512,hfov:90.0`，HFOV 單位度。沒有 fx/fy、depth_scale、外參、區域或噪聲設定。不得自行改原檔補欄位；深度尺度來源另存 provenance|
|內參派生|既有反投影契約 fx=fy=W/[2 tan(hfov/2)]=256，cx=256、cy=256；方形影像 VFOV=90°。後續仍讀本批 JSON，不借用一樓內參|
|其他|save_semantic=false，無 semantic PNG／birdseye PNG、每影格時間戳、動作軌跡、route.json 或 windows.json；路線與操作資訊須人工另記|

`configs/second_floor.yaml` 關鍵值（不得改原檔）：

|區塊|值與影響|
|---|---|
|scene／agent|apartment_0/habitat/mesh_semantic.ply；start [0,1,−1]；前後 0.2m、左右 6°|
|camera|512×512、HFOV 90°、position [0,1.5,0]、orientation [0,0,0]；color/depth 同相機配置|
|birdseye|512×512、HFOV 90°、position [0,2.5,0]、orientation [−1.5708,0,0]；跟隨 agent 的局部鳥瞰，不是整層地圖|
|marker|enabled=false；size [0.4,0.05,0.4]、height_offset=.03、forward_offset=1.0 目前不生效；不啟用 marker／physics|
|lighting|brightness=contrast=gamma=1.0、ambient_rgb=[1,1,1]；config loader 補 amplitude=frequency=phase=0|
|depth 基本|enabled=true、stuck=false；noise_std=.005m、dropout_prob=0、min_range=0、max_range=10m、quantization=0；redwood=false、redwood_multiplier=1（目前不生效）|
|光照與深度耦合|light_nominal=1、noise_gain=4、dropout_gain=.3、range_gain=.4；stress=abs(exposure−1)，噪聲乘 (1+4stress)、丟失率加 .3stress（上限1）、最大距離乘 max(0,1−.4stress)|
|uncertainties|enabled=true、mode=spatial、seed=20；XZ 圓形區域第一個符合者生效，radius 都 1.5m|
|三區域|benign center [3.77,3.10]、amplitude .30／frequency .73Hz；moderate [2.22,6.22]、.60／1.17Hz；severe [3.05,8.01]、.95／1.91Hz|
|display|scale=1、RGB／Depth／birdseye 全顯示；預期三個 512 面板約 1536×512 加視窗外框|
|output|root=`eval/_data/second_floor/`、save_rgb=true、save_depth=true、save_semantic=false、**clear_existing=true**|

互動效果用 session wall-clock；seed 20 只控制 `default_rng([seed,round(t*1000)])` 的每影格 Depth 雜訊，不是 RANSAC seed，也不能使人工採集完全可重現。區域以 agent XZ 判斷；不依區域 GT 邊界刻意挑選較乾淨影格。結束時保留各 zone 張數輸出，可為零；二樓 §3.4 沒有規定必須進入每一區，不能因未進入某區宣稱有該區效果證據。後續 Data Verification 必須依真實八因素，不用設定區域代填因子或品質標籤。

P2-A／C 建議保留教師效果與 seed，不加 `--clean`。`--clean` 只關 spatial scheduler，**不會關 .005m 基本噪聲**；不得稱為完全無噪聲。若未來要比較 clean，須新宣告、新批次及另行核准，不混入這三條件。

## 5. 防覆寫與保全制度

`prepare_capture_dirs` 在 `clear_existing=true` 且 root 是資料夾時，**shutil.rmtree(root) 刪除該 root 整棵樹**，不是只清 RGB／Depth；然後建立子資料夾並重寫內參。`main` 先做這件事再建立 Engine，所以即使視窗／場景載入失敗，既有資料也可能先被刪。若不用 override，整個 `eval/_data/second_floor/`（含所有學號、測試與正式批次）都在風險內。

正確巢狀 override 不會主動刪父目錄，但錯傳父目錄、符號連結或重用路徑仍危險。**不可直接使用未受保護的預設啟動命令，也不可重新執行同名批次。** 本計畫採雙層保護：

1. 獨立 `scripts/m4_capture_check.py preflight` 唯讀拒絕既有目標（含斷裂符號連結）、錯學號、父目錄、P2-B、任何符號連結祖先；只接受本專案學號下 `P2_A_XX`／`P2_C_XX`。
2. 使用者正式啟動命令先驗證「從未存在」，再以 `mkdir(exist_ok=False)` 獨占保留空批次目錄；衍生 config **只改 output.root 及 clear_existing=false**，寫入新 research_outputs provenance，不改老師原 YAML。這是安全性衍生設定，不改科學條件。啟動時目標雖已由保護程序建立，但原資料路徑是新保留、從未含 Capture；不存在教師 rmtree 刪掉保護標記的問題。

即使 clear_existing=false，官方程式仍可覆寫同名 PNG／GT／內參，因此「拒絕既有路徑」與單次執行不可省略。不要兩個 Terminal 同時擷取同一學號／版本，也不要在啟動期間移動／替換目錄；防護適用正常單一使用者流程，不宣稱可對抗惡意競爭寫入。

```text
原始 Capture： eval/_data/second_floor/114753116/P2_A_01
獨立擷取紀錄： research_outputs/m4_capture_P2_A_01
獨立資料驗證： research_outputs/m41_verify_P2_A_01
未來實驗：     experiments/p2_114753116_a01_baseline_01
未來觀測輸出： research_outputs/p2_114753116_a01_baseline_01
P2-C 對應：    P2_C_01（其餘名字同樣獨立替換）
```

以上正式目錄本次均未建立。重拍用 P2_A_02／P2_C_02 等；**失敗批次、已保留的空目錄與紀錄也不刪不重用**。未來若重新出現 env_test，必須保持原樣，不能用它作正式輸出。Phase 1 Capture／experiments／research_outputs 全部保持；不呼叫歷史停止／finalize 入口，不擴大 `.DS_Store` 例外。新資料夾若出現非標準檔案，工具報錯並人工處理，不自行清理或全域忽略。

每次保存 Git HEAD、固定 Snapshot、原 config／衍生 config、load／simulator／lock SHA、完整 argv、開始／結束時間、退出碼、套件版本及人工 route notes。採集後 SHA 逐檔覆蓋 RGB、Depth、GT、內參，對所有舊受保護檔案再比前後 SHA。宣告 Seal 不能取代原始資料與研究輸出 SHA。只將必要原始碼、測試及 MD 加入 Git；原始 Capture、provenance、JSON、圖及大型資產不加入。

## 6. P2-A／P2-B／P2-C 條件與路線

### P2-A — Dense Route

目的：第一次完整二樓資料與固定 Baseline，約 120～200 張；不為張數原地連拍。起點使用 config 預設 agent 位置，**第一張在移動前拍攝**並保留為所有後續子集首參考。

目前未實地導航，沒有足夠證據為房間命名或編造精確 waypoint。採可操作的相對拓樸路線，M4.1 邊走邊把可見主要區域記成 R0、R1…，連通處記 C1…，分支／角落記 K1…，不得將局部鳥瞰誤稱全層平面圖：

1. R0 起點：拍 1，觀察主視角與鳥瞰，記錄起點地標及可走出口。先沿可達邊界採**右手優先**的房間／分支巡訪。
2. R0 → 第一連通區 C1：每 1～2 次 w（命令距離 .2～.4m）拍一張；接近門口、家具、狹窄處改每 1 次。碰壁沒有移動就不因按了 w 而拍重複影格。
3. 進每個新房間 Rj：門外、門檻、門內保持橋接視角；沿可行房間周邊觀察遠端角落，讓畫面保留跨影格可辨識的牆角／門框／家具。不要只對單一白牆或貼牆拍。
4. 每次轉彎以 1～2 次 a/d（6～12°）後拍；90° 約 8～15 張橋接視角，不一次轉完再拍。需要掉頭 180° 時仍分段拍，不瞬間從前向跳到後向。360° 全景只在補缺視野必要時做一次，不在每個位置重複。
5. 走完分支後沿連續視角回到已記錄連通地標，再選下一未訪區域。單一路徑外返也記入路線；不瞬移、不爬不可達家具／樓梯、不預設可通行的門一定可過。
6. 完成所有可達主要區域與角落後回到起點附近的辨識地標（能安全回返時），拍末影格，按 q 保存。閉合巡訪是涵蓋與描述用途，現有 sequential pipeline 不會自動做 loop closure。

規則是足夠重疊的操作起點，**不保證某一百分比幾何重疊**。狹窄、遮蔽、快速轉向段應補連續橋接；保留正常空間變化與效果，不因 Depth 預覽變差就等效果消失。若 200 張仍缺主要區域，先記錄缺口及實際張數，由人工決定是否繼續補齊；若提前完成可少於120，不湊數。

### P2-B — Sparse Selection（本次不擷取、不選取）

來源必須是 P2-A 凍結原始影格，以原始索引與順序引用，**始終保留 frame 1**，不複製重編號成假新 Capture、不讀 GT 選較準影格。候選僅供之後評估，不先指定門檻或產生 `.rq`：

- 固定索引步進／目標保留比例：可考慮隔 1～2 張或約 1/2、2/3，但轉角／門口可能失去橋接。
- 依人工房間／連通／轉角註記分層減密：各主要區域保留代表與橋接，維持時間順序；不能只保留容易配準的房間。
- First-Pass 後依真實八因素的分布與失敗區段，制定可說明的減密／支撐規則；不因 GT 誤差小才保留。

**決策門：P2-A 完整 First-Pass Data Verification＋Baseline 驗收後**，才記錄假說、保留比例、正式 selection 規則、SPARQL（experiment-scoped、DISTINCT、ORDER BY frameIndex）、精確索引與 SHA；不得套用 PDF 範例閾值或 Phase 1 排除104的規則。查詢結果先人工檢視再執行 Selected；記錄跳號造成的新鄰接配準、spliceCount／gap metadata。舊相鄰對因素不能冒充稀疏新鄰接對的實測值。

公平比較：A FullBatch Baseline 完整 Mean L2 仍獨立報告；B 與 A 的**主要誤差比較使用相同保留影格集合 S**，從保存的 A Baseline 位姿取 S、B 使用同一 S（含1）評估，固定首相機參考且不做最佳擬合，另報 FullBatch N、|S|／N、房間／通道涵蓋與時間。這不代表 A 只消耗了 S，須揭露 A 使用全批歷史、B 使用稀疏鄰接；若 B 又改參數，還需在同一 S 上固定參數的控制，不把密度與參數效果混在一起。GT 只在凍結規則後計算結果，不能回頭調 selection。

### P2-C — Different Route

在 A Baseline 驗收後才考慮採集。獨立 P2_C_01、保留同一相機／效果／動作設定與起點首張，目標主要區域與 A 相同；採**左手優先／反向分支順序**，例如 A 是 R0→R1→R2→R3，C 改 R0→R3→R2→R1（必須可實際連通，不以該示意當真實地圖）。可從相反側接近同一門口／角落；維持安全小步橋接，不以缺乏重疊刻意製造失敗。若場景限制不能反向，就保留共同連通路徑並明列改變的分支順序與視角。

記錄 A/C：實際影格數、人工 w/s 次數與名義行走長度（.2×次數，含碰撞高估）、採集 GT 相鄰位置弦長合計（漏掉未拍路段／繞行，可能低估，**非真實全程里程**）、房間／通道／角落清單、相同地標方向、轉向段比例與相鄰 GT 分布。相機角度跨度／RGB 差異只是重疊風險代理，不等於量測到幾何重疊率。

不同路線 Mean L2 的參考首姿態、路程、長度、可見幾何及效果曝露可能不同，即使使用同一演算法也不能直接排名演算法優劣。C 先建立自己的完整 Baseline；正式介入仍須自己的 First-Pass 證據，不借用 A 因素當 C 的量測。

## 7. 給使用者的正式 Mac Terminal 指令（本次未執行）

**僅於 M4.0 人工驗收後，由使用者操作 M4.1。** 下列第一段安全唯讀；第二段會啟動正式 P2-A，請分開貼上。不要只摘出官方 load.py 那一行執行，不要加 `--trajectory`／`--clean`，不要先建立 Capture 目錄。

```bash
cd /Users/alyssa/Documents/Codex_Workspace/physicalai_hw1
pixi run --locked -e habitat python load.py --help
pixi run --locked -e habitat python scripts/m4_capture_check.py preflight \
  --target "$PWD/eval/_data/second_floor/114753116/P2_A_01"
df -h .
```

下段是有防護的官方 load.py 啟動流程，完整貼入同一 Terminal。`condition` 是唯一需於新批次修改的名稱；C 必須等 A Baseline 驗收後才可改成 `P2_C_01`。此區塊建立來源／舊成果 SHA、衍生安全 config 與單次紀錄後，仍透過原始 load.py 擷取，未改核心。

```bash
OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 pixi run --locked -e habitat python - <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import importlib.metadata as md
import json, os, platform, subprocess, sys, yaml
from scripts.m4_capture_check import ROOT, check_target, inventory, no_links, sha
condition = 'P2_A_01'
os.chdir(ROOT)
if subprocess.check_output(['git','branch','--show-current'], text=True).strip() != 'main':
    raise RuntimeError('必須位於 main')
if subprocess.check_output(['git','status','--porcelain'], text=True).strip():
    raise RuntimeError('請先確認並提交待處理變更；不要自動 stash 或清理')
if subprocess.check_output(['git','rev-parse','snapshot/pre-implementation'], text=True).strip() != '291209750bd8ecf84f337112c9b92307e6be192a':
    raise RuntimeError('Snapshot 不符')
target = ROOT / 'eval/_data/second_floor/114753116' / condition
check_target(target)
record = no_links(ROOT / 'research_outputs' / ('m4_capture_' + condition))
if record.exists():
    raise FileExistsError(record)
protected = {}
for base in ['eval/_data', 'experiments', 'research_outputs']:
    protected.update({base+'/'+k:v for k,v in inventory(ROOT/base).items()})
source_names = ['load.py','utils.py','reconstruct.py','api.py','ontology/hw1.ttl',
                'configs/second_floor.yaml','pixi.toml','pixi.lock','scripts/m4_capture_check.py']
source_names += [str(p.relative_to(ROOT)) for p in (ROOT/'packages/simulator').rglob('*.py')]
sources = {n:sha(ROOT/n) for n in sorted(source_names) if '__pycache__' not in n}
record.mkdir(parents=True, exist_ok=False)
def dump(name, value):
    with (record/name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
dump('protected.before.json', protected)
config = yaml.safe_load((ROOT/'configs/second_floor.yaml').read_text())
config['output'].update(root=str(target), clear_existing=False)
safe_config = record/'capture.safe.yaml'
with safe_config.open('x') as f:
    yaml.safe_dump(config, f, sort_keys=False)
# 先拒絕既有目錄，再獨占保留空目錄；clear_existing=false 防止官方入口 rmtree。
check_target(target)
target.mkdir(parents=True, exist_ok=False)
argv = [sys.executable, str(ROOT/'load.py'), '--config', str(safe_config),
        '--output-root', str(target), '--fps', '30']
dump('start.json', {'argv':argv, 'cwd':str(ROOT), 'condition':condition,
    'started_at_utc':datetime.now(timezone.utc).isoformat(),
    'git_commit':subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
    'snapshot':'291209750bd8ecf84f337112c9b92307e6be192a', 'source_sha256':sources,
    'safe_config_sha256':sha(safe_config), 'effective_file_config':config,
    'depth_scale_source':'replay.save_frame uint16 millimetres; divide 1000',
    'platform':platform.platform(), 'python':sys.version,
    'versions':{n:md.version(n) for n in ['numpy','pygame','opencv-python','PyYAML','open3d','rdflib']}})
print('正式擷取：', target, flush=True)
result = subprocess.run(argv)  # 鍵盤焦點放在新開的 Habitat 視窗
changed = [n for n,h in protected.items() if not (ROOT/n).is_file() or sha(ROOT/n)!=h]
source_changed = [n for n,h in sources.items() if not (ROOT/n).is_file() or sha(ROOT/n)!=h]
dump('finish.json', {'ended_at_utc':datetime.now(timezone.utc).isoformat(),
    'returncode':result.returncode, 'protected_changes':changed, 'source_changes':source_changed,
    'capture_sha256':inventory(target), 'verification':'pending'})
if result.returncode or changed or source_changed:
    raise RuntimeError('擷取或保全未通過；保存目前批次並停止，不要重用目錄')
PY
```

啟動後拍攝由人工操作，不會自動存影格。不要在主 Terminal 按 Ctrl-C；正常 q 後回到 Terminal，先保留完整輸出（可從 Terminal 選取另存到該新 record 的 `console.txt`，不覆寫任何檔案）。若原生崩潰或中斷導致 finish.json 不存在，start.json 和部分影格仍是失敗證據，不能當作正式成功批次。

若 provenance／空 Capture 已建立卻環境未成功啟動，改新版本；不得用刪掉目錄的方法繞過保護。若來源或舊成果 SHA 改變，停止並記錄精確差異，不能更新舊預期 SHA 使其通過。上述程式只比較已存在的受保護檔案，另須查明是否有非預期新增檔案；新 provenance 與新 Capture 是預期新增範圍。

### 需要的權限與資源

使用者 Terminal 需要專案內新 `eval/_data/second_floor/114753116/<新版本>` 及新 research_outputs 子目錄寫入權限，並能使用目前登入桌面的 Cocoa/OpenGL。Pixi 使用既有鎖定環境，不需要下載／升級；若要求重新安裝或網路存取先停止診斷。平常不需 sudo 或整碟存取，也不因本文件授權 Codex 代按擷取。

正式擷取前重測磁碟／系統負載並關閉非必要高負載程式；本次約23 GiB 只是快照。採集目標沒有整批累積點雲，但仍可能有渲染記憶體風險；若卡頓、黑畫面、寫入失敗，q 正常退出，保留資料，待驗證，不降低解析度／停用效果來偷換條件。後續重建沿用既有總 RSS 3 GiB 護欄與可觀測性要求，啟動前另做必要權限／資源 preflight。

## 8. 人工擷取操作清單

1. 驗收本計畫，確認只做 P2-A；執行第7節唯讀段，核對目標完整絕對路徑。若存在立即換下一版本，禁止清空父目錄。
2. 執行受保護啟動段；核對 Terminal capture dir、uncertainty zones 與三面板正常。畫面空白／不可操作時不盲拍；可 q 保留失敗批次。
3. 點選 Habitat 視窗、切到英文輸入，未移動前按 c 取得第1張；Terminal 應顯示 captured frame 1。固定首影格不可事後換掉。
4. 按第6節右手優先路線，以分開的動作／拍攝鍵採集；避免長按、連按 c／Space，轉彎與門口保留橋接；每區記代表索引及視角。
5. 人工在新 `research_outputs/m4_capture_P2_A_01/route_notes.md` 記錄時間、起點地標、區域巡訪順序、各區首末／代表影格、轉向／出入門索引、w/s 步數（可計數時）、碰撞／重複拍攝、缺漏與不能到達原因；不要寫入原始 Capture。分區數量及名稱以實際畫面填寫，不用本文件示例代填。
6. 完成主要區域／連通／角落清單後，按 q／Esc，等 Terminal 印出 saved N poses 與 zone coverage，等程序正常結束；記錄最終 N 與預估涵蓋，不宣稱已重建成功。
7. 正常退出後不重新啟動同一路徑；保存 console，立即執行下一節驗證。發現缺 GT／缺圖／錯型別／不合理位姿，整批保留並停止，由人工決定是否新版本重採。

## 9. Capture 完成後的驗證（M4.1，不是本次執行）

獨立工具不匯入 simulator／Open3D／重建 API，不挑影格、不讀寫 Turtle。只讀 Capture；報告以獨占新目錄保存：

```bash
cd /Users/alyssa/Documents/Codex_Workspace/physicalai_hw1
OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 pixi run --locked -e habitat \
  python scripts/m4_capture_check.py verify \
  --capture "$PWD/eval/_data/second_floor/114753116/P2_A_01" \
  --report-dir "$PWD/research_outputs/m41_verify_P2_A_01"
```

報告已有就拒絕，重複稽核用新的 `m41_verify_P2_A_01_review02` 等，不覆寫。檢查失敗輸出例外，保留 Terminal 訊息於新失敗紀錄；不刪圖／補 GT／改索引。工具 `structural_integrity=passed` 只表示檔案結構，**human_coverage_review=pending、first_pass_data_verification=not_run** 仍須後續驗收。

|檢查|工具／人工驗收方式|
|---|---|
|RGB／Depth 配對|兩邊精確 1..N、N>0、無跳號／重複／非標準檔；逐張可解碼、RGB uint8 H×W×3、Depth uint16 H×W|
|GT|float32 (N,7)、所有值有限、四元數長度約1、首影格對應；GT 缺失／空拍 shape=(0,) 一律不通過|
|內參／深度|三欄合法、90°／512×512 是否符合本 config；尺度來源明列／1000，零深度比、正深度 mm 分布、>10m 像素告警；不改 JSON 加尺度|
|逐張 Depth 品質|保存每張無效像素比例、正值 min／median／p95／max；全零告警，交人工停止審查，不自動刪除或當成因素|
|相鄰 GT 描述|逐對位移與完整四元數旋轉角、分布、近靜止段與弦長；僅離線擷取描述，沒有輸出配準初值／Selection／最佳參數|
|重複與重疊|相同解碼 RGB hash 群組僅告警；噪聲讓 Depth 不同不代表新視角，靜止／大轉角段人工對照。角度／位移不是幾何重疊率，必要時逐張翻閱橋接|
|Scene Coverage|人工依 route_notes 建 R/C/K 區域×代表影格清單，逐張確認門內外、轉角、遠端區域及缺漏；可用新研究目錄聯絡表。無完整全層表面GT，僅報已確認區域與缺口|
|SHA 保全|報告內 `sha256` 覆蓋全部原始檔，工具前後重算確保稽核時未改變；與 finish.json 的 capture_sha256 逐項比對。後續啟動前再驗 SHA|
|來源／舊成果|核對 start/finish、原與安全 config 差異僅 output 兩欄、版本／argv／SHA；所有 protected.before 舊資料不變，沒有碰 Phase 1 workspace|
|分離|Capture 根目錄不應有 workspace TTL／plots／重建輸出；未來 Declare 指向此批但寫新 experiments，監測與資料稽核寫獨立 research_outputs|

人工不因 GT 誤差／路線描述挑掉較差影格；M4.1 若只發現一般品質風險，記錄並交完整 First-Pass 量測，不先建立因素 Pass/Fail。若完整性不通過則不啟動正式重建。無品質嚴重程度的預設自動門檻可冒充驗收。

## 10. M4.1／M4.2 後續驗收與可重現 Baseline

### M4.1 擷取驗收

- 使用者親自採集、全新版本、正常 q 保存 N>0；完整來源、路線、時間、影格數與異常紀錄。
- RGB／Depth／GT／內參格式及索引完整；SHA 與 finish 一致、舊成果不變；Coverage 人工檢視列出主要區域及缺漏，不能只憑張數通過。
- 原始首影格固定、原始 Capture 凍結，沒有 GT 選擇；稽核輸出獨立。
- 此階段可以驗收資料可供 First-Pass 使用，不能宣稱八因素、Seal、Baseline 或 Phase 2 演算法品質已驗收。通過後等待 M4.2 授權。

### M4.2 完整 First-Pass Baseline（只規劃，無本次執行指令）

1. 啟動前再驗本批 SHA、核心／lock／HEAD／Snapshot，資源與監測權限通過；新 experiment／研究輸出拒絕覆寫，備份保全舊來源及研究檔案。保留第一次失敗、停止／Traceback，不自動恢復重入。
2. 透過官方 `api.py declare` 建立 `p2_114753116_a01_baseline_01`，`--floor 2`、`--data-dir` 精確指向 P2_A_01。宣告假說／預測、完整設定／來源連結；不預先選因素門檻。衍生 config 包含環境設定，不作為重建器的 GT／區域輸入。
3. **建議 Baseline 明設** backend=open3d、registration voxel=.05m、seed=0、map-only down_voxel=.05m、OMP_NUM_THREADS=1；.05/0 來自現有 CLI 預設，map .05 是為資源可控的明示地圖設定（CLI 原始預設 None），不是 Phase 2 最佳值。正式執行前登記並驗收，不繼承 Phase 1 Seed1／Voxel .08 的優勢宣稱。
4. 派生設定固定：Normals 半徑 .10m／30 鄰點、FPFH .25m／100、RANSAC 距離 .075m、mutual matching、edge .9、100000 次／confidence .999；Point-to-Plane ICP 距離 .075m、100次、relative fitness／RMSE 1e−6；沿用 current→previous 累積、原始首相機參考。map-only 副本降採樣不改位姿／因素。任何不同設定須先記錄，不依 GT 搜尋。
5. 一次完整 FullBatch First-Pass，N 張／N−1 對、不先過濾；實際八因素 RawPointCount、VoxelizedPointYield、CoarseRANSACFitness／RMSE／Correspondences、ICPInlierFitness／RMSE／Correspondences 全記錄，2N＋6(N−1)。不以品質預覽、區域設定或 GT 代填量測；失敗則保持未完成狀態，不能封存假成功。
6. 驗合法 Turtle、Declaration bytes／Seal、因素完整性與同次 pipeline 數值、正式 Baseline Run；保存同次完整 estimated poses、pair transforms、map／圖像來源、資源／完整時間。避免 Phase 1 原 M2 缺少完整點雲而限制後續比較的問題；控制另存資料量，繪圖抽樣須揭露。
7. 官方 Explore／Query 及診斷圖，檢視八因素分布與失敗區段；Mean L2 以原始首姿態對齊、無最佳擬合。保存去天花板 Point Cloud、紅 Estimated／黑 GT、完整評估 N／時間範圍／CPU／總RSS／點數與繪圖設定。Runtime 邊界須一致（另列後處理），單次時間不宣稱顯著優勢。
8. 人工驗收完整 Baseline 與 Data Verification 後才決定 P2-B 的正式規則／SPARQL，及是否啟動 P2-C。Selected 的重建／正式 run 寫入須符合既有 CLI `--write` 契約，保留 Baseline／Declaration／Seal 與舊因素，新增鄰接因素來源不能混淆。

不得用修補／略過壞影格來湊齊數量，不以重跑未記錄的新 seed 取代第一次結果。必要修改核心、公開 CLI、Ontology、Pixi 或採集流程只能提出最小修正方案與影響，等待人工核准。

## 11. 本次驗證、已知限制與停止點

新增 `scripts/m4_capture_check.py` 與純暫存合成測試 `tests/test_m4_capture_check.py`。安全測試針對父目錄／既有目錄／斷裂符號連結拒絕、preflight 不建立目錄、缺配對／GT列數／非有限值／非法四元數／8-bit Depth／損壞 PNG／非標準檔名等明確失敗、稽核前後原檔不變、單位／位移／重複影格描述。不呼叫模擬器或配準。

本次針對性驗證：

```bash
OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 pixi run --locked -e habitat \
  python -m pytest -q tests/test_m4_capture_check.py tests/test_capture_inputs.py \
  packages/simulator/tests/test_effects.py packages/simulator/tests/test_import_surface.py
```

結果 **48 passed in 1.91s**。沒有跑會建立 Engine／replay 的 `test_e2e.py`、完整重建、Declare／Explore 或既有正式資料配準；不將未跑項目列通過。正式啟動區塊僅靜態語法／安全檢視，未藉測試偷跑。

必要風險保留：目前視窗／導航／PNG寫入未重新實測；實際房間拓樸待人工觀察；事件批次造成舊畫面存檔；異常退出缺 GT；imwrite 未檢查成功；無每影格 timestamp／動作記錄，人工採集不能以 seed 完全重播光照與噪聲。替代是分開操作、正常退出、完整驗證與來源／原始檔保全。若要核心增補 timestamp、成功回傳檢查、原子 checkpoint 或原生拒覆寫入口，先提案並核准，不能本次擅改。

M4.0 保持 main、無 remote、Snapshot `291209750bd8ecf84f337112c9b92307e6be192a`；小步提交工具／測試及計畫。起始 2024 項既有檔案 SHA 清單位於 `research_outputs/m4_20261119_preflight_01/protected.before.json`；結尾保全／來源／測試證據另存該新目錄，原 Phase 1 歷史紀錄不改寫。2024 項前後 SHA 全數相同；工具／測試提交為 `3aa1b3e`，本計畫以後續獨立 docs commit 保存，最終來源 SHA／提交見同目錄 `provenance.json`。

**M4.0 至此停止，等待人工驗收與使用者親自進行 M4.1；沒有授權自動正式 Capture、Phase 2 重建、Bonus 或英文報告。**
