"""Bounded patch/feedback experiment; candidate code executes only after review."""
import argparse
import ast
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import random
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
UPSTREAM = ROOT / 'evaluations/fixtures/upstreams/superpowers/b36e0829c6d0140e93cfef2ca599b1b07d4a7797'
MODEL_TIMEOUT = 240
TEST_TIMEOUT = 15


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def snapshot(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes().decode('utf-8')
            for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def parse_submission(raw, allowed):
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('files'), dict) or type(data.get('done')) is not bool:
        raise ValueError('Expected object with files object and done boolean')
    for name, content in data['files'].items():
        if name not in allowed or not isinstance(content, str):
            raise ValueError('Only explicitly allowed UTF-8 Python files may change')
        ast.parse(content, filename=name)
    return data


def run_tests(work, modules):
    args = [sys.executable, '-B', '-m', 'unittest', *modules, '-v']
    tick = time.monotonic()
    try:
        p = subprocess.run(args, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=TEST_TIMEOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        code, out, err, error = p.returncode, p.stdout, p.stderr, None
    except subprocess.TimeoutExpired as exc:
        code, out, err, error = None, exc.stdout or b'', exc.stderr or b'', 'test timeout'
    raw_log = work / '.evaluation-logs' / (uuid.uuid4().hex + '.json')
    raw_log.parent.mkdir(exist_ok=True)
    save(raw_log, {'stdout': out.decode('utf-8', errors='replace'), 'stderr': err.decode('utf-8', errors='replace'), 'exit_code': code})
    def redact(value):
        return value.decode('utf-8', errors='replace').replace(str(work), '<PROJECT>').replace(str(Path.home()), '<USER_HOME>')
    text = redact(out) + redact(err)
    match = re.search(r'Ran (\d+) tests? in', text)
    return {'command': ['python', '-B', '-m', 'unittest', *modules, '-v'], 'exit_code': code,
            'stdout': redact(out), 'stderr': redact(err), 'raw_stdout_sha256': sha(out), 'raw_stderr_sha256': sha(err), 'raw_log_id': raw_log.name,
            'error': error, 'tests_run': int(match.group(1)) if match else 0,
            'has_skips': bool(re.search(r'\bskipped\b', text)),
            'observed_duration_ms': round((time.monotonic()-tick)*1000)}


def tests_pass(result, minimum):
    return (result['exit_code'] == 0 and not result['error'] and not result['has_skips']
            and result['tests_run'] >= minimum)


def initialize():
    protocol = read(BASE/'protocol.json')
    local_folder = ROOT/'skills/engineering/debug-evidence-triage'
    upstream = snapshot(UPSTREAM)
    provenance = read(UPSTREAM/'provenance.json')
    for name, item in provenance['files'].items():
        if sha((UPSTREAM/name).read_bytes()) != item['sha256']:
            raise ValueError('Upstream bytes changed')
    packages = {'baseline': None, 'ours': snapshot(local_folder),
                'upstream': {n:v for n,v in upstream.items() if n.startswith('skills/')}}
    root = ROOT/'evaluations/runs'/('engineering-three-arm-01-'+uuid.uuid4().hex[:8])
    root.mkdir(parents=True)
    fixture = {case: snapshot(BASE/'fixtures'/case) for case in protocol['cases']}
    frozen = {'frozen_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'protocol': protocol, 'packages': packages, 'fixtures': fixture,
              'ours_version': '0.1.1',
              'ours_package_sha256': runpy.run_path(str(ROOT/'scripts/validate_collection.py'))['package_fingerprint'](local_folder),
              'upstream_provenance': provenance, 'upstream_license': upstream['LICENSE'],
              'source_hashes': {n:sha((BASE/n).read_bytes()) for n in ['protocol.json','run_comparison.py']},
              'fixture_verification': read(BASE/'fixture-verification-current.json')}
    save(root/'frozen.json', frozen)
    matrix = [(c,a,k) for c in protocol['cases'] for a in protocol['arms'] for k in [1,2]]
    random.Random(protocol['seed']).shuffle(matrix)
    jobs = []
    for i,(case,arm,repeat) in enumerate(matrix):
        work = Path(tempfile.mkdtemp(prefix='zero-engineering-patch-'))
        visible = {n.removeprefix('public/'):v for n,v in fixture[case].items() if n.startswith('public/')}
        for n,v in visible.items():
            (work/n).write_bytes(v.encode('utf-8'))
        initial = run_tests(work, ['test_public'])
        job = {'id':f'E{i+1:02}', 'case':case, 'arm':arm, 'repeat':repeat,
               'work':str(work), 'initial_files':visible, 'initial_test':initial,
               'history':[], 'done':False, 'steps':[]}
        jobs.append(job)
    save(root/'jobs.json', jobs)
    print('RUN_ROOT',root,flush=True)


def generate(root, step):
    frozen, jobs = read(root/'frozen.json'), read(root/'jobs.json')
    protocol = frozen['protocol']
    if not 1 <= step <= protocol['max_turns']:
        raise ValueError('Out of turn budget')
    selected = [j for j in jobs if not j['done']]
    if any(len(j['steps']) != step-1 for j in selected):
        raise ValueError('Apply previous round before advancing')
    def execute(job):
        folder=root/job['id']/f'step-{step}'
        folder.mkdir(parents=True,exist_ok=False)
        package=frozen['packages'][job['arm']]
        prompt=protocol['common_prompt']
        if package is not None:
            prompt+='\n技能资料（完整内容）：\n'+json.dumps(package,ensure_ascii=False)
        prompt+='\n允许修改的文件：'+json.dumps(protocol['allowed_files'][job['case']])
        prompt+='\n项目初始文件：\n'+json.dumps(job['initial_files'],ensure_ascii=False)
        prompt+='\n运行器已执行的原始复现：\n'+json.dumps(job['initial_test'],ensure_ascii=False)
        prompt+='\n此前对话及实际测试反馈：\n'+json.dumps(job['history'],ensure_ascii=False)
        prompt+=f'\n当前为第{step}轮（最多{protocol["max_turns"]}轮）。请提交本轮JSON。'
        raw=prompt.encode('utf-8');(folder/'prompt.txt').write_bytes(raw)
        cwd=tempfile.mkdtemp(prefix='zero-engineering-text-session-')
        args=[shutil.which('codex.exe'),'exec','--ephemeral','--ignore-user-config','--skip-git-repo-check',
              '--sandbox','read-only','--model',protocol['model'],'-c','model_reasoning_effort="medium"',
              '--json','--output-last-message',str(folder/'final.txt'),'--cd',cwd,'-']
        started=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.monotonic()
        try:
            p=subprocess.run(args,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             timeout=MODEL_TIMEOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            code,out,err,error=p.returncode,p.stdout,p.stderr,None
        except subprocess.TimeoutExpired as exc:
            code,out,err,error=None,exc.stdout or b'',exc.stderr or b'','model timeout; no retry'
        elapsed=round((time.monotonic()-tick)*1000)
        (folder/'events.jsonl').write_bytes(out);(folder/'stderr.txt').write_bytes(err)
        final=(folder/'final.txt').read_bytes() if (folder/'final.txt').exists() else b''
        events=[]
        for line in out.decode('utf-8',errors='replace').splitlines():
            try: events.append(json.loads(line))
            except json.JSONDecodeError: pass
        complete=[e for e in events if e.get('type')=='turn.completed']
        tools=[e for e in events if e.get('item',{}).get('type') not in (None,'agent_message','reasoning')]
        record={'id':job['id'],'case':job['case'],'step':step,'started_at':started,
                'exact_prompt':prompt,'prompt_sha256':sha(raw),'raw_output':final.decode('utf-8'),
                'output_sha256':sha(final),'raw_events':out.decode('utf-8'),'events_sha256':sha(out),
                'stderr':err.decode('utf-8'),'stderr_sha256':sha(err),'exit_code':code,'error':error,
                'usage':complete[-1].get('usage') if complete else None,'tool_items':tools,
                'observed_duration_ms':elapsed,'technical_valid':code==0 and bool(final) and bool(complete) and not tools and not error}
        save(folder/'record.json',record)
        print('Generated',job['id'],job['case'],'step',step,'valid',record['technical_valid'],flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(execute,selected))
    print('ROUND_GENERATED',step,len(selected),flush=True)


def apply_round(root,step):
    frozen,jobs=read(root/'frozen.json'),read(root/'jobs.json')
    approved=read(root/f'reviewed-step-{step}.json')
    for job in jobs:
        if job['done']:
            continue
        folder=root/job['id']/f'step-{step}'
        rec=read(folder/'record.json')
        if approved.get(job['id']) != rec['output_sha256']:
            raise ValueError('Candidate requires matching code-review approval: '+job['id'])
        if len(job['steps']) != step-1:
            raise ValueError('Round already applied')
        before={p.name:sha(p.read_bytes()) for p in Path(job['work']).glob('*.py')}
        parse_error=None;data=None
        try:
            if not rec['technical_valid']:
                raise ValueError('Model turn did not complete normally')
            data=parse_submission(rec['raw_output'],frozen['protocol']['allowed_files'][job['case']])
            for name,body in data['files'].items():
                (Path(job['work'])/name).write_bytes(body.encode('utf-8'))
        except (ValueError,SyntaxError) as exc:
            parse_error=str(exc)
        modules=['test_public']
        if (Path(job['work'])/'test_regression.py').exists():
            modules.append('test_regression')
        result=run_tests(Path(job['work']),modules)
        feedback={'submission_error':parse_error,'actual_test_run':result}
        job['history'].extend([{'role':'assistant','content':rec['raw_output']},
                               {'role':'user','content':'运行器实际反馈：'+json.dumps(feedback,ensure_ascii=False)}])
        saved={'step':step,'submission_error':parse_error,'files_before_sha256':before,
               'submitted_files':data['files'] if data is not None else {},'public_and_regression':result,
               'source_after':(Path(job['work'])/(job['case']+'.py')).read_bytes().decode('utf-8')}
        save(folder/'application.json',saved);job['steps'].append(saved)
        if data is not None and data['done']:
            job['done']=True
        print('Applied',job['id'],job['case'],'step',step,'exit',result['exit_code'],'done',job['done'],flush=True)
    save(root/'jobs.json',jobs)


def acceptance(root):
    frozen,jobs=read(root/'frozen.json'),read(root/'jobs.json')
    results=[]
    for job in jobs:
        case=job['case'];current=Path(job['work'])
        final_files={p.name:p.read_bytes().decode('utf-8') for p in current.glob('*.py')}
        public_intact=all((current/n).read_bytes().decode('utf-8')==v for n,v in job['initial_files'].items() if n!=case+'.py')
        work=Path(tempfile.mkdtemp(prefix='zero-engineering-acceptance-'))
        for n,v in final_files.items():(work/n).write_bytes(v.encode('utf-8'))
        (work/'test_acceptance.py').write_bytes(frozen['fixtures'][case]['heldout/test_acceptance.py'].encode('utf-8'))
        public=run_tests(work,['test_public'])
        heldout=run_tests(work,['test_acceptance'])
        regression_final=run_tests(work,['test_regression']) if 'test_regression.py' in final_files else None
        (work/(case+'.py')).write_bytes(frozen['fixtures'][case]['public/'+case+'.py'].encode('utf-8'))
        regression_original=run_tests(work,['test_regression']) if 'test_regression.py' in final_files else None
        result={'id':job['id'],'case':case,'public_intact':public_intact,'final_files':final_files,
                'public':public,'heldout':heldout,'regression_final':regression_final,
                'regression_original':regression_original,
                'artifact_acceptance':public_intact and tests_pass(public,3) and tests_pass(heldout,5 if case=='memo' else 6)}
        results.append(result)
        print('ACCEPT',job['id'],case,result['artifact_acceptance'],flush=True)
    save(root/'acceptance.json',results)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['init','generate','apply','acceptance'])
    parser.add_argument('--root',type=Path)
    parser.add_argument('--step',type=int)
    args=parser.parse_args()
    if args.action=='init':initialize()
    elif args.action=='generate':generate(args.root.resolve(),args.step)
    elif args.action=='apply':apply_round(args.root.resolve(),args.step)
    else:acceptance(args.root.resolve())
