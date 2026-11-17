"""使用實際 Open3D 配準已知旋轉與平移的合成幾何。"""
import copy
import numpy as np
import open3d as o3d
import pytest
from scipy.spatial.transform import Rotation
import utils


@pytest.fixture
def geometry():
    rng = np.random.default_rng(1729)
    points = rng.normal(size=(500, 3))
    points /= np.linalg.norm(points, axis=1, keepdims=True)
    points *= [1, 0.7, 0.4]
    target = o3d.geometry.PointCloud()
    target.points = o3d.utility.Vector3dVector(points)
    target.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.25, max_nn=30))
    transform = np.eye(4)
    transform[:3, :3] = Rotation.from_euler('xyz', [17, -23, 31], degrees=True).as_matrix()
    transform[:3, 3] = [0.3, -0.2, 0.15]
    source = copy.deepcopy(target).transform(np.linalg.inv(transform))
    return source, target, transform


def test_ransac_recovers_source_to_target(geometry):
    source, target, expected = geometry
    param = o3d.geometry.KDTreeSearchParamHybrid(radius=0.5, max_nn=100)
    source_f = o3d.pipelines.registration.compute_fpfh_feature(source, param)
    target_f = o3d.pipelines.registration.compute_fpfh_feature(target, param)
    result = utils._global_registration(source, target, source_f, target_f, 0.05, 7)
    assert isinstance(result, o3d.pipelines.registration.RegistrationResult)
    np.testing.assert_allclose(result.transformation, expected, atol=1e-8)
    assert result.fitness == pytest.approx(1)
    assert result.inlier_rmse < 1e-8
    assert len(result.correspondence_set) == len(source.points)
    repeated = utils._global_registration(source, target, source_f, target_f, 0.05, 7)
    np.testing.assert_allclose(repeated.transformation, result.transformation, atol=1e-8)


def test_point_to_plane_recovers_refined_pose_and_preserves_result(geometry, monkeypatch):
    source, target, expected = geometry
    initial = expected.copy()
    initial[:3, 3] += [0.015, -0.012, 0.01]
    initial[:3, :3] = Rotation.from_euler('x', 1, degrees=True).as_matrix() @ initial[:3, :3]
    reg = o3d.pipelines.registration
    real = reg.registration_icp
    captured = {}

    def record(*args):
        captured['args'] = args
        captured['result'] = real(*args)
        return captured['result']

    monkeypatch.setattr(reg, 'registration_icp', record)
    result = utils.local_icp_algorithm(source, target, initial, 0.15)
    assert result is captured['result']
    assert captured['args'][0] is source and captured['args'][1] is target
    np.testing.assert_array_equal(captured['args'][3], initial)
    assert isinstance(captured['args'][4], reg.TransformationEstimationPointToPlane)
    assert captured['args'][5].max_iteration == 100
    np.testing.assert_allclose(result.transformation, expected, atol=1e-6)
    assert result.fitness == pytest.approx(1)
    assert result.inlier_rmse < 1e-6
    assert len(result.correspondence_set) == 500


def test_icp_estimates_only_missing_normals(geometry, monkeypatch):
    source, target, expected = geometry
    source.normals = o3d.utility.Vector3dVector(np.empty((0, 3)))
    real = o3d.geometry.PointCloud.estimate_normals
    calls = []

    def record(self, param):
        calls.append((self is source, param.radius, param.max_nn))
        return real(self, param)

    monkeypatch.setattr(o3d.geometry.PointCloud, 'estimate_normals', record)
    result = utils.local_icp_algorithm(source, target, expected, 0.15)
    assert calls == [(True, 0.3, 30)]
    np.testing.assert_allclose(result.transformation, expected, atol=1e-8)


def test_icp_empty_correspondences_remain_actual_failure(geometry):
    source, target, _ = geometry
    source.translate([100, 100, 100])
    result = utils.local_icp_algorithm(source, target, np.eye(4), 0.05)
    assert result.fitness == 0
    assert len(result.correspondence_set) == 0
    # Open3D 此時 RMSE 為零；不可將此情況解讀為完美對齊。


@pytest.mark.parametrize('threshold', [0, -1, np.nan, np.inf, '0.1'])
def test_icp_invalid_threshold(geometry, threshold):
    source, target, initial = geometry
    with pytest.raises(ValueError, match='threshold'):
        utils.local_icp_algorithm(source, target, initial, threshold)
