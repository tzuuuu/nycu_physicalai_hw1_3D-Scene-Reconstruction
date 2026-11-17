"""M1.2：以合成幾何與真實 Open3D 驗證點雲前處理。"""

# 先載入專案入口，沿用其 OpenMP 設定，再匯入原生數值套件。
from utils import preprocess_point_cloud

import numpy as np
import open3d as o3d
import pytest


def cloud(points):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.asarray(points).reshape(-1, 3))
    return pcd


@pytest.fixture
def plane():
    # 密集且非共線的平面，提供足夠鄰點以檢查法向量方向。
    x, y = np.meshgrid(np.linspace(0, 1, 21), np.linspace(0, 1, 21))
    return cloud(np.column_stack((x.ravel(), y.ravel(), np.zeros(x.size))))


def test_voxel_merges_points_at_expected_centroids():
    pcd = cloud([[0, 0, 0], [0.02, 0, 0], [1, 0, 0], [1.02, 0, 0],
                 [0, 1, 0], [0.02, 1, 0]])
    down, _ = preprocess_point_cloud(pcd, 0.1)
    # Open3D 不保證體素輸出順序，因此比較排序後的幾何集合。
    np.testing.assert_allclose(sorted(map(tuple, np.asarray(down.points))),
                               [[0.01, 0, 0], [0.01, 1, 0], [1.01, 0, 0]])


def test_plane_normals_and_feature_dimensions(plane):
    original = np.asarray(plane.points).copy()
    down, fpfh = preprocess_point_cloud(plane, 0.1)
    assert 3 <= len(down.points) < len(plane.points)
    assert down.has_normals()
    normals = np.asarray(down.normals)
    assert np.isfinite(normals).all()
    np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1, atol=1e-12)
    np.testing.assert_allclose(np.abs(normals[:, 2]), 1, atol=1e-12)
    assert isinstance(fpfh, o3d.pipelines.registration.Feature)
    assert fpfh.data.shape == (33, len(down.points))
    assert np.isfinite(fpfh.data).all()
    assert np.any(fpfh.data > 0)
    np.testing.assert_array_equal(np.asarray(plane.points), original)
    assert not plane.has_normals()


@pytest.mark.parametrize('voxel_size', [0.05, 0.1, 0.2])
def test_search_parameters_reach_real_open3d(plane, voxel_size, monkeypatch):
    # 僅記錄參數並轉呼叫真實實作，不替換法向量或特徵結果。
    normal_calls, feature_calls = [], []
    point_type = o3d.geometry.PointCloud
    real_normals = point_type.estimate_normals
    registration = o3d.pipelines.registration
    real_features = registration.compute_fpfh_feature

    def record_normals(self, search_param):
        normal_calls.append((search_param.radius, search_param.max_nn,
                             isinstance(search_param, o3d.geometry.KDTreeSearchParamHybrid)))
        return real_normals(self, search_param)

    def record_features(pcd, search_param):
        feature_calls.append((search_param.radius, search_param.max_nn,
                              isinstance(search_param, o3d.geometry.KDTreeSearchParamHybrid)))
        return real_features(pcd, search_param)

    monkeypatch.setattr(point_type, 'estimate_normals', record_normals)
    monkeypatch.setattr(registration, 'compute_fpfh_feature', record_features)
    down, fpfh = preprocess_point_cloud(plane, voxel_size)
    assert normal_calls == [(voxel_size * 2, 30, True)]
    assert feature_calls == [(voxel_size * 5, 100, True)]
    assert fpfh.data.shape == (33, len(down.points))


def test_larger_voxels_reduce_dense_plane_more(plane):
    counts = [len(preprocess_point_cloud(plane, size)[0].points)
              for size in [0.05, 0.1, 0.2]]
    assert counts[0] > counts[1] > counts[2] >= 3


@pytest.mark.parametrize('points', [[], [[0, 0, 0]], [[0, 0, 0], [1, 0, 0]]])
def test_rejects_empty_or_too_few_points(points):
    with pytest.raises(ValueError, match='empty|At least 3'):
        preprocess_point_cloud(cloud(points), 0.1)


def test_rejects_cloud_collapsed_to_one_voxel():
    with pytest.raises(ValueError, match='At least 3'):
        preprocess_point_cloud(cloud([[0, 0, 0], [0.001, 0, 0], [0, 0.001, 0]]), 0.1)


def test_three_nearby_noncollinear_points_use_real_geometry():
    down, fpfh = preprocess_point_cloud(cloud([[0, 0, 0], [0.1, 0, 0], [0, 0.1, 0]]), 0.1)
    assert len(down.points) == 3
    np.testing.assert_allclose(np.abs(np.asarray(down.normals)[:, 2]), 1)
    assert fpfh.data.shape == (33, 3)
    assert np.isfinite(fpfh.data).all()


@pytest.mark.parametrize('size', [0, -0.1, np.nan, np.inf, -np.inf, 1e308,
                                '0.1', True, [0.1], 0.1 + 0j])
def test_rejects_invalid_voxel_size(plane, size):
    with pytest.raises(ValueError, match='voxel_size'):
        preprocess_point_cloud(plane, size)


@pytest.mark.parametrize('value', [np.nan, np.inf, -np.inf])
def test_rejects_nonfinite_points(value):
    with pytest.raises(ValueError, match='finite points'):
        preprocess_point_cloud(cloud([[0, 0, 0], [1, 0, 0], [value, 1, 0]]), 0.1)
