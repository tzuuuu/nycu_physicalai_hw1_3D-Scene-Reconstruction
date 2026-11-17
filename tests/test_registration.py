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
