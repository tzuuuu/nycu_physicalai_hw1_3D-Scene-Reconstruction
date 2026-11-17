import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import json
import numpy as np
import open3d as o3d
import os
import cv2
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

DEPTH_SCALE  = 1000.0     # uint16 depth PNGs store millimetres
# Image axes (+X right, +Y down, +Z forward) to Habitat's sensor axes
# (+X right, +Y up, +Z backward), used by the scorer.
CAM_TO_GT_AXES = np.diag([1.0, -1.0, -1.0])



def depth_image_to_point_cloud(rgb, depth_m, width, height, hfov):
    """Back-project one RGB-D frame into a colored 3-D point cloud.

    `rgb` is HxWx3 uint8 in BGR order and `depth_m` the same frame's HxW
    depths in metres; `width`/`height`/`hfov` are that capture's own camera
    parameters (read from its `intrinsics.json` by the caller — never
    hardcoded, so one capture is never unprojected through another's
    camera). Geometry is a pinhole with square pixels, image-centre
    principal point, and focal length derived from `width` and `hfov`.

    Returns points in metres in the frame's camera frame (+X right, +Y
    down, +Z forward) with colors as RGB floats in [0, 1]. A pixel yields
    a point iff `depth_m > 0` (zero means no return and is dropped, never
    placed at the origin).
    Points come out in row-major pixel order; an all-invalid frame yields
    an empty cloud. Inputs are not modified.
    """
    # TODO: Convert `rgb` and `depth_m` to NumPy-compatible arrays and
    # validate that the depth shape agrees with `(height, width)`.
    # 確認尺寸與色彩契約，避免像素與相機參數錯配。
    rgb = np.asarray(rgb)
    depth_m = np.asarray(depth_m)
    if any(isinstance(size, (bool, np.bool_))
           or not isinstance(size, (int, np.integer)) or size <= 0
           for size in (width, height)):
        raise ValueError("width and height must be positive integers")
    if depth_m.shape != (height, width):
        raise ValueError("Depth image shape must match (height, width)")
    if rgb.shape != (height, width, 3):
        raise ValueError("BGR image shape must match (height, width, 3)")
    if rgb.dtype != np.uint8:
        raise ValueError("BGR image must have uint8 channels")

    # TODO: Convert depth values to metres when the input representation
    # requires it; follow the capture convention used by the caller and do
    # not hardcode camera parameters from another capture.
    # depth_m 依契約已是公尺；僅轉浮點數，不重複換算毫米或依型別猜單位。
    if depth_m.dtype.kind not in "uif":
        raise ValueError("depth_m must contain real numeric depths in metres")
    depth_m = depth_m.astype(np.float64, copy=False)

    # TODO: Create a row-major pixel grid `(u, v)` covering the image.
    # 列為 v、欄為 u；後續以同一遮罩維持點與色彩的逐列順序。
    v, u = np.indices((height, width), dtype=np.float64)

    # TODO: Build a validity mask and discard invalid depth values
    # (`depth <= 0`).
    # 僅保留有限正深度，避免 NaN 或無限值進入點雲。
    valid = np.isfinite(depth_m) & (depth_m > 0)
    z = depth_m[valid]

    # TODO: Derive focal lengths and the principal point from `width`,
    # `height`, and `hfov`.
    # 水平視角使用度數；方形像素令兩軸焦距相同，主點取影像中心。
    if not np.isscalar(hfov) or np.asarray(hfov).dtype.kind not in "uif":
        raise ValueError("hfov must be a finite angle between 0 and 180 degrees")
    hfov = float(hfov)
    if not np.isfinite(hfov) or not 0 < hfov < 180:
        raise ValueError("hfov must be a finite angle between 0 and 180 degrees")
    fx = width / (2.0 * np.tan(np.deg2rad(hfov) / 2.0))
    fy = fx
    cx, cy = width / 2.0, height / 2.0

    # TODO: Implement pinhole unprojection:
    #   x = (u - CX) * z / FX
    #   y = (v - CY) * z / FY
    #   z = depth
    # Use the coordinate sign convention documented by the function. In an
    # assignment variant that uses a camera looking toward `-Z`, the final
    # line is `z = -depth`; reconcile that choice with the existing
    # docstring and `CAM_TO_GT_AXES` convention before implementing.
    # 自行套用針孔公式，保留相機座標右、下、前的正軸；此處不做 GT 翻軸。
    x = (u[valid] - cx) * z / fx
    y = (v[valid] - cy) * z / fy
    points = np.column_stack((x, y, z))

    # TODO: Construct and return an Open3D `PointCloud`, including RGB
    # colors normalized to `[0, 1]` and preserving row-major point order.
    # BGR 轉 RGB 並正規化；Open3D 僅接收已手算完成的座標與色彩。
    colors = rgb[valid][:, ::-1].astype(np.float64) / 255.0
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd


