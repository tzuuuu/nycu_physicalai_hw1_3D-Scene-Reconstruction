"""直接執行官方指令，保留 stdout/stderr、耗時與子程序記憶體高水位。"""
import argparse
import json
import os
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def run(command, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    stamp = datetime.now(timezone.utc).isoformat()
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    with (output / 'console.log').open('x', encoding='utf-8') as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1, env=env)
        print(f'Official command PID: {process.pid}', flush=True)
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end='', flush=True)
        code = process.wait()
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    result = {'command': command, 'cwd': os.getcwd(), 'started_utc': stamp,
              'total_process_s': time.perf_counter() - started, 'exit_code': code,
              'child_peak_rss_bytes': int(peak if sys.platform == 'darwin' else peak * 1024),
              'timing_boundary': 'child startup through official command exit, including all command outputs',
              'status': 'process_completed_requires_artifact_validation' if code == 0 else 'failed'}
    (output / 'execution.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('an official command is required after --')
    result = run(command, args.output)
    print(json.dumps(result, indent=2), flush=True)
    raise SystemExit(result['exit_code'])
