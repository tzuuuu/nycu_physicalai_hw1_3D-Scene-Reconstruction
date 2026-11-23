# P2-B 單次結果與人工驗收素材

- status：Scientific validation passed; human visual acceptance pending
- runs：[{'run': 'P2-A FullBatch', 'frames': 320, 'retained_fraction': 1.0, 'pairs': 319, 'observed_factors': 2554, 'mean_l2_m': 0.07025845236530649, 'same_frame_mean_l2_m': 0.07170949737501646, 'worker_runtime_s': 220.751497, 'reconstruction_function_s': 207.318515709, 'observer_overhead_s': 0.5259152819989332, 'map_points': 2054529, 'peak_tree_rss_bytes': 1198620672}, {'run': 'P2-B Selected', 'frames': 204, 'retained_fraction': 0.6375, 'pairs': 203, 'observed_factors': 1626, 'mean_l2_m': 0.04487258932911286, 'same_frame_mean_l2_m': 0.04487258932911286, 'worker_runtime_s': 163.365968959, 'reconstruction_function_s': 145.343667667, 'observer_overhead_s': 0.89128881200077, 'map_points': 1277572, 'peak_tree_rss_bytes': 751648768}]
- worker_time_reduction_fraction：0.25995532905038454
- function_time_reduction_fraction：0.2989354222899714
- same_frame_mean_l2_difference_m：-0.0268369080459036
- preregistered_tradeoff_criteria：{'worker_time_reduced': True, 'same_frame_error_increase_within_0_05m': True, 'observed_map_coverage_at_least_0_85': True}
- tradeoff_supported_under_preregistered_criteria：True
- selected_max_l2_m：0.15586379953318497
- selected_max_l2_original_frame：320
- turtle：{'historical_triples': 22692, 'added_selected_triples': 211, 'baseline_factors_retained': 2554, 'declaration_bytes_unchanged': True, 'seal_valid': True}
- new_selected_measurements：1626
- coverage：{'source_points': 2054529, 'target_points': 1277572, 'threshold_m': 0.2, 'fraction_within_threshold': 0.9999751767923452, 'median_distance_m': 0.014976429550525246, 'p95_distance_m': 0.06684058410856566}
- runtime_caveat：Worker includes imports, observer/export, evaluation, native image and Turtle write. Baseline measures/seals 2554 factors; Selected queries and writes run only. Neither includes preflight or separate comparison/plot worker. Function timer is the secondary consistent computational boundary.
- fairness：P2-A uses 320 historical inputs; P2-B only S. Same-frame evaluation equalizes targets, not reconstruction information.
- conclusion_limit：One realization, no significance or optimal retention inference; geometry/coverage needs visual review.

品質因素分布與場景象限關係為描述性證據；新配對跨距與取樣組成已改變，不能直接將分布變化當成因果。圖中缺失須人工對照房間／轉角觀測，不能由點數比例推論完整率。單次實驗無統計顯著性；不得調整規則重跑。