def preprocess_point_cloud(pcd, voxel_size):
    """Downsample a cloud and prepare it for feature matching and ICP.

    Voxel-downsamples at `voxel_size`, estimates normals (radius
    `voxel_size * 2`, up to 30 neighbours) for point-to-plane ICP, and
    computes FPFH descriptors (radius `voxel_size * 5`, up to 100
    neighbours) for RANSAC matching. Returns the downsampled cloud and
    its FPFH feature set. Pairwise registration is performed by reconstruct().
    """
    # TODO: Voxel-downsample `pcd` with `voxel_size`.
    # 先拒絕無效尺度與座標，再由 Open3D 合併同一體素內的點。
    if (not np.isscalar(voxel_size)
            or np.asarray(voxel_size).dtype.kind not in "uif"):
        raise ValueError("voxel_size must be a finite positive number")
    voxel_size = float(voxel_size)
    if (not np.isfinite(voxel_size) or voxel_size <= 0
            or not np.isfinite(voxel_size * 5)):
        raise ValueError("voxel_size and its search radii must be finite and positive")
    points = np.asarray(pcd.points)
    if len(points) == 0 or not np.isfinite(points).all():
        raise ValueError("Point cloud must contain finite points and must not be empty")
    pcd_down = pcd.voxel_down_sample(voxel_size)

    # TODO: Estimate normals for `pcd_down`, because Point-to-Plane ICP
    # requires them. Use a hybrid KD-tree search radius of
    # `voxel_size * 2` and at most 30 neighbours.
    # 少於三點無法支持平面估計；其餘交由指定鄰域的實際幾何估算法向量。
    if len(pcd_down.points) < 3:
        raise ValueError("At least 3 downsampled points are required to estimate normals")
    pcd_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(
        radius=voxel_size * 2, max_nn=30))

    # TODO: Compute FPFH features for `pcd_down` using radius
    # `voxel_size * 5` and at most 100 neighbours.
    # 使用降採樣點與其法向量計算真實 FPFH，保持特徵欄與點的對應。
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down, o3d.geometry.KDTreeSearchParamHybrid(
            radius=voxel_size * 5, max_nn=100))

    # TODO: Return the downsampled cloud and its FPFH feature object as
    # `(pcd_down, fpfh)`.
    # 一併回傳處理後的點雲與特徵，供後續已授權階段使用。
    return pcd_down, fpfh


def _global_registration(source, target, source_fpfh, target_fpfh,
                         voxel_size, seed):
    """以真實 FPFH/RANSAC 估計 source 到 target 的粗轉換。"""
    o3d.utility.random.seed(int(seed))
    distance = voxel_size * 1.5
    return o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        source, target, source_fpfh, target_fpfh, True, distance,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        3, [o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance)],
        o3d.pipelines.registration.RANSACConvergenceCriteria(100000, 0.999))


def local_icp_algorithm(source_down, target_down, trans_init, threshold):
    """Refine an initial alignment with point-to-plane ICP.

    Estimates normals on either cloud if missing (radius `threshold * 2`,
    up to 30 neighbours), then runs up to 100 ICP iterations at the single
    correspondence `threshold`. Returns the RegistrationResult; its
    `.transformation` is the refined 4x4.
    """
    # TODO: Ensure both source and target clouds have normals, estimating
    # them if necessary.
    # 先確認有效距離與點雲；只替缺少法向量的點雲估計指定鄰域。
    if not np.isscalar(threshold) or np.asarray(threshold).dtype.kind not in "uif":
        raise ValueError("ICP threshold must be finite and positive")
    threshold = float(threshold)
    if not np.isfinite(threshold * 2) or threshold <= 0:
        raise ValueError("ICP threshold must be finite and positive")
    for cloud in (source_down, target_down):
        if len(cloud.points) < 3 or not np.isfinite(np.asarray(cloud.points)).all():
            raise ValueError("ICP requires at least 3 finite points in each cloud")
        if not cloud.has_normals():
            cloud.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(
                radius=threshold * 2, max_nn=30))

    # TODO: Call `o3d.pipelines.registration.registration_icp` with
    # `source_down`, `target_down`, `threshold`, and `trans_init`.
    # 初始化沿用粗配準的 source→target 轉換，不讀取 GT 或重設為單位矩陣。
    trans_init = np.asarray(trans_init, dtype=np.float64)
    if trans_init.shape != (4, 4) or not np.isfinite(trans_init).all():
        raise ValueError("ICP initialization must be a finite 4x4 transform")

    # TODO: Use `TransformationEstimationPointToPlane()` and an explicit
    # convergence criterion.
    # 正式後端固定 Point-to-Plane，明確限制 100 次疊代與相對收斂容差。
    result = o3d.pipelines.registration.registration_icp(
        source_down, target_down, threshold, trans_init,
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
        o3d.pipelines.registration.ICPConvergenceCriteria(
            relative_fitness=1e-6, relative_rmse=1e-6, max_iteration=100))

    # TODO: Return the registration result unchanged so its transformation
    # and metrics remain available to `reconstruct` and diagnostics
    # callbacks.
    # 原樣回傳配準結果，保留真實對應點、內點比例與誤差。
    return result


