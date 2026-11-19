# M4.1 — P2-A Capture 恢復驗收

日期：2026-11-19（臺灣）；學號：114753116。

**M4.1 — P2-A Capture Accepted / Scientific Data Frozen / Ready for M4.2 Authorization**

M4.1 正式通過。Scientific Data Frozen 指已確認並保存 **642 項科學資料的接受版本與 SHA**，不表示抹除歷史差異、改變原始採集成功狀態或以檔案權限鎖定資料。**M4.2 仍未授權、未執行，且有執行前阻擋項。**

本文件為新增恢復驗收，不改寫 [原始停止文件](M4_Phase2_P2A_Capture_Acceptance.md)。原始 start、finish、verification、acceptance_stopped、既有 manifest 與所有歷史 SHA／停止紀錄均原樣保留。

## 1. 授權與獨立證據鏈

本次使用者明確核准的例外僅為：

1. `eval/_data/second_floor/.DS_Store`
2. `eval/_data/second_floor/114753116/P2_A_01/.DS_Store`

僅在本次 `research_outputs/m41_p2_a01_acceptance_01/resume_01/` 恢復流程使用。該目錄啟動前確認不存在，獨占建立；未重用既有輸出。Phase 1 的三個例外清單、原 `m4_capture_check.py`、既有 SHA 驗證及教師核心均未修改。

|新增證據|內容|
|---|---|
|`resume_01/authorization.json`|精確兩路徑、使用者授權、範圍與禁止 M4.2、舊停止目錄檔案的 SHA 錨點|
|`resume_01/metadata_history_and_type.json`|兩個檔案歷史／目前 SHA、一般檔案／連結狀態、file 類型、檔頭與授權 SHA|
|`resume_01/metadata_checks.jsonl`|逐次歷史 SHA 比較、是否差異、例外是否生效與授權 SHA；不以萬用字元放寬|
|`resume_01/scientific_data_frozen_sha256.json`|642項正式接受科學檔案，使用專案相對路徑逐檔保存SHA|
|`resume_01/scientific_comparison.json`|642項 finish／verification／本次SHA逐項比較，全部 match=true|
|`resume_01/fresh_verification.json`|重新逐張解碼／尺寸／型別、GT、內參、Depth、離線位姿描述，非引用舊結果冒稱新實測|
|`resume_01/protected.before.json`|本次2699項既有檔案的起始保護快照；不取代歷史預期值|
|`resume_01/prior_manifest.original.json`、`prior_manifest_limit.json`|原停止manifest bytes副本及原始自我列項缺陷的說明|
|`resume_01/recovery_stopped.json`|本輪恢復腳本在M4.2唯讀ps權限探測停止的原始Traceback，未刪除／改成成功|
|`resume_01/completion_01/acceptance.json`|**本次正式M4.1補充完成驗收**，明列歷史失敗、科學資料凍結與M4.2未授權|
|`resume_01/completion_01/m42_preflight.json`|M4.2預定設定、監測權限／程序樹與來源保存阻擋項|
|`resume_01/completion_01/tests.log`|本輪31項針對性測試結果|
|`resume_01/provenance.json`、`manifest.json`|最終Git／文件／來源SHA與恢復產物清單；manifest不列入自身|

授權檔本身 SHA 被寫入每次例外檢查。未提供此授權檔與精確恢復日誌時，新增政策函式 `verify_hashes` 預設嚴格；不使用跨流程的全域例外狀態。一般 SHA 驗證與科學資料比較完全不套用例外。

## 2. 兩個精確中繼檔的結果

兩者均是**既存一般檔案、非符號連結**；`file -b` 實際辨識為 `Apple Desktop Services Store`；前8 bytes均為 `0000000142756431`（版本1＋Bud1）。未刪除、還原或寫入這兩個檔案。

|路徑|歷史SHA-256|本次SHA-256／結果|
|---|---|---|
|二樓父目錄 `.DS_Store`|採集保護清單：`fcb90c14cc60580b59df6ebebc6e9bbf378c392725f5a7d15e68a6f611686f31`|`4809a73fa9c2fe9f60e7deb62dba2884135ad96a41aa653f962d922415c0141c`；僅本次明確例外放行歷史差異|
|P2_A_01根目錄 `.DS_Store`|finish：`8961dff668c4e95fcb71c6200f79d017532bb7cfd0d45679e46ae31346335bee`|`382cc84dd10e9e27e63c215ad17a6d9bf0309572ddd0c1f64a39fd2de05eac0a`；僅本次明確例外放行finish以後的既有差異|
|P2_A_01根目錄 `.DS_Store` 對既有verification|`382cc84dd10e9e27e63c215ad17a6d9bf0309572ddd0c1f64a39fd2de05eac0a`|完全相同；這項比較**未套例外**|

沒有第三個未核准差異，沒有將任何 PNG、GT、內參、TTL、Seal、程式或 YAML 列為例外。舊中繼檔 bytes 複本與歷史SHA均保留，歷史清單沒有被現在值替換。

## 3. 原始失敗事實與本輪程序停止

正式沿用以下敘述：

