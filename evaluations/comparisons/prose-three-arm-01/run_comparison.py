"""Explicit-loading prose diagnostic. Raw runs remain in ignored evaluations/runs/."""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import random
import runpy
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
UPSTREAM = ROOT / 'evaluations/fixtures/upstreams/humanizer/9862685f575c65a8247f90369951df1b3416e3d6'
MAX_WORKERS = 2
TIMEOUT_SECONDS = 180


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build_prompt(common, case, files):
    package = '' if files is None else '\n技能资料（文件名与完整内容）：\n' + json.dumps(files, ensure_ascii=False)
    return common + package + '\n用户任务与原始材料：\n' + case['prompt']


def valid_record(record):
    return (record['exit_code'] == 0 and bool(record['raw_output'].strip())
            and record['turn_completed'] and not record['tool_items'] and not record['error'])


def main():
    protocol = json.loads((BASE / 'protocol.json').read_text(encoding='utf-8'))
    cases = json.loads((BASE / 'cases.json').read_text(encoding='utf-8'))
    exe = shutil.which('codex.exe')
    if not exe:
        raise RuntimeError('codex.exe not found')
    local_folder = ROOT / 'skills/creation/prose-polish'
    local_files = {p.relative_to(local_folder).as_posix(): p.read_bytes().decode('utf-8')
                   for p in sorted(local_folder.rglob('*')) if p.is_file()}
    packages = {'baseline': None, 'ours': local_files,
                'upstream': {'SKILL.md': (UPSTREAM / 'SKILL.md').read_bytes().decode('utf-8')}}
    provenance = json.loads((UPSTREAM / 'provenance.json').read_text(encoding='utf-8'))
    for name, meta in provenance['files'].items():
        if digest((UPSTREAM / name).read_bytes()) != meta['sha256']:
            raise RuntimeError('Upstream bytes changed: ' + name)
    fingerprint = runpy.run_path(str(ROOT / 'scripts/validate_collection.py'))['package_fingerprint']
    run_root = ROOT / 'evaluations/runs' / (protocol['id'] + '-' + uuid.uuid4().hex[:8])
    run_root.mkdir(parents=True)
    snapshot = {'frozen_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'protocol': protocol, 'cases': cases, 'packages': packages,
                'ours_version': '0.1.1', 'ours_package_sha256': fingerprint(local_folder),
                'upstream_provenance': provenance,
                'upstream_license': (UPSTREAM / 'LICENSE').read_text(encoding='utf-8'),
                'source_hashes': {n: digest((BASE/n).read_bytes())
                                  for n in ['protocol.json', 'cases.json', 'run_comparison.py']}}
    save(run_root / 'frozen.json', snapshot)
    jobs = [(c, arm, repeat) for c in cases for arm in protocol['arms']
            for repeat in range(1, protocol['repetitions'] + 1)]
    random.Random(protocol['run_order_seed']).shuffle(jobs)

    def execute(job):
        case, arm, repeat = job
        rid = uuid.uuid4().hex
        folder = run_root / rid
        folder.mkdir()
        prompt = build_prompt(protocol['common_prompt'], case, packages[arm])
        raw_prompt = prompt.encode('utf-8')
        (folder / 'prompt.txt').write_bytes(raw_prompt)
        work = tempfile.mkdtemp(prefix='zero-prose-comparison-')
        args = [exe, 'exec', '--ephemeral', '--ignore-user-config', '--skip-git-repo-check',
                '--sandbox', 'read-only', '--model', protocol['model'],
                '-c', 'model_reasoning_effort="' + protocol['reasoning_effort'] + '"',
                '--json', '--output-last-message', str(folder / 'final.txt'), '--cd', work, '-']
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tick = time.monotonic()
        try:
            proc = subprocess.run(args, input=raw_prompt, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=TIMEOUT_SECONDS,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            code, stdout, stderr, error = proc.returncode, proc.stdout, proc.stderr, None
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr, error = None, exc.stdout or b'', exc.stderr or b'', 'timeout; no retry'
        elapsed = round((time.monotonic() - tick) * 1000)
        (folder / 'events.jsonl').write_bytes(stdout)
        (folder / 'stderr.txt').write_bytes(stderr)
        output = (folder / 'final.txt').read_bytes() if (folder / 'final.txt').exists() else b''
        events = []
        for line in stdout.decode('utf-8').splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        completed = [e for e in events if e.get('type') == 'turn.completed']
        tool_items = [e for e in events if e.get('item', {}).get('type') in
                      ('command_execution', 'mcp_tool_call', 'web_search', 'file_change')]
        record = {'run_id': rid, 'case_id': case['id'], 'arm': arm, 'repeat': repeat,
                  'args': args, 'exact_prompt': prompt, 'prompt_sha256': digest(raw_prompt),
                  'raw_output': output.decode('utf-8'), 'output_sha256': digest(output),
                  'raw_events': stdout.decode('utf-8'), 'events_sha256': digest(stdout),
                  'stderr': stderr.decode('utf-8'), 'stderr_sha256': digest(stderr),
                  'exit_code': code, 'error': error, 'turn_completed': bool(completed),
                  'started_at': start, 'observed_duration_ms': elapsed,
                  'usage': completed[-1].get('usage') if completed else None,
                  'tool_items': tool_items}
        record['valid'] = valid_record(record)
        save(folder / 'record.json', record)
        print('Finished', case['id'], 'valid=' + str(record['valid']), flush=True)
        return record

    print('RUN_ROOT', run_root, flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        records = list(pool.map(execute, jobs))
    save(run_root / 'records.json', records)
    review_order = records[:]
    secrets.SystemRandom().shuffle(review_order)
    blind = [{'sample_id': f'S{i+1:02}', 'case_id': r['case_id'], 'valid': r['valid'],
              'output': r['raw_output']} for i, r in enumerate(review_order)]
    save(run_root / 'blind-review.json', blind)
    save(run_root / 'blind-key.json', {f'S{i+1:02}': {'run_id': r['run_id'], 'arm': r['arm'],
                                                  'repeat': r['repeat']}
                                     for i, r in enumerate(review_order)})
    print('COMPLETE', len(records), 'valid', sum(r['valid'] for r in records), flush=True)
    if not all(r['valid'] for r in records):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