def my_local_icp_algorithm(source_down, target_down, trans_init, voxel_size):
    """From-scratch point-to-point ICP (the optional Bonus Track backend).

    Each iteration transforms the source by the current estimate, finds
    nearest neighbours in the target via cKDTree, keeps pairs closer than
    `voxel_size * 1.5` (stops below 10 survivors), and solves the optimal
    rigid update with the Kabsch SVD including a reflection fix. Composes
    each delta onto the running transform for up to 60 iterations, stopping
    when the mean inlier error changes by less than 1e-6. Returns a small
    object exposing the final 4x4 as `.transformation`.
    """
    # TODO: Initialize the running transform from `trans_init`.
    # TODO: Transform source points with the current estimate.
    # TODO: Establish nearest-neighbour correspondences against the target.
    # TODO: Reject correspondences outside an appropriate distance threshold
    # and stop safely when too few correspondences remain.
    # TODO: Use target normals to form and solve the point-to-plane
    # linearized pose update. Compose each update into the running 4x4
    # transform. Do not replace this with a call to Open3D's ICP; this is
    # the bonus custom backend selected by `version != "open3d"`.
    # TODO: Stop on convergence or a bounded iteration count.
    # TODO: Return a result-like object exposing the final transform as
    # `.transformation`.
    raise NotImplementedError("TODO: implement my_local_icp_algorithm")


def remove_ceiling_points(point_cloud, margin=1.0):
    """Return the map without the ceiling band, in frame-0 camera coordinates.

    Camera-frame +Y points down, so ceiling returns occupy the map's minimum
    Y values. Drop the same 1 m band that the viewer historically hid. This
    operates only on the merged output map; registration and trajectory scores
    continue to use the original per-frame depth clouds.
    """
    points = np.asarray(point_cloud.points)
    if len(points) == 0:
        return point_cloud
    keep = points[:, 1] > (points[:, 1].min() + float(margin))
    return point_cloud.select_by_index(np.flatnonzero(keep))


# ══════════════════════════════════════════════════════════════════════════════
#  Reconstruction (headless) + metric
# ══════════════════════════════════════════════════════════════════════════════
def _capture_inputs(data_root, frames):
    """讀取本批內參並按數字檔名配對，明確揭露未配對檔案。"""
    import warnings
    with open(os.path.join(data_root, "intrinsics.json"), encoding="utf-8") as fh:
        intrinsics = json.load(fh)
    paired = []
    for name in ("rgb", "depth"):
        indexed = {}
        for entry in os.scandir(os.path.join(data_root, name)):
            if entry.is_file() and entry.name.lower().endswith(".png"):
                stem = int(os.path.splitext(entry.name)[0])
                if stem in indexed:
                    raise ValueError(f"Duplicate numeric frame stem in {name}: {stem}")
                indexed[stem] = entry.path
        paired.append(indexed)
    rgb, depth = paired
    if set(rgb) != set(depth):
        warnings.warn(f"Unpaired RGB/depth stems: {sorted(set(rgb) ^ set(depth))}",
                      RuntimeWarning)
    common = sorted(set(rgb) & set(depth))
    selected = common if frames is None else list(frames)
    if any(isinstance(s, (bool, np.bool_)) or not isinstance(s, (int, np.integer))
           or s not in common for s in selected):
        raise ValueError("Selected frames must be integer stems present in RGB and depth")
    if len(set(selected)) != len(selected):
        raise ValueError("Selected frame stems must be unique")
    scale = intrinsics.get("depth_scale", DEPTH_SCALE)
    if (not np.isscalar(scale) or np.asarray(scale).dtype.kind not in "uif"
            or not np.isfinite(scale) or scale <= 0):
        raise ValueError("depth_scale must be a finite positive divisor")
    return intrinsics, [(rgb[s], depth[s]) for s in selected], float(scale)


