# Phase 1 figure captions (asset drafts, not the final English report)

## single_runs/M2_baseline_native.png

Original M2 baseline reconstruction (191 frames; registration voxel 0.05 m, seed 0; map voxel 0.05 m; Mean L2 3.174055104788 m). The ceiling-cropped scene is shown with the estimated trajectory in red and ground truth in black, in the capture-first-camera reference. This is the original saved PNG; sparse legacy rendering and its native view limit visible scene detail.

## single_runs/M31_selected_native.png

Original M3.1 Selected reconstruction (190 frames, excluding frame 104; Mean L2 4.200397987246 m). The saved ceiling-cropped scene and red estimated / black GT trajectories show the negative ablation outcome. Native camera limits differ from the M2 screenshot; this copy is not a harmonized metric map comparison.

## single_runs/Selected_topdown.png

M3.1 Selected: exclude frame 104 reconstruction (190 frames; map voxel 0.05 m; Mean L2 4.200397987246 m). The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. The retained route is displaced and extended after the new 103-to-105 mismatch. Exploratory ablation informed by prior GT diagnosis; not a GT-independent selection rule.

## single_runs/B0_topdown.png

B0: v=0.05 m, seed=0 reconstruction (191 frames; map voxel 0.05 m; Mean L2 3.174055104788 m). The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. The late route is visibly displaced following the 103-to-104 rotation mismatch. 

## single_runs/B2_topdown.png

B2: v=0.08 m, seed=0 reconstruction (191 frames; map voxel 0.05 m; Mean L2 0.274959466593 m). The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. The estimated route is closer to GT than the flipped controls, but residual displacement remains. 

## single_runs/C1_topdown.png

C1: v=0.05 m, seed=1 reconstruction (191 frames; map voxel 0.05 m; Mean L2 0.155696709607 m). The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. The estimated route is closer to GT than the flipped controls, but residual displacement remains. 

## single_runs/C2_topdown.png

C2: v=0.05 m, seed=2 reconstruction (191 frames; map voxel 0.05 m; Mean L2 3.165352438552 m). The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. The late route is visibly displaced following the 103-to-104 rotation mismatch. C2 supplemental scientific audit passed; original finalize metadata stop preserved.

## single_runs/C3_topdown.png

C3: v=0.05 m, seed=3 reconstruction (191 frames; map voxel 0.05 m; Mean L2 0.221466815796 m). The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. The estimated route is closer to GT than the flipped controls, but residual displacement remains. 

## single_runs/C4_topdown.png

C4: v=0.05 m, seed=4 reconstruction (191 frames; map voxel 0.05 m; Mean L2 3.366709232590 m). The saved ceiling-cropped scene is redrawn top-down with the estimated trajectory in red and ground truth in black, in the fixed first-camera frame, with no fitted alignment. The late route is visibly displaced following the 103-to-104 rotation mismatch. 

## comparisons/A_baseline_reference_vs_selected_maps.png

Harmonized top-down reference for the baseline/Selected comparison. Left: the separately measured B0 matched-control cloud (191 frames; Mean L2 3.174055104788 m), not the unavailable original M2 cloud. Right: actual M3.1 Selected cloud (190 frames; Mean L2 4.200397987246 m). Red is estimated trajectory and black is GT. Common first-camera bounds and identical display sampling retain the displaced geometry. The original M2 baseline scores 3.185555603874 m on the common 190 frames; Selected is 31.86% worse. No alignment or reconstruction correction is applied.

## comparisons/A_baseline_selected_errors.png

Baseline/Selected camera-center errors on the common 190 frames. The original full-191 baseline Mean L2 is 3.174055104788 m; its matching M3.0 diagnostic scores 3.185555603874 m on the retained 190 frames. Selected scores 4.200397987246 m, 31.86% worse, with the new 103-to-105 mismatch. The diagnostic baseline trajectory is not an original same-run M2 pose export. Line colors identify runs, not trajectory roles.

## comparisons/B_maps.png

Registration Pipeline Scale, seed 0: B0 (v=0.05 m, 191 frames, Mean L2 3.174055104788 m), B1 (v=0.03 m, RANSAC failure at 70-to-71; no complete map or Mean L2), and B2 (v=0.08 m, 191 frames, Mean L2 0.274959466593 m). All actual saved ceiling-cropped scenes use common top-down X/Z limits, equal aspect, and identical display sampling. Estimated trajectories are red and GT black; no fitted alignment is used. Completed reconstructions can still have poor accuracy.

