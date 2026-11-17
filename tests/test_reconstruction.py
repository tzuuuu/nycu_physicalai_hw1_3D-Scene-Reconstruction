"""合成 RGB-D 的流程整合與受控剛體組合測試。"""
import json
import cv2
import numpy as np
import open3d as o3d
import pytest
from scipy.spatial.transform import Rotation
import api
import utils


@pytest.fixture
def rgbd_capture(tmp_path):
    for kind in ['rgb', 'depth']:
        (tmp_path / kind).mkdir()
    (tmp_path / 'intrinsics.json').write_text(json.dumps({'width': 48, 'height': 40, 'hfov': 75}))
    v, u = np.indices((40, 48))
    # 不規則彎曲表面避免平面配準完全退化；三幀相同，真實預期為單位轉換。
    depth = (2000 + 400 * np.sin(u / 5) + 250 * np.cos(v / 4) + 2 * u * v).astype(np.uint16)
    rgb = np.stack((u * 4, v * 5, (u + v) * 2), axis=-1).astype(np.uint8)
    for stem in [3, 20, 101]:
        cv2.imwrite(str(tmp_path / 'rgb' / f'{stem}.png'), rgb)
        cv2.imwrite(str(tmp_path / 'depth' / f'{stem}.png'), depth)
    return tmp_path


def test_real_pipeline_callbacks_and_map_switch(rgbd_capture, monkeypatch):
    callback, frame_records, pair_records = api.make_pipeline_measurement_callback(api.load_quality_factors())
    diagnostics, actual = [], []
    real_ransac, real_icp = utils._global_registration, utils.local_icp_algorithm

    def ransac(*args):
        result = real_ransac(*args)
        actual.append(['ransac', result])
        return result

    def icp(*args):
        result = real_icp(*args)
        actual.append(['icp', result])
        return result

    monkeypatch.setattr(utils, '_global_registration', ransac)
    monkeypatch.setattr(utils, 'local_icp_algorithm', icp)
    pcd, positions = utils.reconstruct(rgbd_capture, voxel_size=0.08, verbose=False,
                                      pipeline_callback=callback, diagnostics_callback=diagnostics.append)
    assert len(pcd.points) > 0
    np.testing.assert_allclose(positions, np.zeros((3, 3)), atol=1e-8)
    assert len(frame_records) == 6 and len(pair_records) == 12
    assert all(r['value'] == 1920 for (name, _), r in frame_records.items() if name == 'RawPointCount')
    for index, (left, right) in enumerate([(3, 20), (20, 101)]):
        for prefix, result in actual[2 * index:2 * index + 2]:
            names = (['CoarseRANSACFitness', 'CoarseRANSACRMSE', 'CoarseRANSACCorrespondences']
                     if prefix == 'ransac' else ['ICPInlierFitness', 'ICPInlierRMSE', 'ICPInlierCorrespondences'])
            for name, value in zip(names, [result.fitness, result.inlier_rmse, len(result.correspondence_set)]):
                assert pair_records[(name, left, right)]['value'] == value
        np.testing.assert_array_equal(diagnostics[index]['icp_transformation'], actual[2 * index + 1][1].transformation)
    # 放入不可讀 GT，重建仍應完全不碰它。
    (rgbd_capture / 'GT_pose.npy').write_bytes(b'GT must not be read')
    empty, no_map_positions = utils.reconstruct(rgbd_capture, voxel_size=0.08, verbose=False, build_cloud=False)
    assert len(empty.points) == 0
    np.testing.assert_allclose(no_map_positions, positions, atol=1e-8)
    _, reduced_positions = utils.reconstruct(rgbd_capture, voxel_size=0.08, verbose=False, down_voxel=0.2)
    np.testing.assert_allclose(reduced_positions, positions, atol=1e-8)