def _read_rgbd(rgb_path, depth_path, depth_scale):
    """只在讀檔邊界將 uint16 深度依來源尺度轉成公尺。"""
    import warnings
    rgb = cv2.imread(rgb_path, cv2.IMREAD_COLOR)
    raw = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
    if rgb is None or raw is None:
        warnings.warn(f"Unreadable RGB-D frame: {rgb_path}, {depth_path}", RuntimeWarning)
        return rgb, None
    if raw.dtype != np.uint16 or raw.ndim != 2:
        raise ValueError(f"Expected uint16 depth PNG: {depth_path}; got {raw.dtype}, {raw.shape}")
    return rgb, raw.astype(np.float64) / depth_scale


def reconstruct(data_root, version="open3d", voxel_size=0.05, verbose=True,
                build_cloud=True, frames=None,
                down_voxel=None, registration_seed=0,
                pipeline_callback=None,
                diagnostics_callback=None):
    """Reconstruct a camera trajectory and optionally merge its point clouds.

    Steps for each selected frame: build and preprocess an RGB-D cloud; register
    it to the previous frame with RANSAC initialization and ICP refinement; chain
    the transform and, when requested, add the cloud to the map.

    Frame selection:
      frames=None -> whole batch: every stem present under BOTH rgb/ and
        depth/, ascending numeric order.
      frames=[...] -> only those integer stems, IN THE GIVEN ORDER;
        "consecutive" means consecutive in the subset.

    Returns (global_pcd, pred_cam_pos):
      global_pcd   : every frame's cloud in the FRAME-0 CAMERA frame
                     (+X right, +Y down, +Z forward). Empty when
                     build_cloud=False (trajectory identical either way).
      pred_cam_pos : (N,3) float64 camera centres, frame-0 anchored.
                     GT stays on disk; visualize_and_evaluate loads and
                     subsets it by the same stems when scoring.
    """
    # TODO Stage 1: Load capture-specific intrinsics (`width`, `height`,
    # `hfov`) and select RGB/depth frame pairs in the requested order.
    # `frames=None` uses numeric batch order; an explicit `frames` list
    # keeps its given order.
    # 只讀取本批 RGB-D 與內參；缺 scale 時依既有擷取器的毫米編碼相容處理。
    intrinsics, pairs, depth_scale = _capture_inputs(data_root, frames)
    width, height, hfov = (intrinsics[key] for key in ("width", "height", "hfov"))
    if version != "open3d":
        raise ValueError("M1 reconstruction requires the open3d backend; Bonus is unavailable")
    if pairs and frames is not None:
        _, complete_pairs, _ = _capture_inputs(data_root, None)
        if pairs[0] != complete_pairs[0]:
            raise ValueError("Selected frames must start with the capture's first frame")
    if down_voxel is not None and (not np.isscalar(down_voxel)
            or np.asarray(down_voxel).dtype.kind not in "uif"
            or not np.isfinite(down_voxel) or down_voxel <= 0):
        raise ValueError("down_voxel must be finite and positive")

    T_global = np.eye(4)          # frame i -> frame-0 camera frame
    pred_cam_pos = []
    global_pcd = o3d.geometry.PointCloud()
    prev_down = prev_fpfh = None
    prev_depth_path = None
    prev_stem = None
    prev_pair_index = None
    icp_thr = voxel_size * 1.5

    for i, (rgb_path, depth_path) in enumerate(pairs):
        # TODO Stage 2: Read the RGB-D frame, skip unreadable frames using
        # the existing warning and control-flow behavior, and convert depth
        # to metres.
        # OpenCV 保留深度位元數，僅在這一層除以尺度；反投影接收公尺。
        stem = int(os.path.splitext(os.path.basename(depth_path))[0])
        rgb, depth_m = _read_rgbd(rgb_path, depth_path, depth_scale)
        if i == 0 and (rgb is None or depth_m is None):
            raise ValueError("The reference first RGB-D frame is unreadable")
        if rgb is None or depth_m is None:
            if verbose:
                print(f"  Warning: could not load frame {i}, skipping.")
            continue

        # TODO Stage 3: Convert the frame to a point cloud with
        # `depth_image_to_point_cloud`.
        # 對應本影格的 BGR 色彩與公尺深度，沿用已驗收的手寫反投影。
        pcd = depth_image_to_point_cloud(rgb, depth_m, width, height, hfov)
        # TODO Stage 4: Preprocess it with `preprocess_point_cloud` for
        # voxel downsampling, normals, and FPFH.
        # 沿用已驗收的前處理，保留真實 Voxel 前後點數供回呼取值。
        cur_down, cur_fpfh = preprocess_point_cloud(pcd, voxel_size)
        if pipeline_callback is not None:
            pipeline_callback("frame", {
                "stem": stem,
                "raw_point_count": len(pcd.points),
                "point_yield": len(cur_down.points),
            })

        if prev_down is not None:
            # TODO Stage 6: For every frame after the first processed frame,
            # perform global FPFH feature matching and RANSAC registration
            # to obtain `trans_init`.
            # 當前點雲為 source、上一成功影格為 target；保留粗配準原始統計。
            coarse_result = _global_registration(
                cur_down, prev_down, cur_fpfh, prev_fpfh,
                voxel_size, registration_seed)
            trans_init = coarse_result.transformation
            # TODO Stage 7: Run the selected local backend: Open3D
            # Point-to-Plane ICP for `version == "open3d"`, otherwise the
            # custom ICP backend.
            # Stage 1 已限制正式後端為 Open3D；保留教師原有後端分支。
            if version == 'open3d':
                result_icp = local_icp_algorithm(
                    cur_down, prev_down, trans_init, icp_thr)
            else:   # my_icp
                result_icp = my_local_icp_algorithm(
                    cur_down, prev_down, trans_init, voxel_size)
            # TODO Stage 8: Accumulate the returned transform into the
            # frame-0 coordinate system (`T_global` maps each processed
            # frame into the frame-0 camera coordinate system;
            # registration is always current frame to the previous
            # processed frame).
            # 無內點的零 RMSE 不是成功；失敗時附真實統計中止，不產生假軌跡。
            for label, result in (("RANSAC", coarse_result), ("ICP", result_icp)):
                if (len(result.correspondence_set) == 0
                        or not np.isfinite(result.fitness) or result.fitness <= 0
                        or not np.isfinite(result.inlier_rmse)
                        or not np.isfinite(result.transformation).all()):
                    raise RuntimeError(
                        f"{label} failed for {prev_stem}->{stem}: "
                        f"fitness={result.fitness}, RMSE={result.inlier_rmse}, "
                        f"correspondences={len(result.correspondence_set)}")
            T_global = T_global @ result_icp.transformation
            if pipeline_callback is not None and prev_pair_index == i - 1:
                pipeline_callback("pair", {
                    "prev_stem": prev_stem,
                    "stem": stem,
                    "coarse_fitness": float(coarse_result.fitness),
                    "coarse_rmse": float(coarse_result.inlier_rmse),
                    "coarse_correspondences": len(coarse_result.correspondence_set),
                    "icp_fitness": float(getattr(result_icp, "fitness", float("nan"))),
                    "icp_rmse": float(getattr(result_icp, "inlier_rmse", float("nan"))),
                    "icp_correspondences": len(getattr(result_icp, "correspondence_set", [])),
                })
            if diagnostics_callback is not None and prev_pair_index == i - 1:
                diagnostics_callback({
                    "frame_index": i,
                    "prev_stem": prev_stem,
                    "stem": stem,
                    "raw_point_count": len(pcd.points),
                    "point_yield": len(cur_down.points),
                    "coarse_fitness": float(coarse_result.fitness),
                    "coarse_rmse": float(coarse_result.inlier_rmse),
                    "coarse_correspondences": len(coarse_result.correspondence_set),
                    "icp_fitness": float(result_icp.fitness),
                    "icp_rmse": float(result_icp.inlier_rmse),
                    "icp_correspondences": len(getattr(result_icp, "correspondence_set", [])),
                    "trans_init": trans_init,
                    "icp_transformation": result_icp.transformation,
                })

        # TODO Stage 10: Append the current camera position to
        # `pred_cam_pos` (one entry per successfully processed frame).
        # 累積轉換的平移即相機中心；每個成功處理影格記錄一次。
        pred_cam_pos.append(T_global[:3, 3].copy())

        if build_cloud:
            # TODO Stage 11: If `build_cloud` is enabled, optionally
            # downsample only the merged map, transform the current cloud
            # by the accumulated transform, and add it to `global_pcd`.
            # This must not alter trajectory estimation.
            # 地圖使用獨立副本，僅降低地圖點數，避免修改配準輸入。
            map_cloud = (pcd.voxel_down_sample(down_voxel) if down_voxel is not None
                         else pcd.select_by_index(range(len(pcd.points))))
            global_pcd += map_cloud.transform(T_global)

        # TODO Stage 12: Update previous-frame state and preserve progress
        # reporting.
        # 上一影格僅在本影格完成後更新，沿用原有進度與回呼配對規則。
        prev_down, prev_fpfh = cur_down, cur_fpfh
        prev_depth_path = depth_path
        prev_stem = stem
        prev_pair_index = i

        if verbose and (i % 25 == 0 or i == len(pairs) - 1):
            print(f"  frame {i:>4d}/{len(pairs)-1}")

    if not pred_cam_pos:
        return o3d.geometry.PointCloud(), np.zeros((0, 3))
    if build_cloud:
        global_pcd = remove_ceiling_points(global_pcd)
    return global_pcd, np.array(pred_cam_pos, dtype=np.float64)


