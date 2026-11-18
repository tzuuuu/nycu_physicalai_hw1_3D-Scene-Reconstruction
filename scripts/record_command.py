"""直接執行官方指令，保留 stdout/stderr、耗時與子程序記憶體高水位。"""
import argparse
import json
import os
import resource
import subprocess
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path


def _rss_bytes(pid):
    measured = subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)],
                              capture_output=True, text=True)
    if measured.returncode or not measured.stdout.strip():
        raise RuntimeError('Cannot monitor child RSS')
    return int(measured.stdout.strip()) * 1024


def run(command, output, rss_limit_gib=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    stamp = datetime.now(timezone.utc).isoformat()
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    stop = threading.Event()
    guard = {'reason': None, 'sampled_peak_rss_bytes': 0}
    with (output / 'console.log').open('x', encoding='utf-8') as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1, env=env)
        print(f'Official command PID: {process.pid}', flush=True)
        def monitor():
            # 只監測資源；超限或無法量測時中止，不改動演算法與實驗資料。
            while not stop.wait(0.5):
                if process.poll() is not None:
                    return
                try:
                    rss = _rss_bytes(process.pid)
                    guard['sampled_peak_rss_bytes'] = max(guard['sampled_peak_rss_bytes'], rss)
                    with (output / 'memory_samples.jsonl').open('a') as sample:
                        sample.write(json.dumps({'elapsed_s': time.perf_counter() - started, 'rss_bytes': rss}) + '\n')
                    if rss > rss_limit_gib * 2**30:
                        raise RuntimeError(f'Child RSS exceeds {rss_limit_gib} GiB guard')
                except Exception as exc:
                    if process.poll() is None:
                        guard['reason'] = str(exc)
                        process.terminate()
                    return
        watcher = None
        if rss_limit_gib is not None:
            watcher = threading.Thread(target=monitor, daemon=True)
            watcher.start()
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end='', flush=True)
        code = process.wait()
        stop.set()
        if watcher is not None:
            watcher.join()
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    result = {'command': command, 'cwd': os.getcwd(), 'started_utc': stamp,
              'total_process_s': time.perf_counter() - started, 'exit_code': code,
              'child_peak_rss_bytes': int(peak if sys.platform == 'darwin' else peak * 1024),
              'timing_boundary': 'child startup through official command exit, including all command outputs',
              'rss_limit_gib': rss_limit_gib, 'resource_guard': guard,
              'status': 'process_completed_requires_artifact_validation' if code == 0 else 'failed'}
    (output / 'execution.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--rss-limit-gib', type=float, default=None)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('an official command is required after --')
    result = run(command, args.output, rss_limit_gib=args.rss_limit_gib)
    print(json.dumps(result, indent=2), flush=True)
    raise SystemExit(result['exit_code'])
