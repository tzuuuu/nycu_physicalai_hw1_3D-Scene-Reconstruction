"""Preflight 紀錄工具不替代官方流程，僅測試統計與不覆蓋護欄。"""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('m2_preflight', Path(__file__).parents[1] / 'scripts/m2_preflight.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def test_factor_summary_keeps_actual_values():
    records = {('RawPointCount', 1): {'value': 10}, ('RawPointCount', 2): {'value': 20}}
    pair = {('ICPInlierFitness', 1, 2): {'value': 0.25}}
    summary = preflight.factor_summary(records, pair)
    assert summary['RawPointCount'] == {'count': 2, 'min': 10, 'max': 20, 'mean': 15}
    assert summary['ICPInlierFitness']['min'] == 0.25
    assert preflight.peak_rss_bytes() > 0


def test_output_cannot_overwrite_capture(tmp_path):
    with pytest.raises(ValueError, match='outside'):
        preflight.run(tmp_path, tmp_path / 'unsafe', 5)
    assert not (tmp_path / 'unsafe').exists()


def test_frame_count_validation_precedes_writes(tmp_path):
    with pytest.raises(ValueError, match='two frames'):
        preflight.run(tmp_path, tmp_path / 'unused', 1)


def test_resource_extrapolation_is_explicit_and_nonoverwriting(tmp_path):
    import json
    spec = importlib.util.spec_from_file_location('m2_summary', Path(__file__).parents[1] / 'scripts/summarize_m2_preflight.py')
    summary_tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(summary_tool)
    (tmp_path / 'inventory.json').write_text(json.dumps({'valid_points_total': 400, 'map_position_color_bytes': 400 * 48, 'rgb_count': 20}))
    run_dir = tmp_path / 'frames_05'
    run_dir.mkdir()
    measured = {'frames': list(range(1, 6)), 'peak_rss_bytes': 300 * 2**20,
                'rss_at_start_bytes': 100 * 2**20, 'raw_points_total': 100, 'reconstruction_s': 10}
    source = json.dumps(measured)
    (run_dir / 'summary.json').write_text(source)
    result = summary_tool.summarize(tmp_path)
    assert result['full_batch_estimates'][0]['full_peak_GiB_estimate'] == pytest.approx(900 / 1024)
    assert result['full_batch_estimates'][0]['full_reconstruction_s_estimate'] == 40
    assert (run_dir / 'summary.json').read_text() == source
    with pytest.raises(FileExistsError):
        summary_tool.summarize(tmp_path)
