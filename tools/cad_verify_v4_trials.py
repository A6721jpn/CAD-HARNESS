"""Separately authorized C-capability live trials; imports never launch a model.

Implementation locks are prerequisites, not authorizations. Sealed custody data
is admitted only after an explicit execution registration/authorization match.
Test transports remain unit_mock and cannot mint a usable live manifest.
"""
from contextlib import AbstractContextManager
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import time

if __package__:
    from . import cad_verify_v4_ledger as ledger, cad_verify_v4_live as live
    from . import cad_verify_v4_integrated as integrated, cad_verify_v4_agent as agent
    from . import cad_verify_v4_freeze as freezing, cad_verify_v4_s1 as s1
    from .cad_verify_guard import Stop, quota_snapshot
    from .cad_verify_v3_guard import Budget
else:
    import cad_verify_v4_ledger as ledger, cad_verify_v4_live as live
    import cad_verify_v4_integrated as integrated, cad_verify_v4_agent as agent
    import cad_verify_v4_freeze as freezing, cad_verify_v4_s1 as s1
    from cad_verify_guard import Stop, quota_snapshot
    from cad_verify_v3_guard import Budget

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = dict(model='openai-codex/gpt-6.1-sol', thinking='xhigh')
ASTRA = dict(model='openai-codex/gpt-6-astra', thinking='max')
MODULES = dict(families='cad_verify_v4_family_live', benchmark='cad_verify_v4_benchmark',
               pilot='cad_verify_v4_pilot_live', judge='cad_verify_v4_model_judge')
AUTH_SCHEMA = 'cad-harness.live-trial-authorization.v1'
MANIFEST_SCHEMA = 'cad-harness.live-trial.v1'
REGISTRATION_SCHEMA = 'cad-harness.live-registration.v1'


def _module(name):
    return importlib.import_module(('tools.' if __package__ else '') + name)


def _schema_check(name, value):
    schema = ledger.read_json(ROOT / 'design/cad-harness-verify-v4/schemas' / (name+'.schema.json'))
    _module('cad_verify_v4_plans')._check(value, schema, schema, '$')


def _digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _equal(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)


def _record(path):
    path = Path(path)
    before = path.stat()
    digest = ledger.file_sha(path)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise Stop('trial_file_changed_during_read')
    return dict(path=str(path), sha256=digest, bytes=after.st_size)


def _safe(value, *, regular=True):
    return s1.safe_path(value, regular=regular)


def _read_record(record):
    if not isinstance(record, dict) or not {'path', 'sha256', 'bytes'} <= record.keys():
        raise Stop('trial_file_record_required')
    if not _digest(record['sha256']) or type(record['bytes']) is not int or record['bytes'] < 0:
        raise Stop('trial_file_record_invalid')
    path = Path(record['path'])
    if not path.is_absolute():
        raise Stop('trial_bound_file_absolute_required')
    _custody_file(path.parent, path.name)
    actual = _record(path)
    if any(actual[key] != record[key] for key in ('sha256', 'bytes')):
        raise Stop('trial_bound_file_changed:' + str(path))
    return path


def _relative(value):
    if (not isinstance(value, str) or not value or any(char in value for char in '\\:\x00<>"|?*')
            or value.startswith('/') or any(not part or part in ('.', '..') or part.endswith((' ', '.'))
            or part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
                                            *('COM'+str(i) for i in range(1, 10)),
                                            *('LPT'+str(i) for i in range(1, 10))}
            for part in value.split('/'))):
        raise Stop('trial_relative_path_required')
    return value


def _custody_file(root, relative):
    """Only called after authorization. No unbounded traversal or link following."""
    path = root.joinpath(*_relative(relative).split('/'))
    for parent in reversed((path, *path.parents)):
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise Stop('trial_custody_link_or_reparse')
    if not path.is_relative_to(root) or not stat.S_ISREG(path.stat().st_mode):
        raise Stop('trial_custody_regular_file_required')
    return path


def _phase(registration):
    _schema_check('live-registration', registration)
    phase = registration.get('phase') if isinstance(registration, dict) else None
    if phase not in MODULES or registration.get('schema') != REGISTRATION_SCHEMA:
        raise Stop('trial_registration_contract')
    for key in ('trial_id', 'cycle_id', 'source_root'):
        if not isinstance(registration.get(key), str) or not registration[key].strip():
            raise Stop('trial_registration_identity')
    if not Path(registration['source_root']).is_absolute():
        raise Stop('trial_source_root_absolute')
    files = registration.get('files')
    if not isinstance(files, dict) or not files:
        raise Stop('trial_closed_file_inventory_required')
    paths = {}
    for name, record in files.items():
        if not isinstance(name, str) or not name or not isinstance(record, dict):
            raise Stop('trial_file_inventory_contract')
        path = _relative(record.get('path'))
        if (not _digest(record.get('sha256')) or type(record.get('bytes')) is not int or record['bytes'] < 0
                or not isinstance(record.get('role'), str) or not record['role']):
            raise Stop('trial_file_inventory_contract')
        if path.casefold() in paths:
            raise Stop('trial_duplicate_file_alias')
        paths[path.casefold()] = name
    _module(MODULES[phase]).validate_registration(registration)
    return phase


def reservations(registration):
    phase = registration['phase']
    if phase == 'judge':
        return {'judge': len(registration['entries'])}
    return dict(_module(MODULES[phase]).RESERVATIONS)


def _authorize(auth, registration, registration_record, lock_record):
    _schema_check('live-authorization', auth)
    if (not isinstance(auth, dict) or auth.get('schema') != AUTH_SCHEMA
            or auth.get('phase') != registration['phase'] or auth.get('trial_id') != registration['trial_id']
            or auth.get('cycle_id') != registration['cycle_id'] or auth.get('user_approved') is not True
            or auth.get('clock_confirmation') is not True or auth.get('independent_control_validation') is not True
            or not isinstance(auth.get('approved_by'), str) or not auth['approved_by'].strip()
            or auth.get('registration_sha256') != registration_record['sha256']
            or auth.get('integrated_manifest_sha256') != lock_record['sha256']
            or not _equal(auth.get('reserved_calls'), reservations(registration))
            or not isinstance(auth.get('quota_snapshot'), str) or not Path(auth['quota_snapshot']).is_absolute()
            or not isinstance(auth.get('omp_profile'), str) or not auth['omp_profile'].strip()):
        raise Stop('trial_separate_authorization_required')
    return auth


