"""Supervised, three-invocation bare construction with a real Windows boundary.

The model gets only the verbatim original request, original asset inventory and
this generic tool wire protocol. No checker result is returned to construction.
The collector copies bytes; it never runs submitted source or creates CAD.
"""
import base64
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import uuid

if __package__:
    from . import cad_verify_v4_bare_windows as isolation
else:
    import cad_verify_v4_bare_windows as isolation

MODEL = 'openai-codex/gpt-6.1-sol'
THINKING = 'xhigh'
ACTIVE_LIMIT = 1200
MAX_CALLS = 3
HOST_INIT_PREFIX = 'FREECAD_HOST_INIT='
PYTHON_BOOTSTRAP = chr(10).join([
    "import sys as _sys, os as _os, runpy as _runpy, json as _json",
    # LPAC redirects the native temp API below scratch, but does not create it.
    # FreeCAD's C++ temp_directory_path requires that directory during import.
    "import ctypes as _ct, pathlib as _paths",
    "_get_temp = _ct.WinDLL('kernel32', use_last_error=True).GetTempPathW",
    "_get_temp.argtypes = [_ct.c_uint32, _ct.c_wchar_p]",
    "_get_temp.restype = _ct.c_uint32",
    "_temp_buffer = _ct.create_unicode_buffer(32768)",
    "_temp_length = _get_temp(len(_temp_buffer), _temp_buffer)",
    "if not 0 < _temp_length < len(_temp_buffer):",
    "    raise OSError('bare_native_temp_path_unavailable')",
    "_temp = _paths.Path(_temp_buffer.value)",
    "if not _temp.is_absolute():",
    "    raise RuntimeError('bare_native_temp_path_not_absolute')",
    "_temp = _temp.resolve()",
    "if not _temp.is_relative_to(_paths.Path(_os.getcwd()).resolve()):",
    "    raise RuntimeError('bare_native_temp_path_outside_scratch')",
    "_temp.mkdir(parents=True, exist_ok=True)",
    "__import__('FreeCAD')",
    "_version = list(__import__('FreeCAD').Version()[:3])",
    "_gui = bool(__import__('FreeCAD').GuiUp)",
    "assert _version == ['1','1','4'] and not _gui",
    "_nonce, _args = _sys.argv[1], _sys.argv[2:]",
    "_sys.stderr.write(chr(10) + 'FREECAD_HOST_INIT=' + _nonce + ':' + _json.dumps({'schema':'freecad.host-init.v1','version':_version,'gui_up':_gui}) + chr(10))",
    "_sys.stderr.flush()",
    "_sys.path.insert(0, _os.getcwd())",
    "if _args[0] == '-c':",
    "    _sys.argv = ['-c'] + _args[2:]",
    "    exec(compile(_args[1], '<string>', 'exec'), {'__name__':'__main__'})",
    "elif _args[0] == '-m':",
    "    _sys.argv = _args[1:]",
    "    _runpy.run_module(_args[1], run_name='__main__', alter_sys=True)",
    "else:",
    "    _sys.argv = _args",
    "    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(_args[0])))",
    "    _runpy.run_path(_args[0], run_name='__main__')"])
BOOTSTRAP_SHA256 = hashlib.sha256(PYTHON_BOOTSTRAP.encode('utf-8')).hexdigest()


PROTOCOL = {
    'schema': 'cad-harness.bare-actions.v1',
    'response': {'actions': ['write(path,content_base64)', 'read(path)', 'list(path)',
                             'python(args)', 'shell(command)'],
                 'handover': 'null or {native,step,source:[paths],extensions:[],output_object,probes,final?:boolean}'},
    'rules': ['Return one JSON object with actions and handover only.',
              'Paths are relative to scratch. Original inputs are in inputs/ (read-only).',
              'python initializes pinned isolated FreeCAD 1.1.4/Python before user code.',
              'python args: [-c,code,...], [-m,module,...], or [relative_script,...]. No modeling names/helpers are injected.',
              'shell is Windows cmd built-ins only; OS child-process creation is disabled.',
              'No network, packages, GUI, external processes or external files are available.',
              'External drive-volume queries are denied. cmd del requires them; use self-authored Python for scratch-file deletion.',
              'At most three model responses total, including all continuations.',
              'A response may execute actions and immediately hand over their outputs.',
              'Submit ordinary model.FCStd and model.step plus reproducible source/dependencies.',
              'Handovers are immutable. final defaults true; false allows remaining responses, without checker feedback.',
              'A final:false handover needs a terminal handover within the same three responses.',
              'Python restoration extensions are not accepted; use ordinary native features. No fourth response.']}


