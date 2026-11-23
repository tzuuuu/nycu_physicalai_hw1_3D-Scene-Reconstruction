# Phase 1報告素材

本目錄只保存F2素材，不是正式ZIP或英文最終報告。所有圖片由既有正式PNG、已保存點雲／位姿／CSV離線產生；沒有讀取原始RGB-D重建、配準、GT擬合或修正錯圖。

## 使用

優先使用single_runs中的Selected／B2／C1／C3 Top-down與M2原生PNG；B0／C2／C4同樣保留，不隱藏負面條件。comparisons包含A／B／C圖，diagnostics保存各誤差與八因素。captions/figure_captions.md為英文Figure Caption素材。完整來源、尺寸、SHA與限制在manifest.json。

## 已知限制

- Original M2 did not retain its same-run full cloud or poses. The original PNG is preserved; no exact new M2 top-down map can be made without new reconstruction.
- The harmonized Baseline/Selected map comparison uses the explicitly labeled B0 matched-control cloud; it is not the original M2 map.
- Saved clouds were already ceiling-cropped by the original pipeline, and were originally stride-sampled. New rendering uses the same 90,000-index cap on each saved sample; lost detail cannot be recovered.
- Isometric views are not required here; original native PNGs provide their original viewpoints. No synthetic scene or repaired reconstruction is used.

B1沒有完整地圖或完整Mean L2，data/run_comparison.csv的70是已接受位姿前綴，不是完整重建或已評估190/191張。M2原生圖不放大捏造細節；A等尺度地圖參考明示使用B0控制組。所有新地圖只顯示保存且已裁天花板的取樣，不能量出全樓層正確涵蓋百分比。

## 視覺驗收

請參考visual_review.json；previews為檢視用聯絡表，不是新增科學結果。原生PNG沒有宣稱300 dpi重繪；其餘新Matplotlib圖以300 dpi輸出。