def _source_files(registration):
    root = Path(registration['source_root'])
    result = {}
    for name, binding in registration['files'].items():
        path = _custody_file(root, binding['path'])
        record = _record(path)
        if any(record[k] != binding[k] for k in ('sha256', 'bytes')):
            raise Stop('trial_input_commitment_mismatch:' + name)
        result[name] = record
    return result


def _input_closure(registration, files):
    """No manifest asset may escape the authenticated inventory after release."""
    originals = {str(Path(record['path'])).casefold(): name for name, record in files.items()}
    records = registration.get('entries', []) + registration.get('pairs', []) + registration.get('controls', [])
    manifest_ids = {entry['input_manifest'] for entry in records if 'input_manifest' in entry}
    manifests = {}
    for name, binding in registration['files'].items():
        if binding['role'] != 'input_manifest' and name not in manifest_ids:
            continue
        path = _read_record(files[name])
        document = ledger.read_json(path)
        assets = document.get('assets')
        if not isinstance(assets, dict):
            raise Stop('trial_input_manifest_assets_required')
        members = {}
        for asset_id, asset in assets.items():
            if not isinstance(asset, dict):
                raise Stop('trial_input_asset_record')
            relative = _relative(asset.get('path'))
            target = path.parent.joinpath(*relative.split('/'))
            identity = originals.get(str(target).casefold())
            if identity is None or any(asset.get(key) != files[identity][key] for key in ('sha256', 'bytes')):
                raise Stop('trial_unbound_manifest_asset:' + str(asset_id))
            members[identity] = asset.get('role')
        manifests[name] = members
    for entry in registration.get('entries', []) + registration.get('pairs', []):
        members = manifests.get(entry.get('input_manifest'), {})
        for identity in entry.get('model_inputs', []):
            if members.get(identity) == 'checker':
                raise Stop('trial_checker_asset_in_model_inputs')


def _public_bindings(registration, files, mode):
    if mode == 'unit_mock':
        return {}
    phase = registration['phase']
    required = {}
    if phase in ('families', 'benchmark'):
        required['families'] = (registration['public_commitment' if phase == 'families' else 'source_commitment'],
                                'holdout-families-commitment.md')
    elif phase == 'pilot':
        required['pilot'] = (registration['custody']['commitment'], 'pilot-bundle-commitment.md')
        required['rubric'] = (registration['rubric']['file'], 'pilot-rubric.json')
    result = {}
    for name, (identity, filename) in required.items():
        canonical = _record(_safe(ROOT / 'design/cad-harness-verify-v4' / filename))
        if identity not in files or any(files[identity][key] != canonical[key] for key in ('sha256', 'bytes')):
            raise Stop('trial_canonical_public_commitment_required:' + name)
        result[name] = canonical
    return result


def _pilot_prerequisites(registration, files, integrated_record, *, allow_mock):
    if registration['phase'] != 'pilot':
        return
    required = registration.get('prerequisites')
    if not isinstance(required, dict) or set(required) != {'original_holdout', 'families'}:
        raise Stop('trial_pilot_requires_completed_holdouts')
    for phase, references in required.items():
        if (not isinstance(references, dict) or set(references) != {'manifest', 'claim', 'result', 'ledger'}
                or any(identity not in files for identity in references.values())):
            raise Stop('trial_pilot_prerequisite_records')
        paths = {key: _read_record(files[identity]) for key, identity in references.items()}
        manifest = ledger.read_json(paths['manifest'])
        claim = ledger.read_json(paths['claim'])
        result = ledger.read_json(paths['result'])
        mode = result.get('evidence_mode')
        if mode != 'live' and not (allow_mock and mode == 'unit_mock'):
            raise Stop('trial_pilot_requires_real_holdout_evidence')
        if (claim.get('manifest_sha256') != ledger.file_sha(paths['manifest'])
                or Path(claim.get('run_dir', '')) != paths['result'].parent
                or paths['ledger'].parent != paths['result'].parent
                or result.get('stop_reason') is not None):
            raise Stop('trial_pilot_prerequisite_custody')
        if phase == 'original_holdout':
            if (manifest.get('schema') != 'cad-harness.manifest.v4'
                    or result.get('schema') != 'cad-harness.holdout-results.v4'
                    or result.get('status') != 'COMPLETE' or result.get('summary', {}).get('complete') is not True
                    or (mode == 'live' and result.get('fresh_holdout') != 'complete')
                    or paths['result'].name != 'summary.json'
                    or paths['claim'] != paths['manifest'].parent / 'manifest.claim.json'):
                raise Stop('trial_pilot_original_holdout_incomplete')
            if not allow_mock:
                freezing.verify(paths['manifest'])
        else:
            if (manifest.get('schema') != MANIFEST_SCHEMA or manifest.get('phase') != 'families'
                    or manifest.get('integrated_lock', {}).get('sha256') != integrated_record['sha256']
                    or result.get('schema') != 'cad-harness.family-live-result.v1'
                    or result.get('generative_denominator') != 43 or result.get('control_denominator') != 4
                    or len(result.get('records', [])) != 47
                    or any(row.get('status') in ('UNSTARTED', 'STARTED', 'INTERRUPTED')
                           for row in result['records'])
                    or paths['result'].name != 'family-result.json'
                    or paths['claim'] != paths['manifest'].parent / 'execution-claim.json'):
                raise Stop('trial_pilot_family_holdout_incomplete')
            if not allow_mock:
                verify_trial(paths['manifest'])
        events = list(ledger.rows(paths['ledger']))
        started = [row for row in events if row['event'] == 'run_started']
        finished = [row for row in events if row['event'] == 'run_finished']
        if (len(started) != 1 or len(finished) != 1 or events[-1] != finished[0]
                or started[0].get('manifest_sha256') != ledger.file_sha(paths['manifest'])
                or finished[0].get('stop_reason') is not None
                or not any(row['event'] == 'attempt_started' and row.get('operation') == 'model'
                           and row.get('evidence_mode') == mode for row in events)):
            raise Stop('trial_pilot_holdout_execution_evidence')