# ══════════════════════════════════════════════════════════════════════════════
#  Evaluation + visualisation (used by the thin reconstruct.py CLI)
# ══════════════════════════════════════════════════════════════════════════════
def visualize_and_evaluate(reconstructed_pcd, predicted_cam_poses, data_root,
                           frames=None, title="reconstruction", show=True,
                           save_path=None):
    """Score the trajectory and visualise map + trajectories.

    GT is loaded here from data_root/GT_pose.npy as (M,7)
    [x,y,z,qw,qx,qy,qz], or None when absent. GT rows are in capture order
    while image stems are identifiers, so when `frames` is given each stem
    is mapped to its ordinal in the sorted common RGB/depth frame list
    before indexing (stems absent from the capture or beyond GT are skipped,
    requested order preserved) — the score stays meaningful on subsets.

    1. Mean L2 over camera centres: reconcile frames first (pred is frame-0
       camera on image axes → flip Y and Z; GT world poses → R0^T (t_i - t_0)
       via pose 0), then mean over i of ||pred[i] - gt[i]||_2 with
       L2 = sqrt(dx^2 + dy^2 + dz^2). No scale/rotation/offset fitting TO the
       GT. inf when either side is missing/empty. Prints it and returns it.
    2. Estimated trajectory LineSet (red), GT trajectory LineSet (black).
    3. Open3D window with the ceiling-cropped map plus both trajectories
       (skipped when show=False, e.g. headless scoring). Ceiling points have
       already been removed from the merged map by `reconstruct`.
    """
    # TODO: Load `GT_pose.npy` when present and map requested `frames` to
    # the correct ground-truth rows while preserving requested order.
    # GT 僅在評估階段載入；影格編號對應共同檔名的排序位置，而非 stem-1。
    gt = None
    gt_path = os.path.join(data_root, "GT_pose.npy") if data_root is not None else None
    if gt_path is not None and os.path.isfile(gt_path):
        gt = np.asarray(np.load(gt_path), dtype=np.float64)
        if gt.ndim != 2 or gt.shape[1] != 7 or not np.isfinite(gt).all():
            raise ValueError("GT_pose.npy must contain finite (N,7) poses")
    prediction = (np.empty((0, 3)) if predicted_cam_poses is None
                  else np.asarray(predicted_cam_poses, dtype=np.float64))
    if prediction.size == 0:
        prediction = np.empty((0, 3))
    if prediction.ndim != 2 or prediction.shape[1] != 3 or not np.isfinite(prediction).all():
        raise ValueError("Predicted camera centres must be finite (N,3) positions")
    selection = None if frames is None else list(frames)
    rows = []
    if gt is not None and len(gt):
        if selection is None:
            rows = [(i, i) for i in range(min(len(prediction), len(gt)))]
        else:
            stems_by_kind = []
            for kind in ("rgb", "depth"):
                stems_by_kind.append({int(os.path.splitext(name)[0])
                    for name in os.listdir(os.path.join(data_root, kind))
                    if name.lower().endswith(".png")})
            ordered = sorted(stems_by_kind[0] & stems_by_kind[1])
            if selection and (not ordered or selection[0] != ordered[0]):
                raise ValueError("Selected frames must start with the capture's first frame")
            ordinal = {stem: i for i, stem in enumerate(ordered)}
            rows = [(i, ordinal[stem]) for i, stem in enumerate(selection)
                    if stem in ordinal and ordinal[stem] < len(gt)]

    # TODO: Handle missing or empty ground truth and empty predictions
    # without raising; return an infinite mean error when no score can be
    # computed.
    # 缺資料或預測數量不符時不猜影格身分，回傳無法評分的無限誤差。
    expected_count = len(selection) if selection is not None else (0 if gt is None else len(gt))
    if len(prediction) != expected_count:
        rows = []
    n = len(rows)
    mean_l2_error = float("inf")

    # TODO: Reconcile predicted and ground-truth coordinate conventions
    # using the existing camera-axis and frame-0 alignment conventions.
    # 固定翻轉 Y/Z；GT 使用原始首姿態，不以最佳擬合重新對齊軌跡。
    pred_disp = prediction @ CAM_TO_GT_AXES
    gt_disp = np.empty((0, 3))
    if gt is not None and len(gt):
        qw, qx, qy, qz = gt[0, 3:7]
        rotation0 = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
        gt_disp = (gt[:, :3] - gt[0, :3]) @ rotation0

    # TODO: Compute mean camera-centre L2 distance:
    #   dx = predicted_x - gt_x
    #   dy = predicted_y - gt_y
    #   dz = predicted_z - gt_z
    #   L2 = sqrt(dx**2 + dy**2 + dz**2)
    #   mean_l2 = mean(L2)
    # 只對已確認一一對應的相機中心計算平均歐氏距離。
    if n:
        predicted_rows, gt_rows = np.asarray(rows).T
        mean_l2_error = float(np.linalg.norm(
            pred_disp[predicted_rows] - gt_disp[gt_rows], axis=1).mean())
    print(f"Mean L2 distance: {mean_l2_error:.6f} meters  (over {n} frames, "
          f"{0 if predicted_cam_poses is None else len(predicted_cam_poses)} "
          f"reconstructed)")
    if save_path is not None:
        save_reconstruction_image(
            reconstructed_pcd, predicted_cam_poses, data_root,
            save_path, frames=frames, title=title)
    if not show:
        return mean_l2_error
    # TODO: Create a `LineSet` for the estimated trajectory colored red.
    # 預測軌跡先轉為 Habitat 首相機軸向，使用紅線連接相機中心。
    geoms = []
    if len(pred_disp) > 1:
        estimated = o3d.geometry.LineSet()
        estimated.points = o3d.utility.Vector3dVector(pred_disp)
        estimated.lines = o3d.utility.Vector2iVector(
            [[i, i + 1] for i in range(len(pred_disp) - 1)])
        estimated.paint_uniform_color([1, 0, 0])
        geoms.append(estimated)

    # TODO: Create a `LineSet` for the ground-truth trajectory colored black.
    # GT 顯示相同評估子集，避免把未使用影格誤畫成比較樣本。
    display_rows = [row for _, row in rows]
    if len(display_rows) > 1:
        truth = o3d.geometry.LineSet()
        truth.points = o3d.utility.Vector3dVector(gt_disp[display_rows])
        truth.lines = o3d.utility.Vector2iVector(
            [[i, i + 1] for i in range(len(display_rows) - 1)])
        truth.paint_uniform_color([0, 0, 0])
        geoms.append(truth)

    # TODO: Add the available map and trajectories to the Open3D
    # visualization when `show=True`; keep headless scoring functional when
    # `show=False`.
    # 地圖副本套用同一固定軸向轉換，不修改原重建結果；無幾何時不開視窗。
    if reconstructed_pcd is not None and len(reconstructed_pcd.points):
        axes = np.eye(4)
        axes[:3, :3] = CAM_TO_GT_AXES
        geoms.insert(0, o3d.geometry.PointCloud(reconstructed_pcd).transform(axes))
    if not geoms:
        return mean_l2_error
    print(f"[visualize] opening visualiser for {title} …  (press Q to close)")
    o3d.visualization.draw_geometries(
        geoms, window_name=f'HW1 Reconstruction - {title}',
        zoom=0.5, front=[0, -1, 0], lookat=[0, 0, 0], up=[0, 0, 1])
    return mean_l2_error

