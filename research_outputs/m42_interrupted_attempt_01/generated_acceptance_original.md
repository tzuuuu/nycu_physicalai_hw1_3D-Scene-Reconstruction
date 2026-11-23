# M4.2 — P2-A First-Pass Baseline 驗收

日期：2026-11-19（臺灣；UTC時間見證據）。

狀態：**M4.2 stopped before official reconstruction**。

工程工具與授權：本次使用者已授權完整工程準備及 Preflight 全通過後的一次正式執行。未修改教師核心、Ontology、Pixi、Capture 或歷史 SHA 政策。

正式證據目錄：`research_outputs/m42_p2_a01_baseline_01`。逐項 Preflight 位置記於 `preregistration.json`；正式命令、來源 SHA、凍結 Capture 642項 SHA、Declaration、Observer、程序樹 RSS 與 watchdog 紀錄均在該目錄。

正式設定：Floor 2、320張、319對、2554筆預期因素、registration voxel=0.05m、seed=0、Open3D Point-to-Plane、map-only voxel=0.05m、OMP_NUM_THREADS=1、程序樹 RSS 3 GiB。

實際結果：

```json
{
  "status": "M4.2 stopped before official reconstruction",
  "traceback": "Traceback (most recent call last):\n  File \"/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/scripts/m42_baseline.py\", line 297, in terminal_run\n    execution=guarded([sys.executable,str(Path(__file__).resolve()),'_worker',str(out)],out/'command')\n  File \"/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/scripts/m42_monitor.py\", line 227, in run\n    stop_workload()\n  File \"/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/scripts/m42_monitor.py\", line 160, in stop_workload\n    result=kill_group(worker.pid)\n  File \"/Users/alyssa/Documents/Codex_Workspace/physicalai_hw1/scripts/m42_monitor.py\", line 84, in kill_group\n    os.killpg(pgid, signal.SIGKILL)\nPermissionError: [Errno 1] Operation not permitted\n"
}
```

程序樹監測使用 ps 的 PID／PPID／PGID／RSS，每0.5秒加總存活後代及保留群組；RSS 包含重複計算的共享頁，屬保守取樣指標，不能保證瞬間峰值不超限。獨立 watchdog 在監測程序失聯後最多約8秒內終止本次群組。監測器與 watchdog 自身不計入科學工作負載 RSS。

成功產物完整地圖為同次正式 Pipeline 回傳、經逐影格0.05m地圖降採樣及官方去天花板後的全部點／色，分開串流儲存為 NPY；繪圖另用明列 stride 的取樣，沒有以15萬點樣本替代正式地圖。首相機座標與 float64 shape／SHA 見 map_summary.json。GT 僅於重建完成後評估；無最佳擬合。

成功時見 validation.json、baseline_comparison.csv、per_frame_l2.csv、factors.csv、factor_statistics.json、figure_manifest.json、figures/、candidate_questions.md 與官方 Explore。影像為英文報告素材，並非最終英文報告。空間分區是地圖範圍象限，不冒稱真實房間；缺少逐段路線註記與完整場景表面 GT，不能宣稱全樓層絕對完整率。失敗時只保留真實完成前綴、部分回傳及停止原因，不建立假成功 Seal、完整 Mean L2 或因素。

歷史 Phase 1／M4.1 的中繼資料停止及自我雜湊缺陷原樣保留。新 M4.2 採雙層保全；經檔名、一般檔案與 Finder 檔頭／file 類型確認的 .DS_Store 獨立記錄前後 SHA，其餘科學來源嚴格比對。

至此停止；未啟動 P2-B、P2-C、新參數／seed、Experiment D、Bonus、最終英文報告或 Submission ZIP。
