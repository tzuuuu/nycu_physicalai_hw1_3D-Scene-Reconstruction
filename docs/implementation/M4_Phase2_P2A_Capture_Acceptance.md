# M4.1 P2-A 最後驗收 — SHA 異常停止紀錄

日期：2026-11-19（臺灣）；學號：114753116。

**M4.1 尚未通過最後驗收；未核准原始資料正式凍結完成或進入 First-Pass Baseline。** 使用者已完成正式採集並提供人工涵蓋確認，但依本次「SHA 或完整性異常即停止」要求，發現兩個 `.DS_Store` 歷史 SHA 差異後停止驗收。不自行新增中繼資料例外、不修復／刪除／改寫原始資料或歷史清單。本次沒有執行 M4.2。

## 1. 本次範圍與證據

Capture 完整路徑：

```text
/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/eval/_data/second_floor/114753116/P2_A_01
```

- 使用者自行採集 **N=320**，原始影格保留，未刪重複影格、重編號或更改 GT。
- 採集來源：`research_outputs/m4_capture_P2_A_01/{start.json,finish.json,capture.safe.yaml,protected.before.json}`。
- 既有資料驗證：`research_outputs/m41_verify_P2_A_01/verification.json`。
- 本次新增停止紀錄：`research_outputs/m41_p2_a01_acceptance_01/acceptance_stopped.json`；該目錄另存原始紀錄 bytes 副本、引用 SHA 清單、目前兩個中繼檔 bytes、人工確認與 manifest。**原 start／finish／verification 未覆寫。**
- 採集及既有 verify 的 Git Commit：`f55b64f7dac44cfc460401e2cbdad01c2d782f1b`；本次檢查開始亦為同一 commit。最終文件提交另由 Git 與停止目錄 `provenance.json` 識別。
- Snapshot 維持 `291209750bd8ecf84f337112c9b92307e6be192a`，main／本機 Git 制度不變。

## 2. 阻擋項：精確 SHA 差異

|路徑與比對基準|歷史預期 SHA-256|目前 SHA-256|
|---|---|---|
|`eval/_data/second_floor/.DS_Store`；採集 `protected.before.json`|`fcb90c14cc60580b59df6ebebc6e9bbf378c392725f5a7d15e68a6f611686f31`|`4809a73fa9c2fe9f60e7deb62dba2884135ad96a41aa653f962d922415c0141c`|
|`eval/_data/second_floor/114753116/P2_A_01/.DS_Store`；`finish.json` 的 capture_sha256|`8961dff668c4e95fcb71c6200f79d017532bb7cfd0d45679e46ae31346335bee`|`382cc84dd10e9e27e63c215ad17a6d9bf0309572ddd0c1f64a39fd2de05eac0a`|

`finish.json` 已記錄 `protected_changes=["eval/_data/second_floor/.DS_Store"]`，所以 **load.py 的 returncode=0 不代表外層保全流程成功**；M4.0 的受保護啟動程式在寫完 finish 後，遇到該差異應拋出保全失敗。原紀錄中 `verification=pending` 亦保留，不倒填為成功。

Capture 根目錄 `.DS_Store` 的目前值與稍後既有 verification 相同，但與 finish 不同。因此不能聲稱「自採集完成後全部 Capture 檔案皆未異動」。既有 verify 的 warnings=[] 是資料檢查告警，不是跨歷史 SHA 保全的通過證明。

這兩個檔案為 macOS 慣用中繼資料檔名；本次保存目前 bytes，但不推測變動者、時間或內容原因。Phase 1 先前核准的其他精確 `.DS_Store` 路徑，不自動適用這兩個新路徑。停止條件來自使用者本次指示與既有嚴格保全制度，不是自動核准審查拒絕。

## 3. 已確認的資料與來源狀態

