"""只使用暫存合成資料驗證 M1，不宣告實驗、不封存 Turtle。"""
import json
import cv2
import numpy as np
import pytest
import api
import utils


def test_synthetic_rgbd_to_factors_and_mean_l2(tmp_path):
    for kind in ['rgb', 'depth']:
        (tmp_path / kind).mkdir()
    (tmp_path / 'intrinsics.json').write_text(json.dumps({'width': 40, 'height': 32, 'hfov': 70}))
    v, u = np.indices((32, 40))
    raw = (3000 + 500 * np.sin(u / 4) + 300 * np.cos(v / 3) + u * v).astype(np.uint16)
    for stem in [7, 42, 108]:
        cv2.imwrite(str(tmp_path / 'depth' / f'{stem}.png'), raw)
        cv2.imwrite(str(tmp_path / 'rgb' / f'{stem}.png'), np.full((32, 40, 3), [17, 83, 201], np.uint8))
    # 同一位置與方向的三張影像，GT 首姿態仍有非零位置與旋轉。
    np.save(tmp_path / 'GT_pose.npy', np.tile([4, 7, -2, np.sqrt(0.5), 0, np.sqrt(0.5), 0], (3, 1)))
    callback, frame, pair = api.make_pipeline_measurement_callback(api.load_quality_factors())
    diagnostics = []
    pcd, predicted = utils.reconstruct(tmp_path, voxel_size=0.1, verbose=False,
                                       pipeline_callback=callback, diagnostics_callback=diagnostics.append)
    assert len(frame) + len(pair) == 8 * 3 - 6 == 18
    assert len(diagnostics) == 2
    assert len(pcd.points) > 0
    assert np.isfinite([r['value'] for r in [*frame.values(), *pair.values()]]).all()
    assert utils.visualize_and_evaluate(pcd, predicted, tmp_path, show=False) == pytest.approx(0, abs=1e-8)
    output = tmp_path / 'proof.png'
    assert utils.visualize_and_evaluate(pcd, predicted, tmp_path, show=False, save_path=output) == pytest.approx(0, abs=1e-8)
    assert output.stat().st_size > 0
    # 以既有實際 callback 形成 18 筆因素，不產生任何 TTL／正式 run。
    assert not list(tmp_path.rglob('*.ttl'))
