"""Read-only failure classification. Never prints requests, argv values or gold."""
import argparse
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_h0_runtime as runtime,cad_verify_v4_live as live,cad_verify_v4_ledger as ledger
from tools.sw_m1_inputs import private_path

CATEGORIES={
    'unknown_option':r'unknown (?:option|argument)|unrecognized (?:option|argument)|unexpected argument',
    'unknown_model':r'model (?:not found|not available|not supported)|unknown model|no model matching|invalid model',
    'authentication':r'not authenticated|no (?:api key|credentials)|authentication (?:required|failed)|please (?:log ?in|authenticate)',
    'module_missing':r'cannot find module|module not found|cannot resolve',
    'configuration':r'invalid config|config.*(?:invalid|unknown|error)|unrecognized config',
    'invalid_usage':r'(?:^|\n)usage:|requires? (?:an? )?(?:argument|value)',
}
FLAGS={'--print','--mode','--model','--thinking','--no-tools','--no-lsp','--no-pty',
    '--no-extensions','--no-skills','--no-rules','--no-title','--no-session','--no-prewalk',
    '--config','--system-prompt'}
WORDS=set('error failed config configuration json thinking level mode model provider auth authentication broker credential api key missing unknown invalid prompt message messages stdin tty required requires cannot must not found file directory path permission denied enoent eacces token quota session profile subscription disabled arguments parse read access frozen sealed malformed locked'.split())


def diagnose(run):
    root=private_path(runtime.PRIVATE/run)
    events=list(ledger.rows(root/'ledger.jsonl'))
    rows=[]
    for episode in sorted(root.glob('episode-*')):
        for attempt in sorted(episode.glob('attempt-*')):
            if not (attempt/'submitted.json').is_file():continue
            submitted=ledger.read_json(attempt/'submitted.json')
            if submitted.get('model') is None:continue
            stderr=(attempt/'stderr.bin').read_text(encoding='utf-8',errors='replace')
            stdout=(attempt/'stdout.bin').read_text(encoding='utf-8',errors='replace')
            categories=[k for k,p in CATEGORIES.items() if re.search(p,stderr+'\n'+stdout,re.I|re.M)]
            flag_matches=re.findall(r'(?:unknown|unrecognized|unexpected)\s+(?:option|argument)[: ]+[\'\"]?(--[a-z][a-z0-9-]*)',stderr,re.I)
            parsed=live.omp_result(attempt/'stdout.bin')
            end=next((e for e in events if e['event']=='attempt_finished' and e.get('attempt_id')==attempt.name),{})
            rows.append(dict(sequence=int(episode.name.split('-')[-1]),
                exit_code=end.get('exit_code'),stderr_bytes=(attempt/'stderr.bin').stat().st_size,
                stdout_bytes=(attempt/'stdout.bin').stat().st_size,categories=categories,
                stderr_sha256=ledger.file_sha(attempt/'stderr.bin'),
                diagnostic_words=sorted(WORDS.intersection(re.findall(r'[a-z]+',stderr.lower()))),
                unknown_flags=[f for f in flag_matches if f in FLAGS],
                assistant_ends=parsed['assistant_ends'],final_present=parsed['final'] is not None,
                usage_records_known=any(v is not None for v in parsed['usage']['values'].values()),
                structured_provider_codes=[c for c in parsed['summary']['error_infos'] if c in ('server_overloaded','rate_limit_exceeded','authentication_error')]))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args()
    try:
        rows=diagnose(a.run);variants={}
        for row in rows:
            key=row['stderr_sha256']
            if key not in variants:variants[key]=dict(row,sequences=[])
            variants[key]['sequences'].append(row['sequence'])
        print(json.dumps({'attempts':len(rows),'variants':list(variants.values())}))
    except Exception as exc:
        print(json.dumps({'status':'FAIL','error_type':type(exc).__name__,
            'failure_site':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in __import__('traceback').extract_tb(exc.__traceback__)]}));raise SystemExit(1)