## comparisons/B_mean_l2.png

Registration Pipeline Scale, seed 0: B0 (v=0.05 m, 191 frames, Mean L2 3.174055104788 m), B1 (v=0.03 m, RANSAC failure at 70-to-71; no complete map or Mean L2), and B2 (v=0.08 m, 191 frames, Mean L2 0.274959466593 m). All actual saved ceiling-cropped scenes use common top-down X/Z limits, equal aspect, and identical display sampling. Estimated trajectories are red and GT black; no fitted alignment is used. Completed reconstructions can still have poor accuracy. Bars report full-sequence errors only; no zero is inserted for B1.

## comparisons/C_maps.png

RANSAC seed sensitivity at v=0.05 m, with 191 frames per run: seeds 0/1/2/3/4 have Mean L2 values 3.174055104788/0.155696709607/3.165352438552/0.221466815796/3.366709232590 m. Seeds 0, 2 and 4 have a major 103-to-104 rotation mismatch; seeds 1 and 3 do not. All actual saved ceiling-cropped scenes use common top-down X/Z limits, equal aspect, and identical display sampling. Estimated trajectories are red and GT black; no fitted alignment is used. Completed reconstructions can still have poor accuracy.

## comparisons/C_mean_l2.png

RANSAC seed sensitivity at v=0.05 m, with 191 frames per run: seeds 0/1/2/3/4 have Mean L2 values 3.174055104788/0.155696709607/3.165352438552/0.221466815796/3.366709232590 m. Seeds 0, 2 and 4 have a major 103-to-104 rotation mismatch; seeds 1 and 3 do not. All actual saved ceiling-cropped scenes use common top-down X/Z limits, equal aspect, and identical display sampling. Estimated trajectories are red and GT black; no fitted alignment is used. Completed reconstructions can still have poor accuracy. Bars report full-sequence errors only; no zero is inserted for B1.

## diagnostics/per_frame_l2.png

Per-frame L2 errors from six complete M3.2 runs (191 frames each) and the actual M3.1 Selected run (190 frames). The original frame identity is preserved. B1 has no full-sequence curve because it failed at 70-to-71. Colors identify runs; this is an error plot, not a map. High-error seeds are retained.

## diagnostics/local_registration_errors.png

RANSAC and ICP local rotation/translation errors for all six complete M3.2 runs, evaluated offline using their saved same-run matrices and fixed first-camera GT convention. B0/C2/C4 have major rotation mismatches at 103-to-104; B2/C1/C3 do not. B1 has no complete sequence. No registration is rerun and no matrix is replaced.

## diagnostics/pose_flip_103_104.png

The saved B0 control (v=0.05 m, seed 0, 191 frames; full Mean L2 3.174055104788 m) shows a coarse rotation error of 176.074504 degrees at 103-to-104 and an ICP error of 179.778159 degrees. ICP reduces local residuals without recovering the correct pose; the wrong orientation then affects global motion accumulation. These are offline errors from frozen results, not a new registration experiment.

## diagnostics/B_eight_factors.png

B pipeline-grounded factor timelines. Complete runs contain 191 single-frame and 190 pair measurements per factor type. B1 contributes only the actual unsealed prefix through its failed 70-to-71 pair (562 observed values total); it is not a complete factor set. Fitness and correspondence RMSE are internal metrics at native thresholds and do not establish GT pose accuracy. VoxelizedPointYield is a count, not a proportion.

## diagnostics/C_eight_factors.png

C pipeline-grounded factor timelines. Complete runs contain 191 single-frame and 190 pair measurements per factor type. All five seeds are shown, including overlapping raw-count/yield curves and high-error seeds. Fitness and correspondence RMSE are internal metrics at native thresholds and do not establish GT pose accuracy. VoxelizedPointYield is a count, not a proportion.

## diagnostics/existing_pair_cloud_projections.png

Existing M3.0 diagnostic cloud projections for 103-to-104. Saved coarse/ICP transforms and the offline GT reference are applied for diagnosis; no new RANSAC/ICP is run and GT is not used to correct a reconstruction. This is a local projection diagnostic, not a full-floor map.

