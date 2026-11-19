# Phase 2 結果整理與交接

日期：2026-11-19（臺灣）。狀態：**M4.2／M4.3技術驗收通過，研究結果與素材整理完成，已停止；供人工最終驗收，尚未提交最終作業。**

正式決策：P2-C Different Route已取消。歷史計畫原文不改，詳見 [取消紀錄](M4_Phase2_P2C_Cancellation_Decision.md)。不採第二路線、不建立P2-C Capture／Experiment、不安排P2-C重建。

## 正式結果

|項目|P2-A FullBatch|P2-B sparse-v1|
|---|---:|---:|
|影格／配對|320／319|204／203|
|保留比例|100%|63.75%|
|完整Mean L2(m)|0.07025845236530649|0.04487258932911286|
|Same-Frame Mean L2(m)|0.07170949737501646|0.04487258932911286|
|Worker時間(s)|220.751497|163.365968959|
|重建函式時間(s)|207.318515709|145.343667667|
|完整地圖點數|2054529|1277572|
|八因素觀測數|2554（Turtle及Observer）|1626（新Observer；未改原因素）|

同原首相機／同GT索引，未最佳擬合。Same-Frame範圍相同但輸入資訊不同：P2-A用了320張，P2-B只用了S。Worker減少26.00%；本次Same-Frame誤差下降，主要可見布局仍保留。Baseline→Selected距離≤0.20m之全點比例99.9975%，0.20m佔據IoU0.8049。此為相對觀測地圖一致性，不能寫成全樓層／所有房間完整率。

P2-B僅一次正式重建，40項原生測試及11項必要Preflight全通過。原後處理因float32 GT轉型順序造成3.2×10⁻⁹m檢核差異而停止；只修復離線分析，未重新重建、放寬容許值或改Selection。原停止收據、原Manifest與文件bytes已保留，新結案記錄另存。

## 證據與報告素材

- [M4.2驗收](M4_Phase2_P2A_Baseline_Acceptance.md)、[M4.3完整驗收](M4_Phase2_P2B_Selected_Acceptance.md)：來源、八因素、凍結假說／規則／SPARQL、完整數據、六項研究回答與SHA。
- `docs/implementation/m43/selection_rule.json`／`p2b_sparse.rq`：唯一凍結規則及204個原索引。規則SHA `2117058e33c89b84f44c63a8ae3e1f48592e86e1d15d5db47889924605d8dabe`。
- `research_outputs/m43_p2b_preparation_01/`：Baseline八因素時序／分布、原RGB診斷接觸表、非GT相對運動、逐張保留原因、Manifest。
- `research_outputs/m43_p2b_selected_01/`：原正式CLI、程序樹RSS、原失敗後處理、同次完整位姿／配對變換／地圖、原Manifest。
- `research_outputs/m43_p2b_closeout_01/analysis/`：各自完整結果與Same-Frame表、Runtime表、八因素、全點Coverage、共同尺度俯視／軌跡／L2／分布圖。
- `research_outputs/m43_p2b_closeout_01/report_details/`：兩張同尺度3D報告圖、四象限對照、全51個相對差異點、八因素時序、配對與漂移診斷。
- 結案`audit_final.json`、`provenance.json`與`manifest.json`：歷史SHA別名快照、來源版本、資料保全與圖表來源。完整地圖與stride繪圖樣本分開；沒有隱藏重建。

## 尚餘交接事項

1. 人工最終驗收：確認地圖／轉角與缺失的描述是否符合實際採集觀察；現有資料沒有逐房間路線註記，不補造名稱或漏建結論。
2. 在另行授權的後續工作中，使用上述素材撰寫英文報告、核對作業要求並準備Submission ZIP；**本次尚未開始這些工作**。
3. 報告必須保留單Capture／單Seed／單次實驗限制。Selected局部Fitness較低、末段仍漂移、36個共同索引誤差較高；不宣稱普遍更準、統計顯著或最佳保留率。
4. 原始資料及大型產物未加入Git；最終打包前依Manifest查核本機保存成果，不能以重新重建補資料。P2-C、Bonus及其他Seed／Voxel不在本交接的待執行範圍。

到此停止，未宣稱最終作業已提交。