def _dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _record(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=isolation.file_hash(path))


def _relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('bare_relative_path')
    path = PurePosixPath(value)
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if (path.is_absolute() or path.as_posix() != value or
            any(p in ('..', '.') or p.endswith((' ', '.')) or p.split('.')[0].upper() in reserved or
                any(ord(c) < 32 or c in '*?<>|\"' for c in p) for p in value.split('/'))):
        raise ValueError('bare_relative_path')
    return path


def scoped(root, value, *, write=False):
    relative = _relative(value)
    if write and relative.parts[0].casefold() == 'inputs':
        raise ValueError('bare_inputs_read_only')
    path = Path(root).joinpath(*relative.parts)
    for candidate in (path, *path.parents):
        if candidate.exists() and (candidate.is_symlink() or getattr(candidate.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('bare_reparse_path')
        if candidate.is_file() and candidate.stat().st_nlink > 1:
            raise ValueError('bare_hardlink_path')
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('bare_path_escape')
    return path


def validate_runtime(session, config):
    """Admit only the frozen byte-equivalent private copy, never installed ACLs."""
    if not isinstance(config, dict) or set(config) != {'root', 'inventory', 'staging_proof'}:
        raise ValueError('bare_staged_runtime_configuration_required')
    runtime = Path(config['root'])
    inventory_path, proof_path = (session.path(config[key]) for key in ('inventory', 'staging_proof'))
    if any(path.resolve().is_relative_to(runtime.resolve()) for path in (inventory_path, proof_path)):
        raise ValueError('bare_staging_evidence_must_be_external')
    inventory = json.loads(inventory_path.read_bytes())
    proof = json.loads(proof_path.read_bytes())
    return isolation.validate_staged_runtime(runtime, inventory, proof)


def parse_actions(response):
    value = json.loads(response, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('bare_nonfinite_json')))
    if not isinstance(value, dict) or set(value) != {'actions', 'handover'} or not isinstance(value['actions'], list):
        raise ValueError('bare_action_envelope')
    for action in value['actions']:
        if not isinstance(action, dict) or action.get('kind') not in ('write', 'read', 'list', 'python', 'shell'):
            raise ValueError('bare_action_kind')
        expected = {'write': {'kind', 'path', 'content_base64'}, 'read': {'kind', 'path'},
                    'list': {'kind', 'path'}, 'python': {'kind', 'args'}, 'shell': {'kind', 'command'}}[action['kind']]
        if set(action) != expected:
            raise ValueError('bare_action_fields')
    return value


class ToolLoop:
    def __init__(self, session, scratch, boundary, out, remaining, record_id, originals=()):
        self.session, self.scratch, self.boundary, self.out = session, Path(scratch), boundary, Path(out)
        self.remaining, self.serial = remaining, 0
        self.native_intervals, self.tool_intervals = [], []
        self.record_id = record_id
        self.originals = tuple(originals)
        self.unverified_native_intervals = []

    def verify_originals(self):
        for record in self.originals:
            try:
                path = scoped(self.scratch, record['name'])
                actual = _record(path)
            except (OSError, ValueError) as exc:
                raise isolation.BoundaryUnavailable('bare_original_input_unavailable') from exc
            if any(actual[key] != record[key] for key in ('sha256', 'bytes')):
                raise isolation.BoundaryUnavailable('bare_original_input_changed')

    def execute(self, action):
        self.session.check()
        self.verify_originals()
        if self.remaining() <= 0:
            raise TimeoutError('bare_active_limit')
        self.serial += 1
        start = self.session.wall()
        result = None
        error = None
        try:
            result = self._perform(action)
            self.verify_originals()
            if self.remaining() <= 0:
                raise TimeoutError('bare_active_limit')
            if action['kind'] in ('python', 'shell'):
                # Custodian stream paths/host repository names never enter
                # the model continuation; full receipts stay in the journal.
                return {k: result[k] for k in ('returncode', 'stdout_base64', 'stderr_base64')}
            return result
        except Exception as exc:
            error = type(exc).__name__ + ':' + str(exc)
            raise
        finally:
            end = self.session.wall()
            self.tool_intervals.append([start, end])
            self.session.event('bare_tool', record_id=self.record_id, operation_id=self.record_id + ':tool-%03d' % self.serial,
                               action=action, result=result, error=error, start=start, end=end)

    def _python_argv(self, args):
        if (not isinstance(args, list) or not args or
                not all(isinstance(a, str) and '\0' not in a for a in args)):
            raise ValueError('bare_python_args')
        if args[0] in ('-c', '-m'):
            if len(args) < 2:
                raise ValueError('bare_python_entry_required')
            if args[0] == '-m' and not all(part.isidentifier() for part in args[1].split('.')):
                raise ValueError('bare_python_module')
        elif args[0].startswith('-'):
            raise ValueError('bare_python_entry_mode')
        else:
            scoped(self.scratch, args[0])
        nonce = uuid.uuid4().hex
        return [str(self.boundary.python), '-I', '-B', '-u', '-c', PYTHON_BOOTSTRAP, nonce, *args], nonce

    @staticmethod
    def _initialization(path, nonce):
        if not Path(path).is_file():
            return None
        prefix = (HOST_INIT_PREFIX + nonce + ':').encode('ascii')
        messages = [line[len(prefix):] for line in Path(path).read_bytes().splitlines() if line.startswith(prefix)]
        if len(messages) != 1:
            return None
        try:
            value = json.loads(messages[0])
        except (ValueError, UnicodeError):
            return None
        if value != {'schema': 'freecad.host-init.v1', 'version': ['1', '1', '4'], 'gui_up': False}:
            return None
        return dict(value, bootstrap_sha256=BOOTSTRAP_SHA256)

    def _perform(self, action):
        kind = action['kind']
        if kind == 'write':
            path = scoped(self.scratch, action['path'], write=True)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(action['content_base64'], validate=True))
            return {'written': action['path'], 'sha256': isolation.file_hash(path)}
        if kind == 'read':
            path = scoped(self.scratch, action['path'])
            return {'path': action['path'], 'content_base64': base64.b64encode(path.read_bytes()).decode('ascii')}
        if kind == 'list':
            path = self.scratch if action['path'] == '' else scoped(self.scratch, action['path'])
            return {'paths': sorted(p.relative_to(self.scratch).as_posix() for p in path.iterdir())}
        nonce = None
        if kind == 'python':
            argv, nonce = self._python_argv(action['args'])
        else:
            if not isinstance(action['command'], str) or '\0' in action['command']:
                raise ValueError('bare_shell_command')
            argv = [str(Path(os.environ['SystemRoot']) / 'System32/cmd.exe'), '/d', '/s', '/c', action['command']]
        prefix = self.out / ('tool-%03d' % self.serial)
        start = self.session.wall()
        try:
            result = self.boundary.run(argv, stdout=prefix.with_suffix('.stdout'), stderr=prefix.with_suffix('.stderr'), timeout=self.remaining())
        finally:
            end = self.session.wall()
            initialization = self._initialization(prefix.with_suffix('.stderr'), nonce) if kind == 'python' else None
            if kind == 'python':
                (self.native_intervals if initialization else self.unverified_native_intervals).append([start, end])
            streams = {key: _record(prefix.with_suffix('.' + key)) for key in ('stdout', 'stderr') if prefix.with_suffix('.' + key).is_file()}
            self.session.event('bare_process_stopped', record_id=self.record_id, command=argv, start=start, end=end,
                               receipt=getattr(self.boundary, 'last_receipt', None),
                               streams=streams, initialization=initialization,
                               native_metric='initialized_pinned_freecad_python_host_process_wall' if initialization else None,
                               native_metric_missing_reason='freecad_host_initialization_unverified' if kind == 'python' and not initialization else None)
        if self.session.mode != 'unit_mock' and (
                result.get('lpac_token_verified') is not True or not isolation.registry_read_token_scope(result)):
            raise isolation.BoundaryUnavailable('bare_registry_read_only_receipt_required')
        if kind == 'python' and initialization is None:
            raise isolation.BoundaryUnavailable('freecad_host_initialization_unverified')
        result['initialization'] = initialization
        for key in ('stdout', 'stderr'):
            result[key + '_record'] = _record(result[key])
            result[key + '_base64'] = base64.b64encode(Path(result[key]).read_bytes()).decode('ascii')
        return result