> 原始採集流程曾因OS中繼資料SHA差異觸發停止；經人工核准精確中繼資料例外後，透過獨立後續驗證確認科學資料完整性。

`m4_capture_P2_A_01/finish.json` 的 `returncode=0`、`protected_changes` 與 `verification=pending` 全數未改；外層保全失敗仍是真實歷史，不能改稱原始流程完整成功。

本輪資料重驗完成後，恢復腳本嘗試唯讀 `/bin/ps`，受到沙箱 `PermissionError: Operation not permitted` 拒絕。這次腳本因此留下 `recovery_stopped.json`，未產生成功收據。本次沒有重用目錄或重跑該腳本；新增 `completion_01/`，引用已保存的重驗結果，再嚴格核對科學檔案、舊紀錄及整次2699項起始清單後完成M4.1。該ps停止只涉及尚未授權的M4.2監測能力，並未發現科學資料異常；停止Traceback仍保留。

另查明前次停止紀錄的 `manifest.json` 原本誤將**自身建立時空檔**SHA列為自身SHA。這是先前產製紀錄的缺陷，該自我列項不是可成立的自我雜湊，不能宣稱它驗證通過。本次保留原檔與其錯誤列項，嚴格驗證其餘12項，並以新授權／來源紀錄綁定原manifest的完整bytes與目前SHA。這不是將第三個實際檔案異動加入例外，也不更新舊預期值。新manifest先計算其他檔案清單再建立自身，避免重複該缺陷。

## 4. 科學資料與來源驗收

Capture完整路徑：

```text
/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/eval/_data/second_floor/114753116/P2_A_01
```

|檢查|本次結果|
|---|---|
|RGB／Depth|各320張；索引精確1..320、配對完整，逐張可解碼|
|RGB|uint8、512×512×3 PNG|
|Depth|uint16、512×512 PNG，儲存毫米、除1000為公尺；非8-bit預覽|
|GT_pose.npy|float32 (320,7)，所有值有限、四元數為單位長度；世界color sensor `[x,y,z,qw,qx,qy,qz]`|
|內參|恰width=512、height=512、hfov=90.0°；與原始Config／start設定一致，原JSON不加深度尺度欄位|
|科學檔案|640張PNG＋GT＋內參＝642項；finish、既有verification、本次SHA逐項完全一致|
|全部Capture|643項（含根目錄.DS_Store）與既有verification**嚴格全部相符**；沒有新增／缺失檔案或新差異|
|採集保護清單|1215項中1214項嚴格相符，唯一歷史差異是已核准的二樓父目錄中繼檔|
|來源程式|start的19項SHA均相符，亦逐項核對採集Git Commit的bytes；沒有改教師核心／Pixi／Ontology|
|Config／安全衍生Config|原YAML不變；安全YAML SHA仍為`5f60aa0ba6c3c6f67b06fe8687d9bf48d1dd00b0a387502a09d0ae613855db19`；解析值與start一致，與原Config僅output.root、clear_existing兩欄不同|
|本次檢查期間保全|2699項起始既有檔案**完全嚴格相符，不套任何例外**；包含舊採集、驗證、停止紀錄與Phase 1研究資料|
|Phase 1成果|在採集保護清單與本次前後清單範圍內均未修改；未重新呼叫Phase 1歷史恢復／finalize或重跑研究|
|Snapshot／目錄|Snapshot固定`291209750bd8ecf84f337112c9b92307e6be192a`；Capture／採集／驗證／恢復各在獨立路徑，未建立M4.2 workspace|

科學資料重新解碼結果與原verification逐欄一致，warnings=[]。索引與清單精確相同，未透過刪重、重編號、重採或GT挑選來取得通過。來源／接受清單為資料保全版本，不宣稱已證明所有影格都能配準。

採集及既有verification commit均為 `f55b64f7dac44cfc460401e2cbdad01c2d782f1b`；本輪恢復工具／測試commit為 **`15a3027`**，正式補充驗收執行時亦為該commit，工作區乾淨。最終文件commit及驗證UTC時間見獨立provenance；臺灣時間為UTC+8。

## 5. 人工涵蓋確認與限制

正式保存使用者本次確認：

> P2-A的320張影格已涵蓋二樓所有可到達的主要房間及通道，以及房間之間的連通區域。

四者分開解讀：

1. **人工採集涵蓋**：使用者確認上述路線涵蓋範圍。
2. **Capture結構／科學SHA**：本次重新檢查通過，642項接受版本已保存。
3. **GT離線描述**：相鄰位姿弦長合計約25.801237m，不等於完整行走里程；近靜止位移191對、轉角median約6°，不能推導幾何重疊率或選擇較準影格。
4. **Scene Coverage／Map Completeness**：尚未重建，未評估，不能宣稱全部地圖已涵蓋或推導絕對涵蓋百分比。

仍缺逐段route_notes，未編造房間名稱、巡訪順序或影格區間。既有5組完全相同RGB群組及所有原影格保持。Depth無效比例median=0、p95約16.40%、max約18.80%；不將warnings=[]解讀為每段都能配準或無視角重複。

## 6. M4.2 執行前交接：設定固定，仍有阻擋