本次重新計算全部 Capture 檔案 SHA 及採集保護清單／來源 SHA。發現差異後停止驗收，不再執行新影像解碼稽核、模擬器、配準或重建。以下格式結論引用 SHA 一致的既有 verification 與已保存檢查器契約，不能冒稱本次重新跑過完整 verify。

|項目|實際證據與判定|
|---|---|
|影格與索引|既有 verification 記錄 320 組，indices 精確為 1..320，320 筆逐影格檢查；當前清單仍有 RGB 320 張、Depth 320 張，無 SHA 缺檔或新增影格|
|RGB|既有檢查通過 uint8 512×512×3 PNG；320 張逐檔 SHA 與 finish、verification 一致|
|Depth|既有檢查通過 uint16 512×512 PNG；毫米儲存，除1000轉公尺；320 張逐檔 SHA 與 finish、verification 一致|
|GT_pose.npy|既有檢查通過 float32 (320,7)、有限值、單位四元數；世界 color sensor `[x,y,z,qw,qx,qy,qz]`；SHA 與兩份紀錄一致|
|intrinsics.json|512×512、hfov=90°，三欄契約；與採集 start 的 camera／原 config 設定相符；深度單位來源在 provenance，不擅自新增 JSON 欄位|
|完成到現在的科學資料|640 張 PNG＋GT＋內參，共 **642 項科學檔案**與 finish 完全一致；643 項全 Capture 檔案中僅根目錄 `.DS_Store` 不同|
|既有 verify 到現在|全部 **643 項**與 verification.sha256 精確相同，無缺項／新增／內容變更；這只證明兩次已保存觀測的一致性，不能排除期間曾改動後復原|
|採集保護清單|1215 項均存在，1214 項 SHA 相符；唯一差異為二樓父目錄 `.DS_Store`。在此清單範圍內未發現 Phase 1 或其他科學資料被覆寫，不擴稱已完成所有歷史清單的重新稽核|
|來源版本|start 記錄的19項來源 SHA 全相符，source_changes=[]；安全 YAML SHA 仍為 `5f60aa0ba6c3c6f67b06fe8687d9bf48d1dd00b0a387502a09d0ae613855db19`|
|保存／路徑|原始 Capture、採集 provenance、既有 verification、本次停止目錄各自獨立；本次沒有建立 `experiments/p2_114753116_a01_baseline_01`|

採集時間來自 start／finish：2026-11-19 **14:21:40 至 14:30:45**（臺灣）；這是採集工作階段時間，不能當成重建 Runtime。既有 verify：**14:32:00**（臺灣）。本次精確檢查時間以新增 `acceptance_stopped.json.checked_at_taipei` 為準。

start 記錄 Python3.9.23、NumPy1.26.4、Pygame2.6.1、OpenCV4.8.0.76、PyYAML6.0.2、Open3D0.18.0、RDFLib7.1.4，平台 macOS26.7.1／arm64。原始 config 的科學設定保留；衍生安全 YAML 的 output 指向獨立批次、clear_existing=false。來源與完整 argv 以 start 原始 bytes／SHA 為準，沒有重寫紀錄。

## 4. 涵蓋確認與位姿描述必須分開

正式保存使用者本次人工確認：

> 已涵蓋二樓所有可到達的主要房間及通道。

使用者另說明包含房間之間的連通區域。此為**使用者採集路線涵蓋確認**，不推導任何未量測的涵蓋百分比，不等於重建地圖已涵蓋全部房間。

未在 Capture、採集紀錄或驗證目錄中找到既有 route_notes；**尚缺詳細逐段路線紀錄**。沒有自行編造房間名稱、行走順序、轉角或影格區間。實際320張超過M4.0暫定120～200張，保留實際數量，不裁減湊回規劃張數。

既有 verification 的 GT 離線描述：相鄰位移 min／median=0、p95約0.200000m、max約0.471471m；旋轉角 median約5.999841°、max約6.000060°；位移小於1e−5m的相鄰對191組。採集位姿弦長合計約25.801237m，**不是完整行走里程**，可能略過未拍路段。這些數值僅描述採集位姿，不是配準初值、品質判定或選影格依據。