def _bound_phase_inputs(registration, files, integrated_record, *, allow_mock):
    _input_closure(registration, files)
    _pilot_prerequisites(registration, files, integrated_record, allow_mock=allow_mock)
    validator = getattr(_module(MODULES[registration['phase']]), 'validate_bound_inputs', None)
    if validator:
        validator(registration, lambda name: _read_record(files[name]))
    if registration['phase'] in ('families', 'benchmark'):
        _module('cad_verify_v4_model_judge').validate_rubric(
            ledger.read_json(_read_record(files[registration['rubric']])))
    cohort = registration.get('cohort')
    if cohort is not None:
        if not isinstance(cohort, dict) or not _digest(cohort.get('sha256')):
            raise Stop('trial_cohort_commitment_required')
        matches = [record for record in files.values() if record['sha256'] == cohort['sha256']
                   and record['bytes'] == cohort.get('bytes')]
        if not matches:
            raise Stop('trial_cohort_not_in_closed_inventory')
        document = ledger.read_json(_read_record(matches[0]))
        if registration['phase'] in ('families', 'benchmark') and document.get('schema') != 'cad-harness.family-roster.v1':
            raise Stop('trial_original_family_roster_required')


def _authority_paths(registration, authorization, mode):
    base = (ROOT / 'reports/live-authority' if mode == 'live'
            else Path(authorization['path']).parent / 'unit-live-authority')
    identity = {key: registration[key] for key in ('phase', 'trial_id', 'cycle_id')}
    paths = [base / ('authorization-'+authorization['sha256']+'.json'),
             base / ('trial-'+ledger.sha(json.dumps(identity, sort_keys=True).encode())+'.json')]
    if registration['phase'] in ('families', 'benchmark'):
        cohort = dict(phase=registration['phase'], sha256=registration['cohort']['sha256'])
        paths.append(base / ('cohort-'+ledger.sha(json.dumps(cohort, sort_keys=True).encode())+'.json'))
    return paths


def _authority_body(registration, authorization, lock, manifest_path, mode):
    return dict(schema='cad-harness.live-authority-claim.v1', evidence_mode=mode,
                phase=registration['phase'], trial_id=registration['trial_id'], cycle_id=registration['cycle_id'],
                authorization_sha256=authorization['sha256'], integrated_manifest_sha256=lock['sha256'],
                manifest_path=str(manifest_path))


def _claim_authority(registration, authorization, lock, manifest_path, mode):
    paths = _authority_paths(registration, authorization, mode)
    base = _safe(paths[0].parent, regular=False)
    base.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        with paths[0].open('x', encoding='utf-8', newline='\n') as file:
            created.append(paths[0])
            json.dump(_authority_body(registration, authorization, lock, manifest_path, mode),
                      file, ensure_ascii=False, allow_nan=False, indent=2)
            file.write('\n')
        for path in paths[1:]:
            os.link(paths[0], path)
            created.append(path)
        return dict(schema='cad-harness.live-authority-record.v1', records=[_record(path) for path in paths])
    except BaseException as exc:
        for path in reversed(created):
            path.unlink()
        if isinstance(exc, FileExistsError):
            raise Stop('trial_authorization_or_enrollment_already_frozen') from exc
        raise


def _verify_authority(manifest_path, manifest):
    claim = manifest.get('authority_claim')
    if (not isinstance(claim, dict) or set(claim) != {'schema', 'records'}
            or claim['schema'] != 'cad-harness.live-authority-record.v1' or not isinstance(claim['records'], list)):
        raise Stop('trial_authority_claim_required')
    paths = _authority_paths(manifest['registration_data'], manifest['authorization'], manifest['evidence_mode'])
    if [record.get('path') for record in claim['records']] != [str(path) for path in paths]:
        raise Stop('trial_authority_claim_path')
    expected = _authority_body(manifest['registration_data'], manifest['authorization'],
                               manifest['integrated_lock'], manifest_path, manifest['evidence_mode'])
    for record in claim['records']:
        path = _read_record(record)
        if not _equal(ledger.read_json(path), expected):
            raise Stop('trial_authority_claim_binding')


def verify_execution_claim(manifest_path, manifest, *, run_dir=None):
    manifest_path = _safe(manifest_path)
    _verify_authority(manifest_path, manifest)
    path = _safe(manifest_path.parent / 'execution-claim.json')
    claim = ledger.read_json(path)
    if (not isinstance(claim, dict) or set(claim) != {'manifest_sha256', 'run_dir'}
            or claim['manifest_sha256'] != ledger.file_sha(manifest_path)
            or not isinstance(claim['run_dir'], str) or not Path(claim['run_dir']).is_absolute()
            or not _safe(claim['run_dir'], regular=False).is_dir()
            or (run_dir is not None and Path(claim['run_dir']) != Path(run_dir).absolute())):
        raise Stop('trial_execution_claim_binding')
    return dict(claim, claim_file=_record(path))


