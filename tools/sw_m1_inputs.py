"""Read-only USER-authorized original60 gold admission; never print private data.

This is a portability regression, NOT a fresh blind holdout or production rerun.
The original frozen cohort/card bytes are authenticated, never rewritten.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import sw_m0 as base

PRIVATE=base.OUTPUTS/'m1-private'
COHORT_SHA='45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65'
MANIFEST=Path('C:/dev/CAD-HARNESS-herdr/reports/verify-v4-saved59-final60-20261021T142620Z/original-final60-freeze/manifest.json')
MANIFEST_SHA='42baa6abb9c5544cb66dc03690447a6c47f18586b56731d1ae2188d72713bcc3'
OLD_LAUNCH=Path('C:/dev/v4claude-continuation42-custody/launch.json')
FAMILIES={'roller','taper','elbow','ribbed_box','flange','rect_prism','rect_stack','stepped_shaft'}
GROUPS={'dev','legacy','mvp','geometry','q','completion','fault'}
ROUTES={'source','spec','mvp','completion','ask','offline'}


def private_path(value):
    p=base.output_path(value)
    if not p.is_relative_to(PRIVATE) or p==PRIVATE:raise ValueError('M1_private_path_required')
    return p


def admitted():
    from tools.cad_verify_v4_live import load_cohort,safe_input
    if base.digest(MANIFEST)!=MANIFEST_SHA:raise ValueError('original_manifest_binding')
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    metadata=json.loads(OLD_LAUNCH.read_text(encoding='utf-8'))
    argv=metadata.get('argv')
    if not isinstance(argv,list):raise ValueError('opaque_locator_metadata_missing')
    indexes=[i for i,item in enumerate(argv) if item=='--sealed-input']
    if len(indexes)!=1 or indexes[0]+1>=len(argv):raise ValueError('opaque_locator_ambiguous')
    sealed=Path(argv[indexes[0]+1])
    if base.digest(sealed)!=COHORT_SHA:raise ValueError('original_cohort_binding')
    cohort=load_cohort(sealed,manifest)
    rows=[]
    for entry in cohort['entries']:
        card=json.loads(safe_input(sealed.parent,entry['acceptance']).read_text(encoding='utf-8'))
        gold_path=safe_input(sealed.parent,card['gold']) if card.get('gold') else None
        gold=json.loads(gold_path.read_text(encoding='utf-8')) if gold_path else None
        profile=(gold.get('profile') or gold.get('family') or 'rect_prism') if gold else None
        if gold and gold.get('steps') and not gold.get('regions'):profile='stepped_shaft'
        if gold and len(gold.get('regions',[]))>1:profile='rect_stack'
        if profile is not None and profile not in FAMILIES:profile='unsupported_profile'
        if entry['group'] not in GROUPS or entry['route'] not in ROUTES:raise ValueError('unknown_original_route')
        rows.append({'sequence':entry['sequence'],'group':entry['group'],'route':entry['route'],
                     'profile':profile,'card':card,'gold':gold,
                     'gold_path':str(gold_path) if gold_path else None,
                     'gold_sha256':base.digest(gold_path) if gold_path else None,
                     'card_sha256':base.digest(safe_input(sealed.parent,entry['acceptance']))})
    if len(rows)!=60:raise ValueError('original_count')
    return {'cohort_sha256':COHORT_SHA,'manifest_sha256':MANIFEST_SHA,'source_base':str(sealed.parent),
            'entries':rows,'scope':'mechanical_gold_portability_only_not_model_evaluation',
            'paid_model_calls':0}


def inventory(out):
    out=private_path(out);out.mkdir(parents=True,exist_ok=False)
    value=admitted()
    base.save_json(out/'inputs.json',value)
    summaries=[]
    for row in value['entries']:
        physical=row['route'] not in ('ask','offline')
        summaries.append({'sequence':row['sequence'],'group':row['group'],'route':row['route'],
                          'profile':row['profile'],'gold_present':row['gold'] is not None,
                          'CAD_portability_applicable':physical,
                          'parameter_keys':sorted(row['gold'].get('parameters',{})) if row['gold'] else []})
    # Family/field NAME metadata only. No request, identifiers, values or geometry.
    public={'status':'PASS','at':base.utc(),'scope':value['scope'],'paid_model_calls':0,
            'total':len(summaries),'profiles':dict(Counter(r['profile'] for r in summaries if r['CAD_portability_applicable'])),
            'rows':summaries,'inputs_sha256':base.digest(out/'inputs.json'),
            'cohort_sha256':COHORT_SHA,'original_source_unchanged':True}
    base.save_json(out/'inventory-public.json',public)
    return public


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inventory',required=True)
    args=parser.parse_args()
    try:
        result=inventory(args.inventory)
        print(json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        # Never expose private paths/values through a traceback or exception text.
        print(json.dumps({'status':'FAIL','stage':'input_admission','error_type':type(exc).__name__,'paid_model_calls':0}))
        raise SystemExit(1)