原有完全相同解碼 RGB 群組為 [55,63]、[56,62]、[57,61]、[58,60]、[195,196]；保持所有原影格。Depth 無效比例：median=0、p95約16.40%、max約18.80%；warnings=[] 不表示沒有重複視角，也不表示所有配準將成功。

四種狀態分開保存：

1. **人工採集涵蓋**：使用者已確認上述範圍。
2. **Capture 結構**：既有 verify 通過，原科學資料 SHA 相符；跨歷史全檔保全仍有阻擋。
3. **GT 位姿描述**：僅有離線位移／轉角描述，不保證幾何重疊率或重建品質。
4. **Scene Coverage／Map Completeness**：尚未重建，未評估；不能由前三項代替。

## 5. 凍結與核准狀態

本次新增紀錄保存 finish 與 verification 的兩份**參考 SHA 清單**，保留差異，不將現在的值替換歷史預期值。原始資料持續保留原樣；沒有設定檔案權限、刪除中繼檔或重寫 manifest 來強制通過。

- `m41_accepted=false`
- `capture_freeze_accepted=false`
- `eligible_for_first_pass_after_acceptance=false`
- `m42_execution_authorized=false`

需要人工處理的範圍是上述**兩個精確路徑的歷史 SHA 差異**；如未來明確核准僅對這兩個檔案採中繼資料政策，應另立新恢復紀錄，保留原停止證據／歷史SHA與目前bytes，再完成 M4.1，不能全域忽略 `.DS_Store` 或更改原始科學資料。此文件本身不構成例外授權，也沒有據此修改工具。

## 6. M4.2 預定步驟（未啟動，受 M4.1 與人工核准雙重門檻限制）

因 M4.1 尚未通過，本節只保留使用者指定的下一階段範圍，不建立 Declaration 或執行命令。

|設定|固定預定值|
|---|---|
|Experiment|`p2_114753116_a01_baseline_01`|
|Floor／Input|2／完整原始 P2_A_01 的320張，首影格固定|
|Registration voxel／RANSAC seed|0.05m／0|
|ICP|Open3D Point-to-Plane，RANSAC 提供初值|
|Map-only down voxel|0.05m，僅地圖副本；不是最佳參數宣稱|
|預期完整量測|320張、319對，2×320＋6×319＝**2554筆**品質因素|

未來正式順序：

1. 人工先處理本次保全阻擋、另次完成 M4.1，再明確核准 M4.2；核對凍結資料／核心／lock SHA，獨占建立新 workspace 與觀測目錄。
2. 執行前確認總RSS **3 GiB（3221225472 bytes）**護欄、程序樹監測權限、磁碟與資源；若監測不可用則停止，不先啟動再補監測。
3. 官方 Experiment Declaration，floor2、完整批次與預定參數／來源；不選影格或預先設定品質 Pass/Fail。
4. 單次完整 First-Pass RANSAC→Point-to-Plane ICP，逐張／逐對記錄真實八因素；保存同次完整 Estimated Poses、319個 Pairwise Transforms 及可追溯地圖來源。不得借用GT作初值或補正。
5. 成功才驗證正式 Turtle、完整2554筆因素、Declaration／Seal與Baseline Run，計算固定首相機參考系 Mean L2，保存完整時間、資源、去天花板場景與紅 Estimated／黑 GT。
6. 官方 Explore／Query與因素／地圖檢視；區分機器完整性、因素描述與重建涵蓋結果，等待人工驗收。

若首次重建失敗／觸及護欄，保存真實影格／配準對、已測因素、例外與時間／資源，不偽造完整量測、不改 Seed／Voxel／影格集合、不自動重跑直到成功。不開始 P2-B、P2-C、Bonus 或英文報告。

**本次以 SHA 異常停止紀錄交付；M4.1 未通過，M4.2 未核准、未執行。**