def freeze_trial(registration_path, authorization_path, integrated_path, run_dir, *, omp='omp', verifier=None,
                 executable_resolver=None):
    """Freeze a separately approved phase, never synthesize authorization."""
    registration_path, authorization_path, integrated_path = map(_safe, (registration_path, authorization_path, integrated_path))
    registration_record, auth_record, lock_record = map(_record, (registration_path, authorization_path, integrated_path))
    registration, auth = ledger.read_json(registration_path), ledger.read_json(authorization_path)
    _phase(registration)
    _authorize(auth, registration, registration_record, lock_record)
    mode = 'unit_mock' if verifier is not None or executable_resolver is not None else 'live'
    lock = (verifier or integrated.verify)(integrated_path)
    if lock.get('schema') != integrated.SCHEMA or lock.get('authorization') is not None:
        raise Stop('trial_integrated_implementation_prerequisite')
    if os.environ.get('OMP_PROFILE') != auth['omp_profile']:
        raise Stop('trial_operator_profile_not_attested')
    generator = (executable_resolver or freezing._executable)(omp)
    if not generator.get('omp') or not generator.get('version') or not _digest(generator.get('sha256')):
        raise Stop('trial_pinned_omp_required')
    files = _source_files(registration)
    public = _public_bindings(registration, files, mode)
    _bound_phase_inputs(registration, files, lock_record, allow_mock=mode == 'unit_mock')
    out = ledger.new_directory(_safe(run_dir, regular=False))
    value = dict(schema=MANIFEST_SCHEMA, phase=registration['phase'], trial_id=registration['trial_id'],
                 cycle_id=registration['cycle_id'], freeze_dir=str(out), evidence_mode=mode,
                 registration=registration_record, authorization=auth_record, integrated_lock=lock_record,
                 registration_data=registration, source_files=files, reserved_calls=reservations(registration),
                 public_bindings=public,
                 quota_snapshot=auth['quota_snapshot'], omp_profile=auth['omp_profile'], omp=generator,
                 generators=dict(holdout=dict(GENERATOR), benchmark=dict(GENERATOR), pilot=dict(ASTRA)),
                 judge=dict(ASTRA), host=socket.gethostname(), live_calls=0, final_v4_ready=False)
    for record in (registration_record, auth_record, lock_record, *public.values()):
        _read_record(record)
    if files != _source_files(registration):
        raise Stop('trial_source_changed_during_freeze')
    value['authority_claim'] = _claim_authority(registration, auth_record, lock_record, out / 'manifest.json', mode)
    ledger.write_json(out / 'SHA256.json', value)
    value['sha256_file'] = ledger.file_sha(out / 'SHA256.json')
    _schema_check('live-trial', value)
    ledger.write_json(out / 'manifest.json', value)
    return value


def verify_trial(manifest_path, authorization_path=None, *, verifier=None, allow_mock=False):
    path = _safe(manifest_path)
    manifest = ledger.read_json(path)
    _schema_check('live-trial', manifest)
    if (manifest.get('schema') != MANIFEST_SCHEMA or manifest.get('freeze_dir') != str(path.parent)
            or path.name != 'manifest.json' or manifest.get('evidence_mode') not in ('live', 'unit_mock')):
        raise Stop('trial_manifest_contract')
    if manifest['evidence_mode'] == 'unit_mock' and not allow_mock:
        raise Stop('trial_mock_manifest_not_live_authorization')
    payload = path.parent / 'SHA256.json'
    if ledger.file_sha(payload) != manifest.get('sha256_file') or not _equal(
            ledger.read_json(payload), {k: v for k, v in manifest.items() if k != 'sha256_file'}):
        raise Stop('trial_sha_wrapper_mismatch')
    registration = ledger.read_json(_read_record(manifest['registration']))
    auth_path = _read_record(manifest['authorization'])
    if authorization_path is not None and _safe(authorization_path) != auth_path:
        raise Stop('trial_authorization_path_mismatch')
    auth = ledger.read_json(auth_path)
    _phase(registration)
    _authorize(auth, registration, manifest['registration'], manifest['integrated_lock'])
    if (not _equal(registration, manifest['registration_data']) or manifest['phase'] != registration['phase']
            or any(manifest[key] != registration[key] for key in ('trial_id', 'cycle_id'))
            or not _equal(manifest['reserved_calls'], reservations(registration))
            or not _equal(manifest['generators'], dict(holdout=dict(GENERATOR), benchmark=dict(GENERATOR), pilot=dict(ASTRA)))
            or not _equal(manifest['judge'], ASTRA)
            or os.environ.get('OMP_PROFILE') != manifest['omp_profile'] or auth['omp_profile'] != manifest['omp_profile']
            or auth['quota_snapshot'] != manifest['quota_snapshot'] or manifest['host'] != socket.gethostname()):
        raise Stop('trial_execution_identity_changed')
    _verify_authority(path, manifest)
    lock_path = _read_record(manifest['integrated_lock'])
    lock = (verifier or integrated.verify)(lock_path)
    if lock.get('schema') != integrated.SCHEMA or lock.get('authorization') is not None:
        raise Stop('trial_integrated_implementation_prerequisite')
    if not allow_mock:
        current = freezing._executable(manifest['omp']['omp'])
        if not _equal(current, manifest['omp']):
            raise Stop('trial_omp_identity_changed')
    if manifest['source_files'] != _source_files(registration):
        raise Stop('trial_source_files_changed')
    if manifest['public_bindings'] != _public_bindings(registration, manifest['source_files'], manifest['evidence_mode']):
        raise Stop('trial_public_commitment_changed')
    _bound_phase_inputs(registration, manifest['source_files'], manifest['integrated_lock'], allow_mock=allow_mock)
    return manifest, lock