def test_rotation_translation_compose_current_to_previous(rgbd_capture, monkeypatch):
    # 僅此案例使用明確標記的受控配準結果，隔離矩陣組合方向；非正式量測。
    transforms = []
    for angles, translation in [([0, 0, 90], [1, 2, 0]), ([20, 0, 0], [2, 0, 1])]:
        transform = np.eye(4)
        transform[:3, :3] = Rotation.from_euler('xyz', angles, degrees=True).as_matrix()
        transform[:3, 3] = translation
        transforms.append(transform)
    original_clouds = []
    real_unproject = utils.depth_image_to_point_cloud

    def unproject(*args):
        result = real_unproject(*args)
        original_clouds.append(np.asarray(result.points).copy())
        return result

    def controlled(source, target, sf, tf, size, seed):
        transform = transforms[len(original_clouds) - 2]
        # 以 Open3D 真實評估結果承載指定轉換；此處不驗證配準精確度。
        moved = o3d.geometry.PointCloud(source).transform(transform)
        return o3d.pipelines.registration.evaluate_registration(source, moved, 0.01, transform)

    monkeypatch.setattr(utils, 'depth_image_to_point_cloud', unproject)
    monkeypatch.setattr(utils, '_global_registration', controlled)
    monkeypatch.setattr(utils, 'local_icp_algorithm', lambda s, t, initial, threshold:
                        o3d.pipelines.registration.evaluate_registration(s, o3d.geometry.PointCloud(s).transform(initial), 0.01, initial))
    # 不裁天花板，讓本測試能逐一核對地圖的完整剛體轉換。
    monkeypatch.setattr(utils, 'remove_ceiling_points', lambda p: p)
    pcd, positions = utils.reconstruct(rgbd_capture, voxel_size=0.08, verbose=False)
    cumulative = [np.eye(4), transforms[0], transforms[0] @ transforms[1]]
    np.testing.assert_allclose(positions, [t[:3, 3] for t in cumulative], atol=1e-12)
    expected = np.vstack([p @ t[:3, :3].T + t[:3, 3] for p, t in zip(original_clouds, cumulative)])
    np.testing.assert_allclose(np.asarray(pcd.points), expected, atol=1e-12)


@pytest.mark.parametrize('frames', [[20, 101], [20, 3]])
def test_selected_must_keep_capture_reference(rgbd_capture, frames):
    with pytest.raises(ValueError, match='first frame'):
        utils.reconstruct(rgbd_capture, frames=frames, verbose=False)


def test_nonconsecutive_selection_and_bonus_guard(rgbd_capture):
    _, positions = utils.reconstruct(rgbd_capture, frames=[3, 101], voxel_size=0.08, verbose=False, build_cloud=False)
    assert positions.shape == (2, 3)
    with pytest.raises(ValueError, match='Bonus'):
        utils.reconstruct(rgbd_capture, version='my_icp')


def test_unreadable_frame_cannot_yield_complete_factors(rgbd_capture):
    (rgbd_capture / 'depth' / '20.png').write_bytes(b'corrupt')
    callback, frames, pairs = api.make_pipeline_measurement_callback(api.load_quality_factors())
    with pytest.warns(RuntimeWarning, match='Unreadable'):
        _, positions = utils.reconstruct(rgbd_capture, voxel_size=0.08, verbose=False,
                                         pipeline_callback=callback, build_cloud=False)
    assert len(positions) == 2
    assert len(frames) == 4 and len(pairs) == 0  # 既有 CLI 完整性檢查會拒絕封存。


def test_registration_failure_is_explicit(rgbd_capture, monkeypatch):
    monkeypatch.setattr(utils, '_global_registration', lambda *args: o3d.pipelines.registration.RegistrationResult())
    monkeypatch.setattr(utils, 'local_icp_algorithm', lambda *args: o3d.pipelines.registration.RegistrationResult())
    with pytest.raises(RuntimeError, match='RANSAC failed.*fitness=0.0.*correspondences=0'):
        utils.reconstruct(rgbd_capture, voxel_size=0.08, verbose=False)
