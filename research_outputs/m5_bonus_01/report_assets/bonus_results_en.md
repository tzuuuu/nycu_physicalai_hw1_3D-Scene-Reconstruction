# Bonus: Custom ICP Implementation

## Method

We implemented Point-to-Point ICP in `my_local_icp_algorithm`. SciPy cKDTree supplies exact nearest-neighbor queries; the ICP loop, distance filtering, Kabsch rigid update, reflection correction, transform composition, and final metrics are implemented explicitly with NumPy. The existing Open3D Point-to-Plane function is preserved byte for byte. Each target tree is built once per registration, avoiding a dense source-by-target distance matrix.

Starting from the unchanged FPFH/RANSAC initialization, we retain correspondences within 1.5 times the voxel size, estimate a proper rotation and translation using centered SVD, and left-compose the update. The implementation allows up to 60 updates, stops when successive pre-update mean inlier distances differ by less than 1e-6 m, and rejects insufficient (fewer than 10) or degenerate support. Correspondences, fitness, and Euclidean RMSE are recomputed at the final transform. This stopping rule is a heuristic over changing correspondence sets, not a guarantee of ground-truth pose convergence.

## Experimental setup

We reused four historical settings: Floor 1 baseline (191 frames, seed 0), Floor 1 C1 (191 frames, seed 1), Floor 2 baseline (320 frames, seed 0), and the frozen Floor 2 sparse-v1 selection (204 frames, seed 0). Registration and map voxels were both 0.05 m. Each custom reconstruction was run once; no Open3D reconstruction was rerun. All 902 pairwise RANSAC initial transforms matched their historical references exactly. GT was used only after reconstruction for evaluation in the fixed first-camera reference, with no fitted trajectory alignment.

## Results

|Condition|Frames|Open3D Mean L2 (m)|Custom Mean L2 (m)|Historical recorded time (s)|Custom worker time (s)|Custom ICP time (s)|
|---|---:|---:|---:|---:|---:|---:|
|f1_baseline|191|3.174055|3.311659|286.378|327.498|37.207|
|f1_c1|191|0.155697|0.409297|301.956|334.587|37.768|
|f2_baseline|320|0.070258|0.607972|220.751|264.269|35.227|
|f2_sparse|204|0.044873|0.347112|163.366|190.339|25.582|

The custom implementation had higher trajectory error and longer recorded worker time in all four comparisons. Its mean Euclidean inlier RMSE was lower in every condition, illustrating that nearest-neighbor residual quality does not guarantee global trajectory accuracy. In the Floor 1 baseline, the 103-to-104 RANSAC rotation error was 176.075 degrees; custom ICP retained a 176.306-degree error, whereas historical Open3D ICP retained a 179.778-degree error. Neither local method recovered the correct pose from this initialization. C1 also accumulated additional drift before this transition, so its difference cannot be attributed solely to that pair.

For Floor 2, evaluating the full custom trajectory only on the same 204 retained indices gave Mean L2 = 0.609551 m, versus 0.347112 m for the sparse custom reconstruction. The corresponding historical Open3D values were 0.071709 and 0.044873 m. Thus, the frozen density reduction also reduced observed error and recorded runtime with the custom backend in this capture; the full reconstruction nevertheless used more observations, and this is not a comparison at equal input information.

All 902 registrations returned valid support: 899 met the distance-change stopping rule, and three reached the 60-update budget. Completion therefore does not imply convergence for every pair or correct global geometry. The maps retain recognizable layouts but show boundary offsets, scattered surfaces, and trajectory drift, especially in the Floor 1 baseline and the custom Floor 2 results.

## Interpretation and limitations

Point-to-Point and Point-to-Plane optimize different objectives and use different update budgets (60 versus 100) and stopping rules. The study does not isolate these effects. Historical runtime boundaries, dates, and instrumentation differ. Custom ICP call-to-return timing includes validation, array preparation, tree construction, all queries and updates, final metrics, and profiling overhead. Worker time additionally includes imports, declaration/validation, map export, evaluation, PNG generation, and Turtle recording; it excludes later exploration and offline plotting. Historical pure-ICP times are unavailable, so no pure ICP speedup or statistical significance is claimed.

The original Floor 1 baseline has no saved complete point cloud; its native image is retained, and its trajectory and initial transforms come from a previously verified matching diagnostic, explicitly identified in the figures. C1's historical cloud is a saved stride sample. Custom full maps and both historical Floor 2 full maps are saved separately from plotting samples. Ceiling removal and red-estimated/black-GT plotting conventions are consistent; no absolute floor-coverage percentage is available without surface ground truth. These are single-capture, single-run comparisons and do not establish a generally optimal seed, voxel size, or density.

Figure captions and source hashes are supplied alongside the reviewed figures. This material is an English Bonus section draft, not the final assignment report or submission ZIP.