class CapabilityBudget(Budget):
    """Signed C-D subcaps, separate from the unchanged original v3 budget."""
    def __init__(self, clock, *, max_calls=3, one_attempt=False, active_limit=1200):
        super().__init__(max_calls, clock=clock)
        self.deadline = self.started + min(1200, active_limit)
        self.stage_deadline = min(self.deadline, self.started + 600)
        self.one_attempt = one_attempt

    def cad(self):
        if self.one_attempt and self.attempts:
            raise Stop('trial_one_attempt_only')
        super().cad()

    def begin_repair(self):
        if self.one_attempt:
            raise Stop('trial_one_attempt_only')
        if self.attempts != 1 or self.counts['repair']:
            raise ValueError('repair_not_eligible')
        if self.deadline-self.clock() < 570:
            raise Stop('repair_time_reservation_lost')
        self.stage = 'repair'
        self.stage_deadline = min(self.deadline, self.clock()+600)

    def sol_timeout(self, purpose):
        cap = 180 if purpose == 'repair' else 60 if purpose == 'parse_repair' else 450
        reserve = 30
        if self.stage == 'repair':
            reserve = 330 + (60 if purpose == 'repair' and not self.counts['parse_repair'] else 0)
        return min(cap, self.remaining(reserve))

    def cad_timeout(self):
        return min(180 if self.stage == 'repair' else 450,
                   self.remaining(150 if self.stage == 'repair' else 30))

    def verification_timeout(self):
        return min(120 if self.stage == 'repair' else 300, self.remaining())

    def settings(self):
        return dict(max_calls=self.max_calls, max_cad_attempts=1 if self.one_attempt else 2,
                    parse_calls=1, repair_calls=0 if self.one_attempt else 1, deadline_s=1200,
                    initial_s=600, repair_s=600, cleanup_reserve_s=30, repair_sol_s=180,
                    repair_parse_s=60, repair_cad_s=180, repair_reimport_s=120)


class _CallGuard:
    def __init__(self, session, pool, record_id, maximum, kind):
        self.session, self.pool, self.record_id, self.maximum = session, pool, record_id, maximum
        self.key = (pool, record_id, kind)
        self._calls = 0

    @property
    def calls(self):
        return self._calls

    @calls.setter
    def calls(self, value):
        if value < self._calls:
            delta = self._calls-value
            self.session.charged[self.pool] -= delta
            self.session.record_calls[self.key] -= delta
        self._calls = value

    def check(self):
        return self.session.check()

    def before_call(self):
        self.check()
        key = self.key
        if (self.pool not in self.session.charged or self.session.charged[self.pool] >= self.session.manifest['reserved_calls'][self.pool]
                or self.session.record_calls.get(key, 0) >= self.maximum):
            self.session.stop_reason = 'budget_exhausted'
            raise Stop('budget_exhausted')
        self.session.charged[self.pool] += 1
        self.session.record_calls[key] = self.session.record_calls.get(key, 0)+1
        self._calls += 1
        return self.check()


class PlanExecution:
    def __init__(self, session, budget, pool, model, thinking, max_calls):
        self.session, self.budget, self.pool = session, budget, pool
        self.clock, self.mode = session.clock, session.mode
        self.model, self.thinking, self.max_calls = model, thinking, max_calls
        self._started_calls = session.charged[pool]
        self._started_attempts = session._attempt_sequence

    @property
    def live_calls(self):
        return self.session.charged[self.pool]-self._started_calls if self.mode == 'live' else 0

    @property
    def physical_attempts(self):
        return self.session._attempt_sequence-self._started_attempts if self.mode == 'live' else 0

    def check(self):
        self.session.check()

    def admitted_inputs(self, manifest):
        self.session.admitted_inputs(manifest)

    def error_status(self, error):
        return 'INCOMPLETE' if error in ('budget_exhausted', 'quota_stop') or str(error).startswith('quota_') else 'FAIL'