|預先設定|值|
|---|---|
|Experiment／Floor|`p2_114753116_a01_baseline_01`／2|
|Input|P2_A_01完整320張，保留原首相機參考，不先選影格|
|Registration voxel／RANSAC seed|0.05m／0|
|ICP|Open3D Point-to-Plane；RANSAC提供初值，GT不作配準輸入|
|Map-only down voxel|0.05m，只影響地圖副本，不宣稱最佳參數|
|預期配準／因素|319對；2×320＋6×319＝2554筆真實品質因素|
|總RSS護欄|3GiB＝3221225472 bytes，**需要程序樹總和**|

### 尚未解決的執行前阻擋

- **人工尚未核准M4.2。** M4.1資料就緒不等於授權開始First-Pass。
- **程序樹RSS尚未實作／驗證。** `scripts/record_command.py` 每0.5秒只查直接 `process.pid` 的RSS，超限只terminate直接子程序；不是後代程序加總／整組停止。不得以既有Phase 1單PID護欄冒充已滿足本次要求。後續需獨立監控器或非侵入式擴充，先用合成父／子程序驗證總和、3GiB上限、監測失效停止、整組終止及增量紀錄，不改教師核心；本次未實作或啟用重建監控器。
- **目前沙箱不能呼叫 `/bin/ps`。** 正式環境應先取得實際需要的程序讀取／終止權限，並驗證正常取樣、低門檻合成超限、取樣失敗的停止行為；本次不推定權限已恢復，也沒有擅自取得執行重建權限。
- **Phase 2觀測／驗收需泛化。** 現有M3工具包含191張／190對的固定斷言與既有路徑，不得直接使用其正式run入口。應在下一階段將資料識別／計數限制改為本批320／319，保留單次執行標記與異常證據，經合成測試後才能啟動。
- **同次地圖保存規格需落實。** 既有ReturnObserver會保存positions／camera_poses／transforms，但map_sample.npz最多取約150000點，屬抽樣地圖。必須明列保存格式與來源／取樣資訊，不能把抽樣宣稱為完整未取樣地圖。

### 下一階段正式執行步驟（本次未執行）

1. 獲M4.2明確授權後，先解決上述監測／觀測阻擋；核對642項凍結SHA、核心／lock、Snapshot及新workspace不存在，備份舊成果。磁碟與記憶體餘裕另測，不沿用M4.0磁碟數字作保證。
2. 建立獨立研究輸出與官方Experiment Declaration，floor2、完整Capture、固定參數與事前預測；不預先分因素Pass/Fail、不先選影格。
3. 原官方First-Pass只執行一次。非侵入式觀測同一次呼叫：逐影格／逐對增量寫events與transforms，記錄目前frame／pair、原始因素值、實際argv與參數、啟動標記及資源取樣；RANSAC／ICP失敗保留真實位置及已產生量測。
4. 成功時保存320個完整4×4 Estimated Poses、320個相機中心、319個4×4 Pairwise Transforms（current→previous）及配準初值；驗累積矩陣與同次返回相機中心一致。不以另一輪重建補圖／補位姿，亦不以GT補矩陣。
5. 保存同次返回、已去天花板且明設map-only .05m的地圖點／色來源（例如完整該返回地圖的NPZ，另存繪圖抽樣），含點數、dtype、座標系、裁切／voxel／stride與SHA；評估額外儲存峰值，使其仍受3GiB護欄。若只能保存抽樣，需事前明列限制並待人工接受，不能事後補造完整來源。
6. 核對官方Turtle／Declaration／Seal、2554筆因素與同次pipeline數值、Baseline Run；保存完整320張Mean L2、全程時間及資源。GT僅於離線描述／最終評估使用固定原首姿態參考，無最佳旋轉／平移／尺度擬合。
7. 官方Explore／Query與驗證圖，去天花板場景配紅Estimated／黑GT；圖片都連回同次地圖／位姿／參數／SHA，另列Runtime邊界、觀測成本與後處理時間。最後再驗原始資料／舊成果SHA並等待人工驗收。

若第一次重建失敗、取樣失效或觸及護欄，保留Traceback、真實失敗frame／pair、部分因素、時間與資源。不得換seed、voxel、影格集合或自動重試至成功；不得偽造完整Seal或2554筆因素。

## 7. 測試與完成狀態

```bash
OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 pixi run --locked -e habitat \
  python -m pytest -q tests/test_m41_metadata_policy.py tests/test_m4_capture_check.py
```

**31 passed in 0.29s**。涵蓋預設嚴格、僅精確兩路徑、非Finder格式／缺檔／資料夾／符號連結拒絕、授權不能擴到Phase 1或第三路徑、科學檔案／YAML／Seal等仍嚴格、政策不洩漏與原檔不變。均為暫存合成檔案，不執行RANSAC／ICP／模擬器。

正式資料另外已實際重新解碼驗證；這不計入31項合成測試，也不是First-Pass Data Verification。未執行Declaration、Experiment Workspace建立、First-Pass、P2-B、P2-C、Bonus或英文報告。

**M4.1正式完成並停止；等待人工核准M4.2，且M4.2啟動前須關閉本文件所列監測與來源保存阻擋。**
