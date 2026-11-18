"""C 級授權範圍：僅測試地圖資源參數的解析、傳遞與演算法不變性。"""
import sys
import numpy as np
import pytest
import api
import reconstruct as cli
import utils
from test_reconstruction import rgbd_capture


@pytest.mark.parametrize('route', ['unsealed', 'sealed_baseline', 'selected'])
@pytest.mark.parametrize('value', [None, 0.05])
def test_cli_forwards_map_voxel_without_changing_registration(monkeypatch, route, value):
    argv = ['reconstruct.py', '--experiment', 'unused.ttl', '--no-vis']
    if value is not None:
        argv += ['--down-voxel', str(value)]
    if route == 'selected':
        argv += ['--selection-query', 'unused.rq']
    monkeypatch.setattr(sys, 'argv', argv)
    monkeypatch.setattr(api, 'is_assessed', lambda _: route != 'unsealed')
    monkeypatch.setattr(api, 'read_declaration', lambda _: {'batch_path': 'capture', 'required': {'icpBackend': 'open3d'}})
    monkeypatch.setattr(api, '_pair_frames', lambda _: [('1', 'r1', 'd1'), ('2', 'r2', 'd2')])
    monkeypatch.setattr(api, 'read_experiment', lambda _: {
        'batch_path': 'capture', 'exp_name': 'test', 'batch_name': 'floor1_test',
        'frame_indices': [1, 2, 3], 'factor_counts': {}, 'settings': {'icpBackend': 'open3d'}})
    monkeypatch.setattr(cli, '_plan_query_selected', lambda *args: ([1, 3], [[1], [3]]))
    captured = {}
    class ReachedPipeline(Exception):
        pass
    def capture(*args, **kwargs):
        captured.update(args=args, kwargs=kwargs)
        raise ReachedPipeline
    monkeypatch.setattr(utils, 'reconstruct', capture)
    with pytest.raises(ReachedPipeline):
        cli.main()
    assert captured['args'] == ('capture', 'open3d')
    kwargs = captured['kwargs']
    assert kwargs['down_voxel'] == value
    assert kwargs['voxel_size'] == 0.05 and kwargs['registration_seed'] == 0
    assert kwargs['build_cloud'] is True
    assert kwargs['frames'] == ([1, 2] if route == 'unsealed' else [1, 3] if route == 'selected' else None)
    assert ('pipeline_callback' in kwargs) == (route == 'unsealed')


@pytest.mark.parametrize('value', ['0', '-0.1', 'nan', 'inf', '-inf', 'abc'])
def test_cli_rejects_invalid_map_voxel_before_experiment_access(monkeypatch, value):
    monkeypatch.setattr(sys, 'argv', ['reconstruct.py', '--experiment', 'unused.ttl', f'--down-voxel={value}'])
    monkeypatch.setattr(api, 'is_assessed', lambda _: pytest.fail('invalid CLI reached experiment'))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2


def test_real_map_downsampling_keeps_poses_factors_and_mean_l2(rgbd_capture):
    results = []
    np.save(rgbd_capture / 'GT_pose.npy', np.tile([1, 2, 3, 1, 0, 0, 0], (3, 1)))
    for down_voxel in [None, 0.05]:
        callback, frame, pair = api.make_pipeline_measurement_callback(api.load_quality_factors())
        pcd, positions = utils.reconstruct(rgbd_capture, voxel_size=0.05, registration_seed=0,
                                          down_voxel=down_voxel, verbose=False, pipeline_callback=callback)
        l2 = utils.visualize_and_evaluate(pcd, positions, rgbd_capture, show=False)
        results.append((pcd, positions, frame, pair, l2))
    original, reduced = results
    np.testing.assert_allclose(original[1], reduced[1], atol=1e-12, rtol=0)
    assert original[2] == reduced[2] and original[3] == reduced[3]
    assert original[4] == pytest.approx(reduced[4], abs=1e-12)
    assert len(reduced[0].points) <= len(original[0].points)