def save_reconstruction_image(reconstructed_pcd, predicted_cam_poses, data_root,
                              save_path, frames=None, title="reconstruction"):
    """Render reconstructed point cloud and camera trajectories to a PNG file."""
    if save_path is None:
        return None
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)

    gt_poses = None
    if data_root is not None:
        gt_path = os.path.join(data_root, 'GT_pose.npy')
        if os.path.exists(gt_path):
            gt = np.load(gt_path)
            if frames is None:
                gt_poses = gt
            else:
                rgb_dir = os.path.join(data_root, 'rgb')
                if os.path.exists(rgb_dir):
                    ordered_stems = sorted(
                        int(os.path.splitext(f)[0])
                        for f in os.listdir(rgb_dir)
                        if f.endswith('.png'))
                    rows = [ordered_stems.index(int(stem)) for stem in frames
                            if int(stem) in ordered_stems
                            and ordered_stems.index(int(stem)) < len(gt)]
                    gt_poses = gt[rows]
                else:
                    gt_poses = gt[:len(frames)]

    pred_disp = None
    gt_disp = None
    if predicted_cam_poses is not None and len(predicted_cam_poses) > 0:
        pred_disp = np.asarray(predicted_cam_poses, dtype=np.float64) @ CAM_TO_GT_AXES
    if gt_poses is not None and len(gt_poses) > 0:
        gt = np.asarray(gt_poses, dtype=np.float64)
        t = gt[:, :3]
        qw, qx, qy, qz = gt[0, 3:7]
        R0 = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
        gt_disp = (t - t[0]) @ R0

    geoms = []
    if reconstructed_pcd is not None and len(reconstructed_pcd.points) > 0:
        scene_no_ceil = o3d.geometry.PointCloud()
        scene_no_ceil.points = o3d.utility.Vector3dVector(np.asarray(reconstructed_pcd.points).copy())
        if reconstructed_pcd.has_colors():
            scene_no_ceil.colors = o3d.utility.Vector3dVector(
                np.asarray(reconstructed_pcd.colors).copy())
        to_gt_axes = np.eye(4)
        to_gt_axes[:3, :3] = CAM_TO_GT_AXES
        scene_no_ceil.transform(to_gt_axes)
        geoms.append(scene_no_ceil)

    if pred_disp is not None and gt_disp is not None:
        n_min = min(len(pred_disp), len(gt_disp))
        if n_min > 1:
            for traj, color in ((pred_disp[:n_min], [1.0, 0.0, 0.0]),
                                (gt_disp[:n_min], [0.0, 0.0, 0.0])):
                edges = [[i, i + 1] for i in range(len(traj) - 1)]
                lineset = o3d.geometry.LineSet()
                lineset.points = o3d.utility.Vector3dVector(np.asarray(traj))
                lineset.lines = o3d.utility.Vector2iVector(edges)
                lineset.colors = o3d.utility.Vector3dVector([color] * len(edges))
                geoms.append(lineset)
    elif pred_disp is not None and len(pred_disp) > 1:
        edges = [[i, i + 1] for i in range(len(pred_disp) - 1)]
        lineset = o3d.geometry.LineSet()
        lineset.points = o3d.utility.Vector3dVector(np.asarray(pred_disp))
        lineset.lines = o3d.utility.Vector2iVector(edges)
        lineset.colors = o3d.utility.Vector3dVector([[1.0, 0.0, 0.0]] * len(edges))
        geoms.append(lineset)

    if not os.environ.get("DISPLAY"):
        if os.path.exists("/tmp/.X11-unix/X1"):
            os.environ["DISPLAY"] = ":1"
        elif os.path.exists("/tmp/.X11-unix/X0"):
            os.environ["DISPLAY"] = ":0"

    rendered = False
    if geoms and os.environ.get("DISPLAY"):
        try:
            vis = o3d.visualization.Visualizer()
            if vis.create_window(visible=False, width=1920, height=1080):
                for g in geoms:
                    vis.add_geometry(g)
                opt = vis.get_render_option()
                if opt is not None:
                    opt.background_color = np.asarray([1.0, 1.0, 1.0])
                    if hasattr(opt, "line_width"):
                        opt.line_width = 3.0
                ctr = vis.get_view_control()
                if ctr is not None:
                    ctr.set_zoom(0.5)
                    ctr.set_front([0, -1, 0])
                    ctr.set_lookat([0, 0, 0])
                    ctr.set_up([0, 0, 1])
                vis.poll_events()
                vis.update_renderer()
                vis.capture_screen_image(save_path, do_render=True)
                vis.destroy_window()
                rendered = os.path.isfile(save_path) and os.path.getsize(save_path) > 0
        except Exception:
            rendered = False

    if not rendered:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection="3d")
            if reconstructed_pcd is not None and len(reconstructed_pcd.points) > 0:
                pts = np.asarray(reconstructed_pcd.points)
                if len(pts) > 5000:
                    pts = pts[::len(pts) // 5000]
                pts_gt = pts @ CAM_TO_GT_AXES
                ax.scatter(pts_gt[:, 0], pts_gt[:, 1], pts_gt[:, 2], s=0.5, c="gray", alpha=0.3)
            if pred_disp is not None and len(pred_disp) > 0:
                ax.plot(pred_disp[:, 0], pred_disp[:, 1], pred_disp[:, 2], "r-", label="Predicted")
            if gt_disp is not None and len(gt_disp) > 0:
                ax.plot(gt_disp[:, 0], gt_disp[:, 1], gt_disp[:, 2], "k-", label="Ground Truth")
            ax.set_title(title)
            ax.legend()
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            rendered = os.path.isfile(save_path) and os.path.getsize(save_path) > 0
        except Exception as exc:
            print(f"[reconstruct] warning: failed to save reconstruction image {save_path}: {exc}")
    return save_path if rendered else None
