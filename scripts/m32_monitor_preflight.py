"""不讀Capture、不配準：驗證原ps即時RSS監控與失效停止行為。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import record_command as recorder


def probe(output):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    results = {}
    for name, argv in [
        ('shell_ps', ['/bin/zsh', '-c', '/bin/ps -o rss= -p $$']),
        ('python_subprocess_ps', ['/bin/ps', '-o', 'rss=', '-p', str(os.getpid())])]:
        try:
            p = subprocess.run(argv, capture_output=True, text=True, check=True)
            kb = int(p.stdout.strip())
            if kb <= 0: raise RuntimeError('Nonpositive RSS')
            results[name] = dict(passed=True, rss_kib=kb, exit_code=p.returncode)
        except Exception:
            results[name] = dict(passed=False, traceback=traceback.format_exc())
    try:
        rss = recorder._rss_bytes(os.getpid())
        if rss <= 0: raise RuntimeError('Nonpositive recorder RSS')
        results['recorder_self_rss'] = dict(passed=True, rss_bytes=rss)
    except Exception:
        results['recorder_self_rss'] = dict(passed=False, traceback=traceback.format_exc())
    if all(row['passed'] for row in results.values()):
        child = "import os,time; x=bytearray(32*2**20); print('probe child',os.getpid(),flush=True); time.sleep(2.2)"
        execution = recorder.run([sys.executable, '-c', child], output/'live_child', 3)
        samples = [json.loads(line) for line in (output/'live_child/memory_samples.jsonl').read_text().splitlines()]
        passed = (execution['exit_code'] == 0 and execution['resource_guard']['reason'] is None
            and execution['rss_limit_gib'] == 3 and len(samples) >= 3
            and all(row['rss_bytes'] > 0 for row in samples)
            and all(b['elapsed_s'] > a['elapsed_s'] for a,b in zip(samples,samples[1:])))
        results['continuous_child_rss'] = dict(passed=passed, samples=len(samples), execution=execution)
        # 合成測試使用低門檻驗證同一護欄；正式與正常取樣測試仍固定3 GiB。
        limited = recorder.run([sys.executable, '-c', child], output/'synthetic_low_limit', .001)
        results['guard_termination'] = dict(passed=limited['exit_code'] != 0
            and 'exceeds' in str(limited['resource_guard']['reason']), execution=limited)
        original = recorder._rss_bytes
        def unavailable(pid):
            raise PermissionError('Synthetic monitor unavailable; deliberate preflight fault injection')
        try:
            recorder._rss_bytes = unavailable
            failed = recorder.run([sys.executable, '-c', child], output/'synthetic_monitor_failure', 3)
        finally:
            recorder._rss_bytes = original
        results['monitor_failure_termination'] = dict(passed=failed['exit_code'] != 0
            and 'Synthetic monitor unavailable' in str(failed['resource_guard']['reason'])
            and failed['total_process_s'] < 2.2, execution=failed)
    value = dict(passed=all(r['passed'] for r in results.values()), results=results,
        reconstruction_started=False, capture_read=False, recorder_path=str(ROOT/'scripts/record_command.py'))
    (output/'probe.json').write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(value, indent=2), flush=True)
    if not value['passed']: raise RuntimeError('RSS permission/function preflight failed')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    probe(args.output)
