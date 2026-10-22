"""M0 only: fixed build-spec -> existing SolidWorks COM -> neutral v4 judge.

No provider, generated Python, macro, application launch/exit, or process-tree kill.
Run with the installed SolidWorks automation venv; only task-owned documents close.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / 'reports' / 'sw-m0'
FIXTURES = ROOT / 'design' / 'harness2-sw-m0'
SW_PYTHON = Path('C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe')
FC_BIN = Path('C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin')


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def output_path(path):
    path = Path(path).absolute()
    if '..' in path.parts:
        raise ValueError('output_parent_traversal_forbidden')
    if not path.is_relative_to(OUTPUTS) or path == OUTPUTS:
        raise ValueError('output_must_be_inside_worktree_reports_sw_m0')
    if any(p.is_symlink() or (p.exists() and getattr(p.stat(follow_symlinks=False), 'st_file_attributes', 0) & 0x400)
           for p in (path, *path.parents)):
        raise ValueError('output_link_forbidden')
    return path


def read_spec(path):
    from tools.cad_spec import loads_spec
    s = loads_spec(Path(path).read_text(encoding='utf-8'))
    if (s['family'] != 'rect_prism' or len(s['regions']) != 1 or len(s['pockets']) != 1
            or s['holes'] or not s['finish'] or s['finish']['kind'] != 'fillet'
            or s['finish']['target'] != 'top_outer'):
        raise ValueError('M0_only_one_box_blind_pocket_top_fillet')
    b = s['regions'][0]['bounds']
    p = s['pockets'][0]
    if b[4] != 0 or b[0] != -b[1] or b[2] != -b[3]:
        raise ValueError('M0_requires_origin_centered_XY_base_Z0')
    if p['bounds'][0] != -p['bounds'][1] or p['bounds'][2] != -p['bounds'][3]:
        raise ValueError('M0_requires_centered_pocket')
    return s


class Session:
    """All methods address handles created here, never an arbitrary ActiveDoc."""
    def __init__(self, out):
        import pythoncom
        from win32com.client.dynamic import Dispatch
        self.pc, self.out = pythoncom, out
        pythoncom.CoInitialize()
        # GetActiveObject cannot start a new SolidWorks instance.
        self.app = Dispatch(pythoncom.GetActiveObject('SldWorks.Application').QueryInterface(pythoncom.IID_IDispatch))
        self.owned = None
        self.title = None
        self.uncertain = False
        self.events = (out / 'com-events.jsonl').open('x', encoding='utf-8', buffering=1)
        self.revision = self.call(self.app, 'RevisionNumber')
        self.pid = self.call(self.app, 'GetProcessID')
        if self.call(self.app, 'GetDocumentCount') != 0:
            raise RuntimeError('STOP_existing_documents_open_no_document_touched')
        self.template = self.call(self.app, 'GetUserPreferenceStringValue', 8)
        if not Path(self.template).is_file():
            raise RuntimeError('STOP_part_template_missing')

    def call(self, obj, name, *args):
        # Late binding otherwise treats several zero-argument methods as properties.
        if self.uncertain:
            raise RuntimeError('STOP_COM_state_unknown_no_further_calls')
        tick = time.perf_counter()
        self.events.write(json.dumps({'event': 'call_started', 'at': utc(), 'method': name}) + '\n')
        try:
            obj._FlagAsMethod(name)
            result = getattr(obj, name)(*args)
        except self.pc.com_error as e:
            if (e.hresult & 0xffffffff) in (0x80010001, 0x8001010A, 0x800706BA, 0x80010108):
                self.uncertain = True
            self.events.write(json.dumps({'event': 'call_error', 'at': utc(), 'method': name,
                                          'hresult': e.hresult, 'error': str(e)}) + '\n')
            raise
        self.events.write(json.dumps({'event': 'call_finished', 'at': utc(), 'method': name,
                                      'seconds': time.perf_counter() - tick}) + '\n')
        return result

    def null(self):
        from win32com.client import VARIANT
        return VARIANT(self.pc.VT_DISPATCH, None)

    def out_int(self):
        from win32com.client import VARIANT
        return VARIANT(self.pc.VT_BYREF | self.pc.VT_I4, 0)

    def guard(self):
        if self.owned is None or self.call(self.app, 'GetDocumentCount') != 1:
            raise RuntimeError('STOP_session_changed')
        if self.call(self.owned, 'GetTitle') != self.title:
            raise RuntimeError('STOP_owned_document_title_changed')
        active = self.app.ActiveDoc
        if active is None or self.call(active, 'GetTitle') != self.title:
            raise RuntimeError('STOP_user_changed_active_document')

    def adopt(self, doc):
        if doc is None:
            raise RuntimeError('owned_document_not_created_or_opened')
        self.owned = doc
        self.title = self.call(doc, 'GetTitle')
        self.guard()
        return doc

    def close(self):
        if self.owned is None or self.uncertain:
            return
        self.guard()
        self.call(self.app, 'CloseDoc', self.title)
        self.owned = self.title = None
        if self.call(self.app, 'GetDocumentCount') != 0:
            raise RuntimeError('STOP_document_count_changed_after_owned_close')

    def reopen(self, path):
        if self.owned is not None or self.call(self.app, 'GetDocumentCount') != 0:
            raise RuntimeError('STOP_not_empty_before_owned_open')
        path = output_path(path)
        errors, warnings = self.out_int(), self.out_int()
        doc = self.call(self.app, 'OpenDoc6', str(path), 1, 1, '', errors, warnings)
        if errors.value:
            raise RuntimeError('owned_native_open_errors:' + str(errors.value))
        return self.adopt(doc)

    def save(self, path, *, copy=False):
        self.guard()
        path = output_path(path)
        if path.exists():
            raise FileExistsError(path)
        errors, warnings = self.out_int(), self.out_int()
        okay = self.call(self.owned.Extension, 'SaveAs', str(path), 0, 3 if copy else 1,
                         self.null(), errors, warnings)
        if not okay or errors.value or not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError('owned_save_failed:' + str(errors.value))
        self.title = self.call(self.owned, 'GetTitle')
        return {'path': str(path), 'sha256': digest(path), 'bytes': path.stat().st_size,
                'errors': errors.value, 'warnings': warnings.value}

    def body(self):
        bodies = self.call(self.owned, 'GetBodies2', 0, False)
        if not bodies or len(bodies) != 1:
            raise RuntimeError('expected_one_solid_body')
        return bodies[0]

    def history(self):
        self.guard()
        f = self.call(self.owned, 'FirstFeature')
        rows = []
        while f is not None:
            rows.append({'name': f.Name, 'type': self.call(f, 'GetTypeName2')})
            f = self.call(f, 'GetNextFeature')
        values = {}
        for label in ('M0_Boss', 'M0_Pocket', 'M0_TopR3'):
            d = self.call(self.owned, 'Parameter', 'D1@' + label)
            if d is None:
                raise RuntimeError('missing_driving_dimension:' + label)
            values[label] = float(d.SystemValue) * 1000
        return {'features': rows, 'driving_mm': values}

    def mass(self):
        # Parasolid measurement is a secondary observation, never the main judge.
        props = self.call(self.body(), 'GetMassProperties', 1.0)
        return {'volume_mm3': float(props[3]) * 1e9, 'area_mm2': float(props[4]) * 1e6,
                'raw_SI_density_1': list(props), 'role': 'secondary_cross_check_only'}

    def build(self, spec):
        tick = time.perf_counter()
        if self.call(self.app, 'GetDocumentCount') != 0:
            raise RuntimeError('STOP_existing_documents_open')
        doc = self.adopt(self.call(self.app, 'NewDocument', self.template, 0, 0., 0.))
        # Plane identity comes from its transform, not language-specific labels.
        f, plane = self.call(doc, 'FirstFeature'), None
        while f is not None:
            if self.call(f, 'GetTypeName2') == 'RefPlane':
                ref = self.call(f, 'GetSpecificFeature2')
                a = list(ref.Transform.ArrayData)
                if abs(abs(a[8])-1) < 1e-9 and abs(a[6])+abs(a[7])+sum(abs(v) for v in a[9:12]) < 1e-9:
                    plane = f
                    break
            f = self.call(f, 'GetNextFeature')
        if plane is None or not self.call(plane, 'Select2', False, 0):
            raise RuntimeError('XY_reference_plane_not_found')
        sm, fm = doc.SketchManager, doc.FeatureManager
        b, p, r = spec['regions'][0]['bounds'], spec['pockets'][0], spec['finish']['size']
        self.call(sm, 'InsertSketch', True)
        self.call(sm, 'CreateCornerRectangle', b[0]/1000, b[2]/1000, 0., b[1]/1000, b[3]/1000, 0.)
        self.call(sm, 'InsertSketch', True)
        boss = self.call(fm, 'FeatureExtrusion3', True, False, False, 0, 0, b[5]/1000, 0.,
                         False, False, False, False, 0., 0., False, False, False, False,
                         True, True, True, 0, 0., False)
        if boss is None:
            raise RuntimeError('boss_failed')
        boss.Name = 'M0_Boss'
        self.call(doc, 'ClearSelection2', True)
        # Select the actual upper planar face by analytic normal and origin height.
        top = []
        for face in self.call(self.body(), 'GetFaces'):
            surf = self.call(face, 'GetSurface')
            if self.call(surf, 'IsPlane'):
                a = list(surf.PlaneParams)
                if abs(abs(a[2])-1) < 1e-8 and abs(a[5]-b[5]/1000) < 1e-8:
                    top.append(face)
        if len(top) != 1 or not self.call(top[0], 'Select4', False, self.null()):
            raise RuntimeError('unique_top_face_not_found')
        self.call(sm, 'InsertSketch', True)
        # Face sketch coordinates are transformed from WORLD, not assumed UV axes.
        sketch = sm.ActiveSketch
        transform = sketch.ModelToSketchTransform
        util = self.call(self.app, 'GetMathUtility')
        from win32com.client import VARIANT
        corners = []
        for x,y in ((p['bounds'][0],p['bounds'][2]), (p['bounds'][1],p['bounds'][3])):
            # MathUtility requires SAFEARRAY(double), not SAFEARRAY(VARIANT).
            coordinates = VARIANT(self.pc.VT_ARRAY | self.pc.VT_R8,
                                  (x/1000,y/1000,b[5]/1000))
            point = self.call(util, 'CreatePoint', coordinates)
            point = self.call(point, 'MultiplyTransform', transform)
            corners.extend(list(point.ArrayData))
        matrix = list(transform.ArrayData)
        save_json(self.out/('pocket-frame-%s.json' % ('wrong' if p['depth'] != 5 else 'positive')),
                  {'model_to_sketch': matrix, 'rectangle_sketch_SI': corners})
        self.call(sm, 'CreateCornerRectangle', *corners)
        self.call(sm, 'InsertSketch', True)
        cut = self.call(fm, 'FeatureCut4', True, False, matrix[8] < 0, 0, 0, p['depth']/1000, 0.,
                        False, False, False, False, 0., 0., False, False, False, False,
                        False, True, True, False, False, False, 0, 0., False, False)
        if cut is None:
            raise RuntimeError('blind_pocket_failed')
        cut.Name = 'M0_Pocket'
        self.call(doc, 'ClearSelection2', True)
        selected = []
        data = self.call(doc.SelectionManager, 'CreateSelectData')
        data.Mark = 1
        for edge in self.call(self.body(), 'GetEdges'):
            start, end = self.call(edge, 'GetStartVertex'), self.call(edge, 'GetEndVertex')
            if start is None or end is None:
                continue
            pts = [self.call(v, 'GetPoint') for v in (start, end)]
            if all(abs(pt[2]-b[5]/1000) < 1e-8 for pt in pts) and any(
                    all(abs(pt[axis]-limit/1000) < 1e-8 for pt in pts)
                    for axis,limit in ((0,b[0]),(0,b[1]),(1,b[2]),(1,b[3]))):
                if not self.call(edge, 'Select4', True, data):
                    raise RuntimeError('outer_edge_selection_failed')
                selected.append([list(pt) for pt in pts])
        if len(selected) != 4:
            raise RuntimeError('need_exactly_four_top_outer_edges')
        fillet = self.call(fm, 'FeatureFillet3', 2, r/1000, 0., 0., 0, 0, 0,
                           None, None, None, None, None, None, None)
        if fillet is None:
            raise RuntimeError('top_outer_fillet_failed')
        fillet.Name = 'M0_TopR3'
        if not self.call(doc, 'EditRebuild3'):
            raise RuntimeError('native_rebuild_failed')
        self.guard()
        return {'build_s': time.perf_counter()-tick, 'selected_outer_edges_SI': selected,
                'history': self.history(), 'mass': self.mass()}


def com_worker(out):
    result = {'status': 'FAIL', 'paid_model_calls': 0, 'at': utc()}
    session = None
    tick = time.perf_counter()
    try:
        session = Session(out)
        result.update(solidworks_revision=session.revision, solidworks_pid=session.pid,
                      initial_documents=0, template=session.template, stages={})
        stages = result['stages']
        stages['positive'] = session.build(read_spec(FIXTURES/'positive.json'))
        stages['positive']['native'] = session.save(out/'positive.sldprt')
        stages['positive']['step'] = session.save(out/'before-reopen.step', copy=True)
        session.close()
        t = time.perf_counter()
        session.reopen(out/'positive.sldprt')
        if not session.call(session.owned, 'EditRebuild3'):
            raise RuntimeError('reopen_rebuild_failed')
        stages['reopened'] = {'step': session.save(out/'reopened.step', copy=True),
                              'history': session.history(), 'mass': session.mass()}
        session.close()
        stages['reopened']['seconds'] = time.perf_counter()-t
        original_hash = digest(out/'positive.sldprt')
        shutil.copyfile(out/'positive.sldprt', out/'edit-copy.sldprt')
        session.reopen(out/'edit-copy.sldprt')
        dimension = session.call(session.owned, 'Parameter', 'D1@M0_Boss')
        initial = float(dimension.SystemValue)
        t = time.perf_counter()
        # Independent DEV perturbation: +1mm in height, not a new card criterion.
        status = session.call(dimension, 'SetSystemValue3', initial+.001, 1, None)
        if status != 0 or not session.call(session.owned, 'EditRebuild3'):
            raise RuntimeError('dimension_change_rebuild_failed')
        stages['edited'] = {'expected_height_mm': initial*1000+1,
                            'step': session.save(out/'edited.step', copy=True),
                            'history': session.history(), 'mass': session.mass(),
                            'seconds': time.perf_counter()-t}
        t = time.perf_counter()
        status = session.call(dimension, 'SetSystemValue3', initial, 1, None)
        if status != 0 or not session.call(session.owned, 'EditRebuild3'):
            raise RuntimeError('dimension_restore_rebuild_failed')
        stages['restored'] = {'step': session.save(out/'restored.step', copy=True),
                              'history': session.history(), 'mass': session.mass(),
                              'seconds': time.perf_counter()-t}
        session.close()
        if digest(out/'positive.sldprt') != original_hash:
            raise RuntimeError('original_native_changed_during_copy_edit')
        stages['negative'] = session.build(read_spec(FIXTURES/'wrong-depth.json'))
        stages['negative']['native'] = session.save(out/'wrong-depth.sldprt')
        stages['negative']['step'] = session.save(out/'wrong-depth.step', copy=True)
        session.close()
        result.update(status='PASS', final_documents=session.call(session.app,'GetDocumentCount'),
                      original_native_unchanged=True)
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
    finally:
        if session is not None:
            try:
                session.close()
            except Exception as exc:
                result.update(status='FAIL', cleanup_error=str(exc))
            result['COM_state_unknown'] = session.uncertain
            session.events.close()
        result['seconds'] = time.perf_counter()-tick
        save_json(out/'com-result.json', result)
    return 0 if result['status']=='PASS' else 1


def run(out):
    out = output_path(out)
    out.mkdir(parents=True, exist_ok=False)
    OUTPUTS.mkdir(exist_ok=True)
    lock = OUTPUTS/'session.lock'
    with lock.open('x', encoding='utf-8') as f:
        json.dump({'at':utc(),'pid':os.getpid(),'out':str(out)},f)
    stopped = False
    t = time.perf_counter()
    result = {'paid_model_calls':0, 'out':str(out), 'started_at':utc(), 'status':'FAIL'}
    result['source_sha256'] = {name:digest(ROOT/name) for name in
        ('tools/sw_m0.py','tools/sw_m0_probe.py','tools/cad_spec.py','tools/cad_spec_probe.py',
         'design/cad-harness-mvp/eval-v1/P1.json',
         'design/harness2-sw-m0/positive.json','design/harness2-sw-m0/wrong-depth.json')}
    try:
        argv = [str(SW_PYTHON),'-B',str(Path(__file__).resolve()),'--com-worker',str(out)]
        with (out/'com.stdout.bin').open('xb') as stdout, (out/'com.stderr.bin').open('xb') as stderr:
            proc = subprocess.Popen(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
            try:
                code = proc.wait(timeout=300)
            except subprocess.TimeoutExpired:
                # Existing SolidWorks is NOT a child and is NEVER terminated.
                proc.kill()
                proc.wait(timeout=10)
                stopped = True
                raise RuntimeError('STOP_SW_state_unknown_client_only_stopped_no_retry')
        result['com_exit'] = code
        com = json.loads((out/'com-result.json').read_text(encoding='utf-8'))
        if code != 0 or com['status'] != 'PASS':
            stopped = (bool(com.get('COM_state_unknown')) or com.get('error', '').startswith('STOP_')
                       or 'STOP_' in com.get('cleanup_error', ''))
            raise RuntimeError('COM_stage_failed:' + com.get('error','unknown'))
        bootstrap = 'import runpy,sys;sys.path[:0]='+repr([str(ROOT),str(FC_BIN)])+';runpy.run_module("tools.sw_m0_probe",run_name="__main__")'
        argv = [str(FC_BIN/'python.exe'),'-I','-B','-c',bootstrap,str(out)]
        with (out/'judge.stdout.bin').open('xb') as stdout, (out/'judge.stderr.bin').open('xb') as stderr:
            jp = subprocess.run(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,timeout=300)
        result['judge_exit'] = jp.returncode
        judge = json.loads((out/'judge-result.json').read_text(encoding='utf-8'))
        result['status'] = 'PASS' if jp.returncode==0 and judge['status']=='PASS' else 'FAIL'
        result['neutral_checks'] = judge
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(finished_at=utc(),total_seconds=time.perf_counter()-t,manual_recovery_required=stopped)
        save_json(out/'result.json',result)
        if not stopped:
            lock.unlink()
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__':
    # Both installed interpreters must import ONLY this new worktree's tools.
    sys.path.insert(0,str(ROOT))
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--out')
    group.add_argument('--com-worker')
    args=parser.parse_args()
    raise SystemExit(com_worker(output_path(args.com_worker)) if args.com_worker else run(args.out))