def collect(scratch, handover, out, *, profile, evidence_mode='independent_dev'):
    """Copy and hash an explicit handover, without build/import/repair/reopen."""
    expected = {'native', 'step', 'source', 'extensions', 'output_object', 'probes'}
    if not isinstance(handover, dict) or set(handover) not in (expected, expected | {'final'}) or not isinstance(handover.get('final', True), bool):
        raise ValueError('bare_handover_fields')
    if Path(handover['native']).name != 'model.FCStd' or Path(handover['step']).name != 'model.step':
        raise ValueError('bare_handover_native_step_names')
    if not isinstance(handover['source'], list) or not handover['source']:
        raise ValueError('bare_reproducible_source_required')
    if not isinstance(handover['extensions'], list) or not isinstance(handover['probes'], list):
        raise ValueError('bare_handover_dependencies')
    if evidence_mode not in ('independent_dev', 'unit_mock', 'live'):
        raise ValueError('bare_handover_evidence_mode')
    names = [handover['native'], handover['step'], *handover['source']]
    for extension in handover['extensions']:
        if set(extension) != {'module', 'path'}:
            raise ValueError('bare_extension_fields')
        names.append(extension['path'])
    folded = {}
    for name in names:
        key = _relative(name).as_posix().casefold()
        if key in folded and folded[key] != name:
            raise ValueError('bare_handover_case_insensitive_alias_collision')
        folded[key] = name
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    submitted = out / 'submitted'
    submitted.mkdir()
    copied = {}
    for name in dict.fromkeys(names):
        original = scoped(scratch, name)
        if not original.is_file() or _relative(name).parts[0].casefold() == 'inputs':
            raise ValueError('bare_handover_generated_file_required')
        target = submitted.joinpath(*_relative(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with original.open('rb') as source, target.open('xb') as destination:
            shutil.copyfileobj(source, destination)
        copied[name] = _record(target)
    bundle = dict(schema='cad-harness.artifact-bundle.v4', profile=profile, evidence_mode=evidence_mode,
                  native=copied[handover['native']], step=copied[handover['step']],
                  extensions=[dict(module=e['module'], **copied[e['path']]) for e in handover['extensions']],
                  output_object=handover['output_object'], probes=handover['probes'])
    bundle_path = out / 'bundle.json'
    with bundle_path.open('x', encoding='utf-8') as metadata:
        metadata.write(_dump(bundle))
    return {'artifact_bundle': str(bundle_path), 'files': copied, 'bundle': _record(bundle_path),
            'reproducible_source': [copied[name] for name in handover['source']]}


def construct(session, entry, out, *, boundary_factory=None, active_limit=ACTIVE_LIMIT):
    """A unit-mock boundary must be explicit and is never usable in live mode."""
    if boundary_factory is not None and session.mode != 'unit_mock':
        raise ValueError('bare_boundary_injection_live_forbidden')
    if isinstance(active_limit, bool) or not isinstance(active_limit, (int, float)) or not 0 < active_limit <= ACTIVE_LIMIT:
        raise ValueError('bare_signed_active_limit')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    scratch = isolation.create_scratch(out / 'scratch')
    inputs = scratch / 'inputs'
    inputs.mkdir()
    start, active_start = session.wall(), session.clock()
    accounting_before = session.summary()
    runtime = validate_runtime(session, session.registration['bare_runtime']) if boundary_factory is None else Path('DEV-runtime')
    originals = []
    inventory = []
    for item in entry['original_assets']:
        name = _relative(item['name'])
        target = inputs.joinpath(*name.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        original = session.path(item['file'])
        shutil.copyfile(original, target)
        originals.append(target)
        inventory.append(dict(name='inputs/' + name.as_posix(), **{k: v for k, v in _record(target).items() if k != 'path'}))
    request = session.path(entry['request']).read_bytes().decode('utf-8')
    request_record = _record(session.path(entry['request']))
    remaining = lambda: min(active_limit - (session.clock() - active_start),
                            300 - (session.wall() - first['at_wall']) if first is not None else math.inf)
    factory = boundary_factory or isolation.WindowsBoundary
    boundary_options = dict(read_files=originals, wall=session.wall)
    if boundary_factory is None:
        config = session.registration['bare_runtime']
        boundary_options.update(
            runtime_inventory=json.loads(session.path(config['inventory']).read_bytes()),
            staging_proof=json.loads(session.path(config['staging_proof']).read_bytes()))
    first = final = None
    handovers = []
    calls, native_intervals, tool_intervals, reason = 0, [], [], None
    status = 'unsubmitted'
    transcript = []
    finished, last_protocol_error = False, None
    loop = None
    boundary = None
    boundary_identity = {'mode': 'unit_mock' if boundary_factory is not None else isolation.REGISTRY_READ_ISOLATION,
                         'enforcement_verified': False, 'cleanup_status': 'not_entered',
                         'capability_count': None, 'capability_sids': None, 'capability_attributes': None}
    try:
        # inputs/ receives no inherited write permission: ACLs are explicit.
        with factory(scratch, runtime, **boundary_options) as boundary:
            boundary_identity.update(profile=getattr(boundary, 'name', None), cleanup_status='pending')
            if boundary_factory is None:
                boundary_identity['software'] = dict(
                    expected_freecad_version='1.1.4', bootstrap_sha256=BOOTSTRAP_SHA256,
                    source_python=str(isolation.PINNED_PYTHON), relocated_python=str(boundary.python),
                    source_python_sha256=boundary_options['runtime_inventory']['source_python']['sha256'],
                    relocated_python_sha256=isolation.file_hash(boundary.python),
                    runtime_inventory_sha256=isolation.file_hash(session.path(session.registration['bare_runtime']['inventory'])),
                    runtime_staging_proof_sha256=isolation.file_hash(session.path(session.registration['bare_runtime']['staging_proof'])),
                    software_environment_preparation=boundary_options['staging_proof'])
            loop = ToolLoop(session, scratch, boundary, out, remaining, entry['id'] + ':bare', inventory)
            if boundary_factory is None:
                # This real child validates LPAC/token/job admission before the
                # first model call. It derives no task facts or geometry.
                bootstrap = chr(10).join(['import FreeCAD as A',
                    'assert tuple(A.Version()[:3]) == ("1","1","4") and not A.GuiUp',
                    'try:', '    open(' + repr(str(Path(__file__).resolve())) + ', "rb").close()',
                    'except OSError:', '    pass',
                    'else:', '    raise RuntimeError("harness_repository_visible")',
                    'print("BARE_OFFLINE_READY")'])
                ready = loop.execute({'kind': 'python', 'args': ['-c', bootstrap]})
                if ready['returncode'] != 0:
                    raise isolation.BoundaryUnavailable('pinned_headless_runtime_preflight_failed')
                boundary_identity['enforcement_verified'] = True
            for turn in range(MAX_CALLS):
                if remaining() <= 0:
                    raise TimeoutError('bare_active_limit')
                session.check()
                loop.verify_originals()
                runtime_data = {'protocol': PROTOCOL, 'assets': inventory, 'history': transcript,
                                'responses_remaining': MAX_CALLS - turn}
                response = session.call(entry['id'] + ':bare', request, runtime_data,
                    pool='bare:generation', model=MODEL, thinking=THINKING, skill=b'',
                    purpose='bare_tools', timeout=remaining(), max_calls=MAX_CALLS,
                    images=session.input_images(entry.get('original_images', [])))
                calls += 1
                if remaining() <= 0:
                    raise TimeoutError('bare_active_limit')
                try:
                    batch = parse_actions(response)
                except (ValueError, TypeError) as exc:
                    last_protocol_error = type(exc).__name__ + ':' + str(exc)
                    transcript.append({'assistant': response, 'tool_results': [{'error': 'invalid_action_batch'}]})
                    session.event('bare_protocol_error', record_id=entry['id'] + ':bare', turn=turn + 1, error=last_protocol_error)
                    continue
                last_protocol_error = None
                results = []
                for action in batch['actions']:
                    try:
                        results.append(loop.execute(action))
                    except TimeoutError:
                        raise
                    except (OSError, ValueError) as exc:
                        results.append({'error': type(exc).__name__, 'operation': action['kind'],
                                        'path': action.get('path'), 'reason': 'tool_action_failed'})
                transcript.append({'assistant': response, 'tool_results': results})
                if batch['handover'] is not None:
                    handover = dict(at_wall=session.wall(), at_active=session.clock(), turn=turn + 1,
                                    declaration=batch['handover'], collection_status='pending', artifact_bundle=None)
                    if first is None:
                        first = handover
                        session.event('first_handover_declared', record_id=entry['id'] + ':bare', **handover)
                    final = handover
                    handovers.append(handover)
                    collected = collect(scratch, batch['handover'], out / ('handover-%d' % (turn + 1)),
                                        profile=entry['profile'], evidence_mode=session.mode)
                    handover.update(collected, collection_status='collected')
                    if remaining() <= 0:
                        raise TimeoutError('bare_active_or_correction_limit')
                    session.event('handover', record_id=entry['id'] + ':bare', **handover)
                    status = 'in_progress'
                    if batch['handover'].get('final', True):
                        status, finished = 'submitted', True
                        break
            native_intervals, tool_intervals = loop.native_intervals, loop.tool_intervals
            if not finished:
                status = 'invalid_response' if last_protocol_error else 'unsubmitted'
                reason = last_protocol_error or 'no_terminal_handover_within_three_invocations'
        boundary_identity['cleanup_status'] = 'restored' if boundary_factory is None else 'unit_mock'
        if remaining() <= 0:
            raise TimeoutError('bare_active_limit_after_owned_cleanup')
    except (Exception, KeyboardInterrupt) as exc:
        reason = type(exc).__name__ + ':' + str(exc)
        status = ('timed_out' if isinstance(exc, TimeoutError) else
                  'interrupted' if isinstance(exc, KeyboardInterrupt) else 'construction_error')
        if final is not None and final['collection_status'] == 'pending':
            final.update(collection_status='failed', collection_error=reason)
    if boundary_factory is None and boundary is not None:
        receipt = getattr(boundary, 'last_receipt', None)
        if isinstance(receipt, dict):
            boundary_identity.update({key: receipt.get(key) for key in
                ('capability_count', 'capability_sids', 'capability_attributes')})
    if loop is not None:
        native_intervals, tool_intervals = loop.native_intervals, loop.tool_intervals
    end, active_end = session.wall(), session.clock()
    accounting_after = session.summary()
    charged = accounting_after['charged_calls']['bare:generation'] - accounting_before['charged_calls']['bare:generation']
    physical = accounting_after['physical_attempts'] - accounting_before['physical_attempts']
    session.event('bare_construction_stopped', record_id=entry['id'] + ':bare', status=status,
                  reason=reason, start=start, end=end, active_start=active_start, active_end=active_end,
                  first_handover=first, final_handover=final, boundary=boundary_identity)
    return dict(status=status, reason=reason, first_handover=first, final_handover=final,
                artifact_bundle=final['artifact_bundle'] if final else None,
                start=start, end=end, active_start=active_start, active_end=active_end,
                calls=charged, physical_attempts=physical, responses_received=calls,
                handovers=handovers, native_cad_intervals=native_intervals, tool_intervals=tool_intervals,
                original_request=request_record, original_assets=inventory,
                evidence_mode=session.mode, boundary=boundary_identity,
                bootstrap_sha256=BOOTSTRAP_SHA256,
                unverified_python_host_intervals=loop.unverified_native_intervals if loop is not None else [],
                construction_operator={'value': None, 'reason': 'not_applicable'},
                human_engineering_time={'value': None, 'reason': 'not_applicable'})


def check_artifacts(session, entry, bundle, out, *, timeout=300):
    """Never execute model-origin Python restoration in evaluator authority.

    Construction source/dependencies remain reproducible bytes. Ordinary native
    C++ feature history needs no restoration module and uses the identical card.
    """
    import importlib
    artifacts = importlib.import_module(('tools.' if __package__ else '') + 'cad_verify_v4_artifacts')
    try:
        _, files, extensions = artifacts.load_bundle(bundle, profile=entry['profile'])
        if extensions:
            raise ValueError('bare_untrusted_python_restoration_forbidden')
        # Empty allowed files is conservative: bare handovers are self-contained.
        artifacts._guard_archive(files['native'], {}, set())
    except Exception as exc:
        return {'status': 'UNVERIFIED', 'reason': str(exc), 'untrusted_restoration_executed': False}
    return session.check_artifacts(entry, bundle, out, timeout=timeout)
