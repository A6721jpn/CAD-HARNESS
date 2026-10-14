"""S1 host admission tests: independent temporary data, no model/native processes."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import cad_verify_v4_inputs as inputs, cad_verify_v4_plans as plans
from tools import cad_verify_v4_ledger as ledger
from tools.test_support import start_tempdirs, stop_tempdirs


def setUpModule():
    global _temp_patches
    _temp_patches = start_tempdirs()


def tearDownModule():
    stop_tempdirs(_temp_patches)


class _HostFixtures:
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.manifest_path = self.root / 'inputs.json'
        self.step = self.root / 'independent.step'
        # Admission bytes only; never sent to a native importer.
        self.step.write_bytes(b'ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n')
        self.manifest = {'schema': 'cad-harness.inputs.v4c', 'profile': 'c-s1',
                         'evidence_mode': 'independent_dev', 'assets': {'reference': {
                             'kind': 'step', 'role': 'reference', 'path': self.step.name,
                             'sha256': ledger.file_sha(self.step), 'bytes': self.step.stat().st_size}}}
        self.save_manifest()
        deny = patch.object(subprocess, 'Popen', side_effect=AssertionError('process launch forbidden in host suite'))
        deny.start()
        self.addCleanup(deny.stop)
        deny_run = patch.object(subprocess, 'run', side_effect=AssertionError('process launch forbidden in host suite'))
        deny_run.start()
        self.addCleanup(deny_run.stop)
        import socket
        deny_network = patch.object(socket.socket, 'connect', side_effect=AssertionError('provider network forbidden in host suite'))
        deny_network.start()
        self.addCleanup(deny_network.stop)

    def save_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding='utf-8')

    def packet(self):
        digest = self.manifest['assets']['reference']['sha256']
        manifest_digest = ledger.file_sha(self.manifest_path)
        facts = {'schema': 'cad-harness.step-facts.v4c', 'profile': 'c-s1', 'asset_id': 'reference',
                 'source_sha256': digest, 'units': 'mm', 'bounds_mm': [0, 2, 0, 3, 0, 4],
                 'topology': {'solids': 1, 'shells': 1, 'faces': 1, 'edges': 4},
                 'frame': {'source_axes': ['X', 'Y', 'Z'], 'source_units': 'mm', 'import_units': 'mm',
                           'axis_transform': 'identity', 'thickness_mm': None,
                           'thickness_reason': 'requires_explicit_face_pair_not_bbox'},
                 'faces': [{'id': 'Face1', 'signature': '1'*64, 'ambiguous': False, 'surface_type': 'Plane',
                            'area_mm2': 6, 'center_mm': [1, 1.5, 0], 'bounds_mm': [0, 2, 0, 3, 0, 0],
                            'normal': [0, 0, -1], 'normal_kind': 'constant', 'normal_reason': None}],
                 'coverage': {'complete': True, 'missing_reasons': []}, 'recipe_sha256': '2'*64,
                 'provenance': {'manifest_sha256_before': manifest_digest, 'manifest_sha256_after': manifest_digest,
                                'asset_sha256_before': digest, 'asset_sha256_after': digest,
                                'importer': 'FreeCAD.Part.Shape.read', 'freecad_version': 'test-admission-only'}}
        return {'schema': 'cad-harness.prepared.v4c', 'profile': 'c-s1',
                'source_manifest_sha256': manifest_digest, 'assets': {'reference': facts}}

    def plan(self):
        return {'schema': 'cad-harness.plan.v4c', 'profile': 'c-s1', 'family': 'contour_extrude',
                'contour_id': 'outline', 'width_mm': 12, 'thickness_mm': 2,
                'origin_mm': [0, 0, 0], 'references': [], 'engravings': []}


class S1HostAdmission(_HostFixtures, unittest.TestCase):
    def test_consumer_resolution_and_sanitized_packet(self):
        self.assertEqual(inputs.load_manifest(self.manifest_path), self.manifest)
        resolved = inputs.resolve_asset(self.manifest_path, 'reference', 'step')
        self.assertEqual(resolved['path'], self.step)
        self.assertEqual(resolved['digest'], ledger.file_sha(self.step))
        packet = self.packet()
        self.assertEqual(inputs.verify_prepared(packet, self.manifest_path), packet)
        visible = inputs.model_inputs(packet, self.manifest_path)
        text = json.dumps(visible, sort_keys=True)
        self.assertNotIn(str(self.root), text)
        self.assertNotIn('path', visible['assets']['reference'])
        self.assertNotIn('provenance', visible['assets']['reference'])
        self.assertNotIn('recipe_sha256', visible['assets']['reference'])
        self.assertIsNone(visible['assets']['reference']['frame']['thickness_mm'])

    def test_manifest_unknowns_and_missing_fields(self):
        for change in ('unknown', 'missing', 'profile', 'role'):
            with self.subTest(change=change):
                value = copy.deepcopy(self.manifest)
                if change == 'unknown': value['code'] = 'print(1)'
                elif change == 'missing': del value['assets']['reference']['sha256']
                elif change == 'profile': value['profile'] = 'original'
                else: value['assets']['reference']['role'] = 'font'
                self.manifest_path.write_text(json.dumps(value), encoding='utf-8')
                with self.assertRaises(ValueError): inputs.load_manifest(self.manifest_path)
        self.save_manifest()

    def test_traversal_absolute_and_private_rejected_before_lookup(self):
        for name in ('../independent.step', '/outside.step', 'C:/outside.step', 'C:outside.step',
                     'x/../independent.step', 'pilot-user/missing.step', 'V4-HOLDOUT-PRIVATE/missing.step',
                     'x\\independent.step', 'x./independent.step', 'independent.step:stream'):
            with self.subTest(name=name):
                self.manifest['assets']['reference']['path'] = name
                self.save_manifest()
                with self.assertRaises(ValueError): inputs.resolve_asset(self.manifest_path, 'reference')
        with patch.object(Path, 'lstat', side_effect=AssertionError('private lookup')):
            with self.assertRaisesRegex(ValueError, 'private_input_path_forbidden'):
                inputs.load_manifest(self.root / 'pilot-user' / 'never.json')

    def test_reparse_points_denied_even_without_symlink_privileges(self):
        from types import SimpleNamespace
        actual_lstat = Path.lstat
        def reparse_stat(path, *args, **kwargs):
            info = actual_lstat(path, *args, **kwargs)
            if path == self.step:
                return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
            return info
        with patch.object(Path, 'lstat', reparse_stat):
            with self.assertRaisesRegex(ValueError, 'linked_input_path'):
                inputs.resolve_asset(self.manifest_path, 'reference')

    def test_linked_asset_and_parent_denied(self):
        link = self.root / 'linked.step'
        try:
            link.symlink_to(self.step)
        except (OSError, NotImplementedError):
            self.skipTest('OS does not permit test symlinks')
        self.manifest['assets']['reference']['path'] = link.name
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'linked_input_path'):
            inputs.resolve_asset(self.manifest_path, 'reference')
        link.unlink()
        directory = self.root / 'linked-dir'
        directory.symlink_to(self.root, target_is_directory=True)
        self.manifest['assets']['reference']['path'] = 'linked-dir/independent.step'
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'linked_input_path'):
            inputs.resolve_asset(self.manifest_path, 'reference')

    def test_mismatch_missing_unknown_and_special(self):
        for field, value, reason in [('sha256', '0'*64, 'sha256'), ('bytes', 1, 'bytes')]:
            original = self.manifest['assets']['reference'][field]
            self.manifest['assets']['reference'][field] = value
            self.save_manifest()
            with self.assertRaisesRegex(ValueError, reason): inputs.resolve_asset(self.manifest_path, 'reference')
            self.manifest['assets']['reference'][field] = original
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'unknown_asset_id'): inputs.resolve_asset(self.manifest_path, 'missing')
        with self.assertRaisesRegex(ValueError, 'kind_mismatch'): inputs.resolve_asset(self.manifest_path, 'reference', 'image')
        with self.assertRaisesRegex(ValueError, 'not_regular'): inputs.guarded_path(self.root)
        self.step.write_bytes(b'not a STEP file')
        self.manifest['assets']['reference'].update(sha256=ledger.file_sha(self.step), bytes=self.step.stat().st_size)
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'content_mismatch'): inputs.load_manifest(self.manifest_path)

    def test_prepared_admission_provenance_and_unknown_fields(self):
        for mutation in ('manifest', 'asset', 'before', 'after', 'private', 'unknown_asset'):
            packet = self.packet()
            facts = packet['assets']['reference']
            if mutation == 'manifest': packet['source_manifest_sha256'] = '0'*64
            elif mutation == 'asset': facts['source_sha256'] = '0'*64
            elif mutation == 'before': facts['provenance']['asset_sha256_before'] = '0'*64
            elif mutation == 'after': facts['provenance']['manifest_sha256_after'] = '0'*64
            elif mutation == 'private': facts['private_gold'] = {'tolerance': 1}
            else: packet['assets']['unknown'] = copy.deepcopy(facts)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                inputs.model_inputs(packet, self.manifest_path)
        self.step.write_bytes(self.step.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            inputs.verify_prepared(self.packet(), self.manifest_path)

    def test_plan_profile_semantics_strict_and_no_hidden_acceptance(self):
        self.assertEqual(plans.validate_plan(self.plan()), self.plan())
        for mutation in ('profile', 'minR', 'missing', 'zero', 'nan', 'code'):
            value = self.plan()
            if mutation == 'profile': value['profile'] = 'c-s2'
            elif mutation == 'minR': value['minimum_radius_mm'] = 4
            elif mutation == 'missing': del value['references']
            elif mutation == 'zero': value['thickness_mm'] = 0
            elif mutation == 'nan': value['width_mm'] = float('nan')
            else: value['python'] = 'import Part'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): plans.validate_plan(value)
        value = self.plan()
        value['references'] = [{'asset_id': 'reference', 'translation_mm': [0,0,0], 'rotation_axis': [0,0,0], 'rotation_deg': 0}]
        with self.assertRaisesRegex(ValueError, 'zero_rotation_axis'): plans.validate_plan(value)
        value['references'][0]['rotation_axis'] = [1,0,0]
        with self.assertRaisesRegex(ValueError, 'contour_asset_mismatch'): plans.validate_plan(value, self.manifest_path)

    def test_card_no_acceptance_defaults_and_strict_metric_fields(self):
        card = {'schema': 'cad-harness.judge-card.v4c', 'profile': 'c-s1', 'source': 'independent_dev',
                'linear_tolerance_mm': 0, 'criteria': [{'id': 'radius', 'metric': 'min_radius'}]}
        self.assertEqual(plans.validate_judge_card(card), card)
        for mutate in ('unknown', 'duplicate', 'nan', 'schema'):
            value = copy.deepcopy(card)
            if mutate == 'unknown': value['criteria'][0]['script'] = 'pass'
            elif mutate == 'duplicate': value['criteria'].append(copy.deepcopy(value['criteria'][0]))
            elif mutate == 'nan': value['linear_tolerance_mm'] = float('inf')
            else: value['schema'] = 'cad-harness.judge-card.v4'
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): plans.validate_judge_card(value)
        self.assertNotIn('minimum_mm', plans.validate_judge_card(card)['criteria'][0])
        del card['linear_tolerance_mm']
        self.assertNotIn('linear_tolerance_mm', plans.validate_judge_card(card))

    def test_font_registry_requires_license_and_explicit_glyphs(self):
        font = self.root / 'font.ttf'
        font.write_bytes(b'\x00\x01\x00\x00 admission-only')
        self.manifest['assets']['font'] = {'kind':'font','role':'font','path':font.name,
            'sha256':ledger.file_sha(font),'bytes':font.stat().st_size,'glyphs':'ABC','license_asset_id':'license'}
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'font_license_missing'): inputs.load_manifest(self.manifest_path)
        license_path = self.root / 'LICENSE'
        license_path.write_text('Independent host fixture license',encoding='utf-8')
        self.manifest['assets']['license'] = {'kind':'license','role':'license','path':'LICENSE',
            'sha256':ledger.file_sha(license_path),'bytes':license_path.stat().st_size}
        self.save_manifest()
        self.assertEqual(inputs.resolve_asset(self.manifest_path,'font','font')['record']['glyphs'],'ABC')
        visible=inputs.model_inputs(self.packet(),self.manifest_path)
        self.assertEqual(visible['fonts']['font']['glyphs'],'ABC')
        self.assertEqual(visible['fonts']['font']['font_sha256'],ledger.file_sha(font))
        self.assertNotIn(str(font),json.dumps(visible))
        del self.manifest['assets']['font']['glyphs']
        self.save_manifest()
        with self.assertRaises(ValueError): inputs.load_manifest(self.manifest_path)

    def test_host_admission_never_imports_native_stack(self):
        import builtins
        original_import = builtins.__import__
        def guarded_import(name, *args, **kwargs):
            if name.split('.')[0] in {'FreeCAD', 'Part', 'Sketcher', 'numpy', 'scipy', 'PIL', 'shapely', 'OCC'}:
                raise AssertionError('native or numerical import during host admission: ' + name)
            return original_import(name, *args, **kwargs)
        with patch.object(builtins, '__import__', side_effect=guarded_import):
            inputs.load_manifest(self.manifest_path)
            inputs.model_inputs(self.packet(), self.manifest_path)
            plans.validate_plan(self.plan())
            plans.validate_judge_card({'schema':'cad-harness.judge-card.v4c','profile':'c-s1',
                                      'source':'independent_dev','criteria':[{'id':'solid','metric':'solid_valid'}]})

    def test_face_coverage_and_normals_not_fabricated(self):
        for mutation in ('normal', 'count', 'coverage', 'ambiguity'):
            value = self.packet()
            facts = value['assets']['reference']
            if mutation == 'normal': facts['faces'][0]['normal'] = [0, 0, 2]
            elif mutation == 'count': facts['topology']['faces'] = 2
            elif mutation == 'coverage': facts['coverage']['complete'] = False
            else: facts['faces'][0]['ambiguous'] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                inputs.model_inputs(value, self.manifest_path)
        value = self.packet()
        face = value['assets']['reference']['faces'][0]
        face.update(normal=None, normal_kind='unavailable', normal_reason='native_normal_unavailable')
        value['assets']['reference']['coverage'] = {'complete':False,'missing_reasons':['Face1:native_normal_unavailable']}
        self.assertIsNone(inputs.model_inputs(value,self.manifest_path)['assets']['reference']['faces'][0]['normal'])

    def test_independent_analytic_source_is_digest_bound_not_fake_preprocessing(self):
        image = self.root / 'checker.png'
        image.write_bytes(b'\x89PNG\r\n\x1a\n host-admission-only')
        raw = {'schema':'cad-harness.contour-source.v4c','profile':'c-s1','units':'mm',
               'bounds_mm':[0,2,0,2],'nominal_width_mm':2,'source_image_asset_id':'checker',
               'loops':[{'role':'outer','segments':[
                   {'kind':'line','p0':[0,0],'p1':[2,0]}, {'kind':'line','p0':[2,0],'p1':[2,2]},
                   {'kind':'line','p0':[2,2],'p1':[0,2]}, {'kind':'line','p0':[0,2],'p1':[0,0]}]}]}
        contour = self.root / 'contour.json'
        contour.write_text(json.dumps(raw),encoding='utf-8')
        self.manifest['assets'].update({
            'outline':{'kind':'contour','role':'contour','path':contour.name,'sha256':ledger.file_sha(contour),'bytes':contour.stat().st_size},
            'checker':{'kind':'image','role':'checker','path':image.name,'sha256':ledger.file_sha(image),'bytes':image.stat().st_size}})
        self.save_manifest()
        prepared_record = {key:copy.deepcopy(raw[key]) for key in ('profile','units','bounds_mm','nominal_width_mm','loops','source_image_asset_id')}
        prepared_record.update(schema='cad-harness.contour.v4c',asset_id='outline',
            source_sha256=ledger.file_sha(contour),source_image_sha256=ledger.file_sha(image),
            provenance={'kind':'independent_analytic_source'},topology={'components':1,'holes':0},
            pixel_to_mm={'scale_mm_per_pixel':1,'origin_mm':[0,0],'image_height_pixels':2,
                         'y_axis':'up','pixel_convention':'closed unit cells; centers at (col+0.5,row+0.5)'})
        packet = {'schema':'cad-harness.prepared.v4c','profile':'c-s1','source_manifest_sha256':ledger.file_sha(self.manifest_path),
                  'assets':{'outline':prepared_record}}
        visible = inputs.model_inputs(packet,self.manifest_path)
        self.assertNotIn('source_image_asset_id',visible['assets']['outline'])
        self.assertNotIn('source_mask',visible['assets']['outline'])
        self.assertNotIn('recipe',visible['assets']['outline'])
        plans.validate_plan(self.plan(),self.manifest_path,packet)
        changed = copy.deepcopy(packet)
        changed['assets']['outline']['loops'][0]['segments'][0]['p1'] = [3,0]
        with self.assertRaisesRegex(ValueError,'analytic_geometry_mismatch'):
            inputs.verify_prepared(changed,self.manifest_path)
        changed = copy.deepcopy(packet)
        changed['assets']['outline']['source_image_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'analytic_image_mismatch'):
            inputs.verify_prepared(changed,self.manifest_path)
        changed = copy.deepcopy(packet)
        changed['assets']['outline']['recipe'] = {'fake':'preprocessing'}
        with self.assertRaises(ValueError):
            inputs.verify_prepared(changed,self.manifest_path)


if __name__ == '__main__':
    unittest.main()