class TrialSession(AbstractContextManager):
    def __init__(self, manifest_path, authorization_path, run_dir, *, phase, process=None,
                 native_process=None, wall=None, sleep=None, verifier=None, validation_of=None):
        if verifier is not None and process is None:
            raise Stop('trial_test_verifier_requires_injected_transport')
        if native_process is not None and process is None:
            raise Stop('trial_injected_native_requires_injected_model_transport')
        self.process = process if process is not None else live.stream_process
        self._native_delegate = native_process if native_process is not None else live.stream_native_process
        self._real_native = native_process is None
        self.native_process = self._native
        self.wall = wall if wall is not None else live.WallClock()
        self.utc = getattr(self.wall, 'utc', ledger.utc)
        self.sleep = sleep if sleep is not None else time.sleep
        self.mode = 'live' if process is None else 'unit_mock'
        self.clock = agent.ActiveClock(self.wall)
        self.manifest_path = _safe(manifest_path)
        self.manifest, self.lock = verify_trial(self.manifest_path, authorization_path,
                                               verifier=verifier, allow_mock=process is not None)
        if self.manifest['phase'] != phase:
            raise Stop('trial_phase_mismatch')
        self.registration = self.manifest['registration_data']
        self.out = _safe(run_dir, regular=False)
        self.validation_of = _safe(validation_of, regular=False) if validation_of is not None else None
        self.validation_bindings = []
        claim_path = self.manifest_path.parent / 'execution-claim.json'
        if self.validation_of is None:
            with claim_path.open('x', encoding='utf-8') as file:
                json.dump(dict(manifest_sha256=ledger.file_sha(self.manifest_path), run_dir=str(self.out)), file)
        else:
            if phase != 'pilot':
                raise Stop('trial_validation_requires_original_pilot')
            claim = ledger.read_json(_safe(claim_path))
            summary_path = _safe(self.validation_of / 'summary.json')
            summary = ledger.read_json(summary_path)
            if (Path(claim.get('run_dir', '')) != self.validation_of
                    or claim.get('manifest_sha256') != ledger.file_sha(self.manifest_path)
                    or summary.get('schema') != 'cad-harness.pilot-trial.v1'
                    or summary.get('manifest_sha256') != ledger.file_sha(self.manifest_path)
                    or any(summary.get(key) != self.registration[key] for key in ('trial_id', 'cycle_id'))):
                raise Stop('trial_validation_original_handover_binding')
            self.validation_bindings = [_record(claim_path), _record(summary_path)]
        self.out = ledger.new_directory(self.out)
        self.journal = ledger.Journal(self.out / 'ledger.jsonl', self.out.name, 'live-'+phase,
                                      clock=self.wall, now=self.utc)
        self.journal.__enter__()
        self.charged = {name: 0 for name in self.manifest['reserved_calls']}
        self.record_calls, self.adjudicated, self._images = {}, set(), {}
        self._attempt_sequence = self._logical_sequence = 0
        self.native_cad_intervals = []
        self.fatal = None
        self.stop_reason = None
        self._released = False
        self._started = self.wall()
        self.event('run_started', evidence_mode=self.mode, live_calls=0,
                   manifest_sha256=ledger.file_sha(self.manifest_path), omp_profile=os.environ.get('OMP_PROFILE'),
                   validation_only=self.validation_of is not None)

    def __exit__(self, exc_type, exc_value, traceback):
        self.event('run_finished', wall_s=self.wall()-self._started, active_s=self.clock()-self._started,
                   stop_reason=self.stop_reason or self.fatal or (str(exc_value) if exc_value else None),
                   **self.summary())
        return self.journal.__exit__(exc_type, exc_value, traceback)

    def event(self, kind, **fields):
        return self.journal.append(kind, **fields)

    def _identity(self):
        verify_execution_claim(self.manifest_path, self.manifest,
                               run_dir=self.validation_of if self.validation_of is not None else self.out)
        for record in self.validation_bindings:
            _read_record(record)
        for record in self.manifest['public_bindings'].values():
            _read_record(record)
        for record in (self.manifest['registration'], self.manifest['authorization'], self.manifest['integrated_lock']):
            _read_record(record)
        if os.environ.get('OMP_PROFILE') != self.manifest['omp_profile']:
            raise Stop('trial_operator_profile_changed')
        if self.mode == 'live':
            if integrated._head(ROOT)['head'] != self.lock['git']['head'] or integrated._sources(ROOT) != self.lock['files']:
                raise Stop('trial_frozen_implementation_changed')
            if _record(self.manifest['omp']['omp'])['sha256'] != self.manifest['omp']['sha256']:
                raise Stop('trial_omp_identity_changed')
            current = _module('cad_verify_v4_runtime').native_files()
            if current != {path: record['sha256'] for path, record in self.lock['runtime']['files'].items()}:
                raise Stop('trial_native_inventory_changed')
        if self.manifest['source_files'] != _source_files(self.registration):
            raise Stop('trial_source_files_changed')

    def check(self):
        if self.fatal or self.stop_reason:
            raise Stop(self.fatal or self.stop_reason)
        try:
            self._identity()
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.fatal = self.stop_reason = str(exc)
            raise
        try:
            value = quota_snapshot(self.manifest['quota_snapshot'], datetime.fromisoformat(self.utc().replace('Z', '+00:00')))
        except Stop as exc:
            self.stop_reason = 'quota_stop'
            self.event('quota_checked', decision=str(exc), snapshot_path=self.manifest['quota_snapshot'])
            raise Stop('quota_stop') from exc
        self.event('quota_checked', **value)
        if value['decision'] != 'allow':
            self.stop_reason = 'quota_stop'
            raise Stop('quota_stop')
        return value

    def admitted_inputs(self, manifest):
        self.check()
        if manifest.get('evidence_mode') not in ('independent_dev', 'custodian'):
            raise Stop('trial_input_evidence_mode')

    def _release(self):
        if self._released:
            return
        self._identity()
        root = self.out / 'released'
        for name, record in self.manifest['source_files'].items():
            relative = self.registration['files'][name]['path']
            destination = root.joinpath(*relative.split('/'))
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if any(_record(destination)[key] != record[key] for key in ('sha256', 'bytes')):
                    raise Stop('trial_release_collision')
            else:
                with Path(record['path']).open('rb') as source, destination.open('xb') as output:
                    shutil.copyfileobj(source, output)
            if any(_record(destination)[key] != record[key] for key in ('sha256', 'bytes')):
                raise Stop('trial_release_binding_changed')
        self._released = True
        self.event('custody_released', files=len(self.manifest['source_files']), source_root_sha256=ledger.sha(
            json.dumps(self.manifest['source_files'], sort_keys=True).encode()))

    def path(self, file_id):
        if file_id not in self.registration['files']:
            raise Stop('trial_unknown_file_id')
        self._release()
        binding = self.registration['files'][file_id]
        path = self.out / 'released' / binding['path']
        if any(_record(path)[key] != binding[key] for key in ('sha256', 'bytes')):
            raise Stop('trial_released_file_changed')
        if binding['role'] == 'judge_image' or (self.manifest['phase'] == 'benchmark' and binding['role'] == 'original_asset'
                                               and path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp')):
            self._images[str(path)] = _record(path)
        return path

    def input_images(self, file_ids):
        if self.manifest['phase'] != 'benchmark':
            raise Stop('trial_original_images_benchmark_only')
        paths = []
        for identity in file_ids:
            if self.registration['files'].get(identity, {}).get('role') != 'original_asset':
                raise Stop('trial_original_asset_image_required')
            path = self.path(identity)
            if str(path) not in self._images:
                raise Stop('trial_original_asset_image_required')
            paths.append(str(path))
        return tuple(paths)

    def release_entry(self, entry):
        return {key: self.path(entry[key]) for key in ('request', 'input_manifest', 'prepared', 'card', 'context') if key in entry}

    def _native(self, argv, captures, *, cwd, timeout):
        start = self.wall()
        try:
            code = self._native_delegate(argv, captures, cwd=cwd, timeout=timeout)
            if self._real_native:
                native = getattr(captures['stdout'], 'native_evidence', None)
                job = ledger.read_json(Path(argv[argv.index('--job')+1]))
                output = Path(job['out']) / ('verify-result.json' if job['operation'] == 'verify' else 'result.json')
                result = ledger.read_json(output)
                if (not isinstance(native, dict) or native.get('cleanup_status') != 'exited'
                        or not native.get('owned_pid') or native['owned_pid'] != result.get('owned_pid')
                        or result.get('gui_up') != 0 or result.get('document_closed') is not True):
                    raise Stop('trial_native_cleanup_evidence_missing')
            return code
        except BaseException as exc:
            self.fatal = 'trial_native_interrupted:' + type(exc).__name__ + ':' + str(exc)
            raise
        finally:
            end = self.wall()
            interval = dict(start=start, end=end, wall_s=end-start, operation='native_cad')
            self.native_cad_intervals.append(interval)
            self.event('native_interval', **interval)

    def _call_registration(self, record_id, pool, purpose, maximum):
        if not isinstance(record_id, str):
            raise Stop('trial_unregistered_record_or_purpose')
        judging = purpose == 'judge'
        phase = self.manifest['phase']
        if judging and maximum != 1:
            raise Stop('trial_judge_exactly_one_slot')
        if phase in ('pilot', 'judge'):
            allowed = {entry['id'] for entry in self.registration['entries']}
            valid = record_id in allowed and pool == ('pilot' if phase == 'pilot' else 'judge')
            valid = valid and (phase != 'judge' or judging)
        elif phase == 'families':
            allowed = {entry['id']: entry['family'] for entry in self.registration['entries']}
            valid = record_id in allowed and pool == allowed.get(record_id, '') + (':judge' if judging else ':generation')
        else:
            allowed = {entry['id'] for entry in self.registration['pairs']}
            if judging:
                identity, _, arm = record_id.rpartition(':')
                valid = identity in allowed and arm in ('bare', 'with_harness') and pool == 'benchmark:judge'
            elif pool == 'bare:generation':
                valid = record_id.endswith(':bare') and record_id[:-5] in allowed
            else:
                valid = pool == 'with_harness:generation' and record_id in allowed
        if not valid:
            raise Stop('trial_unregistered_record_or_purpose')

    def call(self, record_id, request, runtime_data, *, pool, model, thinking, skill=b'', purpose='source',
             timeout=450, max_calls=3, images=()):
        if self.validation_of is not None:
            raise Stop('trial_validation_cannot_call_model')
        self._call_registration(record_id, pool, purpose, max_calls)
        expected = ASTRA if purpose == 'judge' or self.manifest['phase'] == 'pilot' else GENERATOR
        if dict(model=model, thinking=thinking) != expected:
            raise Stop('trial_model_identity_drift')
        if not isinstance(request, str) or not isinstance(runtime_data, dict) or type(max_calls) is not int or not 1 <= max_calls <= 3:
            raise Stop('trial_model_call_contract')
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise Stop('trial_model_timeout_contract')
        ceiling = (1200 if self.manifest['phase'] == 'benchmark' and pool == 'bare:generation'
                   and purpose == 'bare_tools' else 300 if purpose == 'judge' else 450)
        timeout = min(timeout, ceiling)
        if pool not in self.charged:
            raise Stop('trial_reservation_pool_unknown')
        for image in images:
            path = _safe(image)
            if str(path) not in self._images or _record(path) != self._images[str(path)]:
                raise Stop('trial_unregistered_image_evidence')
        folder = ledger.new_directory(self.out / 'calls' / ('call-%04d' % (self._logical_sequence+1)))
        transport_manifest = dict(generator=dict(self.manifest['omp'], model=model, thinking=thinking),
                                  manifest_sha256=ledger.file_sha(self.manifest_path))
        guard = _CallGuard(self, pool, record_id, max_calls, 'judge' if purpose == 'judge' else 'generation')
        transport = live.LiveTransport(transport_manifest, self.journal, folder, request, skill, guard,
                                       wall=self.wall, process=self.process, sleep=self.sleep,
                                       prompt_files=tuple(str(_safe(image)) for image in images))
        transport.clock = self.clock
        transport.driver_reserves = False
        transport.sequence = self._attempt_sequence
        transport.logical_call = self._logical_sequence
        transport.episode, transport.route, transport.scored = record_id, 'source', True
        last = folder / 'last.txt'
        context = json.dumps(agent.MARKER + json.dumps(runtime_data, ensure_ascii=False), ensure_ascii=False)
        argv = [self.manifest['omp']['omp'], 'exec', '-o', str(last), 'developer_instructions='+context, request]
        try:
            result = transport(argv, cwd=folder, timeout=timeout)
            if result.returncode != 0 or not last.is_file():
                raise Stop('trial_model_response_failed')
            return last.read_bytes().decode('utf-8')
        finally:
            if transport.fatal:
                self.fatal = transport.fatal
            if transport.sequence == self._attempt_sequence and guard.calls:
                guard.calls = 0
            self._attempt_sequence = transport.sequence
            self._logical_sequence = transport.logical_call

    def execute_plan(self, entry, out, *, pool, model, thinking, max_calls=3, one_attempt=False, active_limit=1200):
        out = _safe(out, regular=False)
        out.parent.mkdir(parents=True, exist_ok=True)
        begin = len(self.native_cad_intervals)
        value = dict(status='UNVERIFIED', stop_reason=None, error=None, driver_result=None,
                     artifact_verdict=None, artifact_bundle=None, first_handover=None,
                     native_cad_intervals=[], images=[], checkpoint=str(out.parent / (out.name+'-execution.json')))
        try:
            budget = CapabilityBudget(self.clock, max_calls=max_calls, one_attempt=one_attempt, active_limit=active_limit)
            paths = self.release_entry(entry)
            profile = entry['profile']
            execution = PlanExecution(self, budget, pool, model, thinking, max_calls)
            skill = agent.bundle(ROOT, profile=profile)
            def generate(request, data, *, purpose, timeout):
                return self.call(entry['id'], request, data, pool=pool, model=model, thinking=thinking,
                                 skill=skill, purpose=purpose, timeout=timeout, max_calls=max_calls)
            result, _ = s1.request(paths['request'], paths['card'], out,
                                   manifest_path=paths['input_manifest'], prepared_path=paths['prepared'],
                                   model=generate, process=self.native_process, profile=profile, execution=execution)
            value.update(status=result['status'], driver_result=result, stop_reason=result.get('stop_reason'),
                         error=result.get('stop_reason'))
            ledger.write_json(out.parent / (out.name+'-driver.json'), result)
            candidate = result.get('result') or {}
            source = candidate.get('candidate_dir')
            compiled = candidate.get('compile') or {}
            if source and compiled.get('status') == 'PASS':
                artifacts = _module('cad_verify_v4_worker')._artifacts(Path(source))
                approved = {'tools.'+name: ROOT / 'tools' / (name+'.py') for name in
                            ('cad_verify_v4_compile', 'cad_verify_v4_s2_edit', 'cad_verify_v4_s3_rebuild')}
                modules = compiled['restoration_modules']
                if not isinstance(modules, list) or len(modules) != len(set(modules)) or any(name not in approved for name in modules):
                    raise Stop('trial_unfrozen_native_restoration')
                extensions = [dict(module=name, **_record(approved[name])) for name in modules]
                bundle = dict(schema='cad-harness.artifact-bundle.v4', profile=profile, evidence_mode=self.mode,
                              native=artifacts['native'], step=artifacts['step'],
                              output_object=compiled['output_object'], probes=compiled['artifact_probes'], extensions=extensions)
                bundle_path = out / 'artifacts.json'
                ledger.write_json(bundle_path, bundle)
                value['artifact_bundle'] = str(bundle_path)
                value['first_handover'] = dict(monotonic=self.wall(), attempt=1, cad_attempt=budget.attempts,
                    status='UNVERIFIED', artifact_bundle_sha256=ledger.file_sha(bundle_path),
                    critical_dimension_error=None, fabrication=None, qualified=False)
                ledger.write_json(out.parent / (out.name+'-handover.json'),
                                  dict(first_handover=value['first_handover'], artifact_bundle=str(bundle_path)))
                self.event('first_handover', record_id=entry['id'], **value['first_handover'])
                checked = self.check_artifacts(entry, bundle_path, out / 'neutral', timeout=budget.remaining())
                value['artifact_verdict'] = checked
                value['status'] = checked['status'] if result['status'] == 'PASS' else result['status']
                value['first_handover'].update(status=value['status'], qualified=value['status'] == 'PASS')
                self.event('handover_checked', record_id=entry['id'], first_handover=value['first_handover'],
                           artifact_verdict=checked)
                value['images'] = self.capture_images(entry, value, out / 'images', timeout=budget.remaining())
        except BaseException as exc:
            reason = str(exc) or type(exc).__name__
            incomplete = reason == 'budget_exhausted' or reason.startswith('quota_')
            status = 'INCOMPLETE' if incomplete else 'INTERRUPTED' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'ERROR'
            value.update(status=status, stop_reason='quota_stop' if reason.startswith('quota_') else reason,
                         error=dict(type=type(exc).__name__, message=reason))
            if incomplete:
                self.stop_reason = value['stop_reason']
            else:
                self.fatal = reason
            self.event('execution_error', record_id=entry['id'], status=status, error=value['error'],
                       driver_retained=value['driver_result'] is not None, first_handover=value['first_handover'])
        if self.fatal or self.stop_reason:
            value['stop_reason'] = self.fatal or self.stop_reason
            if value['status'] == 'PASS':
                value['status'] = 'ERROR' if self.fatal else 'INCOMPLETE'
        value['native_cad_intervals'] = list(self.native_cad_intervals[begin:])
        ledger.write_json(value['checkpoint'], value)
        return value


    def check_artifacts(self, entry, artifact_bundle, out, *, timeout=300):
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise Stop('episode_stage_deadline_exceeded')
        paths = self.release_entry(entry)
        self.check()
        _, _, extensions = _module('cad_verify_v4_artifacts').load_bundle(artifact_bundle, profile=entry['profile'])
        approved = {'tools.'+name: ROOT / 'tools' / (name+'.py') for name in
                    ('cad_verify_v4_compile', 'cad_verify_v4_s2_edit', 'cad_verify_v4_s3_rebuild')}
        if any(name not in approved or path != approved[name] for name, path in extensions.items()):
            raise Stop('trial_unfrozen_native_restoration')
        return _module('cad_verify_v4_artifacts').check(paths['input_manifest'], paths['prepared'], paths['card'],
                  paths['context'], artifact_bundle, out, profile=entry['profile'], process=self.native_process,
                  timeout=min(300, timeout), execution=self)

    def capture_images(self, entry, result, out, *, timeout=300):
        bundle_path = result.get('artifact_bundle')
        if not bundle_path:
            return []
        bundle = ledger.read_json(_safe(bundle_path))
        step = bundle['step']
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise Stop('episode_stage_deadline_exceeded')
        rendered = s1.native_work('render-evidence', Path(out), self.journal, profile=entry['profile'],
                                  process=self.native_process, timeout=min(300, timeout), step=step,
                                  settings=_module('cad_verify_v4_render').SETTINGS)
        paths = []
        if rendered.get('status') != 'PASS':
            return paths
        for record in rendered.get('images', []):
            path = _read_record(record)
            self._images[str(path)] = _record(path)
            paths.append(str(path))
        self.event('visual_evidence_registered', record_id=entry['id'], step=step,
                   renderer_sha256=ledger.file_sha(ROOT / 'tools/cad_verify_v4_render.py'), images=[self._images[p] for p in paths])
        return paths

    def judge(self, record_id, request, deterministic, rubric, *, pool, images=()):
        if record_id in self.adjudicated:
            raise Stop('trial_favorable_rescore_forbidden')
        self.adjudicated.add(record_id)
        return _module('cad_verify_v4_model_judge').adjudicate(self, record_id, request, deterministic, rubric,
                                                              pool=pool, images=images)

    def summary(self):
        charged = sum(self.charged.values())
        return dict(evidence_mode=self.mode, charged_calls=dict(self.charged), logical_calls=charged,
                    physical_attempts=self._attempt_sequence, live_calls=charged if self.mode == 'live' else 0,
                    omp_profile=os.environ.get('OMP_PROFILE'), final_v4_ready=False)
