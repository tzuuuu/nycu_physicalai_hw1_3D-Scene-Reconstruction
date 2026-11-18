"""執行紀錄工具不將程序成功誤當成產物驗證，也保留失敗輸出。"""
import importlib.util
import json
import sys
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('record_command', Path(__file__).parents[1] / 'scripts/record_command.py')
recorder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recorder)


@pytest.mark.parametrize('code', [0, 3])
def test_records_actual_exit_output_and_does_not_overwrite(tmp_path, code):
    output = tmp_path / 'record'
    result = recorder.run([sys.executable, '-c', f"print('actual child output'); raise SystemExit({code})"], output)
    assert result['exit_code'] == code
    assert result['total_process_s'] > 0
    assert 'actual child output' in (output / 'console.log').read_text()
    assert json.loads((output / 'execution.json').read_text()) == result
    assert result['status'] == ('process_completed_requires_artifact_validation' if code == 0 else 'failed')
    with pytest.raises(FileExistsError):
        recorder.run([sys.executable, '-c', 'pass'], output)


def test_resource_guard_stops_child_and_preserves_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, '_rss_bytes', lambda pid: 20 * 2**20)
    result = recorder.run([sys.executable, '-c', "import time; print('started', flush=True); time.sleep(10)"],
                          tmp_path / 'guarded', rss_limit_gib=0.01)
    assert result['exit_code'] != 0
    assert result['status'] == 'failed'
    assert 'exceeds' in result['resource_guard']['reason']
    assert (tmp_path / 'guarded' / 'memory_samples.jsonl').exists()


def test_monitor_unavailable_terminates_live_child_and_preserves_reason(tmp_path, monkeypatch):
    def unavailable(pid):
        raise PermissionError('synthetic ps permission denied')
    monkeypatch.setattr(recorder, '_rss_bytes', unavailable)
    result = recorder.run([sys.executable, '-c', "import time; print('live',flush=True); time.sleep(10)"],
                          tmp_path/'unavailable', rss_limit_gib=3)
    assert result['exit_code'] != 0 and result['total_process_s'] < 3
    assert result['rss_limit_gib'] == 3
    assert result['resource_guard']['reason'] == 'synthetic ps permission denied'
    assert json.loads((tmp_path/'unavailable/execution.json').read_text()) == result
