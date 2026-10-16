"""Frozen native feature algorithms with data-only persistence and explicit dependencies.

OCCT numerical checks use 1e-6 mm probes and 1e-8 relative volume consistency;
these are construction invariants, never judge-card acceptance tolerances.

Rejected edits clear the complete frozen output chain, including a Body's cached
Shape: FreeCAD rejects an empty Tip without clearing that public output itself.
"""
import base64
import hashlib
import json
import math
from contextlib import contextmanager


def _imports():
    if __package__:
        from . import cad_spec, cad_verify_v4_inputs as inputs, cad_verify_v4_text as text
    else:
        import cad_spec
        import cad_verify_v4_inputs as inputs
        import cad_verify_v4_text as text
    return cad_spec, inputs, text


def _number(value, name, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(name)
    return float(value)


def _vector(value, name):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(name)
    return [_number(v, name) for v in value]


def _solid(shape, expected_solids=1):
    if type(expected_solids) is not int or expected_solids < 1:
        raise ValueError('invalid_expected_solid_count')
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != expected_solids or shape.Volume <= 0:
        raise ValueError('single_valid_solid_required' if expected_solids == 1 else 'declared_valid_solids_required')
    return shape


def shape_measurements(shape, *, tight_bounds=False, expected_solids=1):
    _solid(shape, expected_solids)
    # S2 dimensions must bound trimmed geometry, not extended spline supports.
    b = shape.optimalBoundingBox(False, False) if tight_bounds else shape.BoundBox
    return {'bounds_mm': [b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax],
            'volume_mm3': shape.Volume, 'solids': len(shape.Solids), 'valid': shape.isValid()}


def contour_face(record, scale=1.0):
    """Exact OCCT edges; FaceMakerBullseye preserves nested counters and islands."""
    import FreeCAD as App
    import Part
    wires = []
    for loop in record['loops']:
        edges = []
        def point(p):
            if not isinstance(p, (list, tuple)) or len(p) != 2:
                raise ValueError('contour_point')
            return App.Vector(_number(p[0], 'contour_point') * scale,
                              _number(p[1], 'contour_point') * scale, 0)
        for segment in loop['segments']:
            kind = segment['kind']
            if kind == 'line':
                edge = Part.makeLine(point(segment['p0']), point(segment['p1']))
            elif kind == 'arc':
                edge = Part.Arc(point(segment['p0']), point(segment['pm']), point(segment['p1'])).toShape()
            elif kind == 'bezier':
                poles = segment['poles']
                if len(poles) not in (3, 4):
                    raise ValueError('quadratic_or_cubic_required')
                curve = Part.BezierCurve()
                curve.setPoles([point(p) for p in poles])
                edge = curve.toShape()
            else:
                raise ValueError('contour_segment_kind')
            edges.append(edge)
        wire = Part.Wire(edges)
        if not wire.isClosed() or not wire.isValid():
            raise ValueError('native_contour_wire')
        wires.append(wire)
    if not wires:
        raise ValueError('native_contour_empty')
    face = Part.makeFace(wires, 'Part::FaceMakerBullseye')
    if face.isNull() or not face.isValid() or face.Area <= 0:
        raise ValueError('native_contour_face')
    return face


def engraving_placement(entry):
    import FreeCAD as App
    origin = _vector(entry['origin_mm'], 'engraving_origin')
    axis = _vector(entry['rotation_axis'], 'engraving_axis')
    if math.sqrt(sum(v * v for v in axis)) == 0:
        raise ValueError('engraving_axis_zero')
    angle = _number(entry['rotation_deg'], 'engraving_angle')
    return App.Placement(App.Vector(*origin), App.Rotation(App.Vector(*axis), angle))


def engraving_tool(entry, outline):
    import FreeCAD as App
    depth = _number(entry['depth_mm'], 'engraving_depth', True)
    face = contour_face(outline)
    tool = face.extrude(App.Vector(0, 0, -depth))
    tool.Placement = engraving_placement(entry)
    if tool.isNull() or not tool.isValid() or not tool.Solids:
        raise ValueError('engraving_tool_invalid')
    return tool


class _FrozenProxy:
    """FreeCAD serializer stores only this version token; geometry lives in properties."""
    TOKEN = 'cad-harness.native-feature.v4c:1'

    def dumps(self):
        return self.TOKEN

    def loads(self, value):
        if value != self.TOKEN:
            raise ValueError('native_proxy_version')

    def __getstate__(self):
        return self.TOKEN

    def __setstate__(self, value):
        self.loads(value)

    def onDocumentRestored(self, obj):
        obj.touch()

    def expected_solids(self, obj):
        return 1

    def execute(self, obj):
        import Part
        # Clear first: an exception or failed recompute can never retain a valid stale Shape.
        obj.Shape = Part.Shape()
        obj.BuildStatus = 'computing'
        try:
            shape = self.construct(obj)
            obj.Shape = _solid(shape, self.expected_solids(obj))
            obj.BuildStatus = 'ok'
        except Exception as exc:
            # Recompute stops at a failed dependency. Descendants (and the Body's
            # separate Shape cache) must not keep exposing the last valid solid.
            pending = [obj]
            cleared = set()
            while pending:
                failed = pending.pop()
                if failed.Name in cleared:
                    continue
                cleared.add(failed.Name)
                failed.Shape = Part.Shape()
                failed.BuildStatus = ('failed:' + str(exc) if failed == obj else
                                      'failed:upstream_feature:' + obj.Name)
                for dependent in failed.InList:
                    if dependent.TypeId == 'PartDesign::Body' and dependent.Tip == failed:
                        dependent.Shape = Part.Shape()
                    elif (type(dependent.Proxy if 'Proxy' in dependent.PropertiesList else None)
                          is EngravingProxy and dependent.Base == failed):
                        pending.append(dependent)
            raise


class _ValidatedContourSource(str):
    """Immutable, fully authenticated source bytes; never serialized in a feature."""
    __slots__ = ()

    def __new__(cls, value):
        if type(value) is not str:
            raise ValueError('contour_source_requires_string')
        if __package__:
            from .cad_verify_v4_contours import validate_contour
        else:
            from cad_verify_v4_contours import validate_contour
        validate_contour(json.loads(value))
        return super().__new__(cls, value)


@contextmanager
def validated_contour_sources(doc):
    """Authenticate fixed sources once for this synchronous recompute/edit chain.

    Only installed ContourProxy instances receive an immutable representation.
    A changed ContourData value still takes the ordinary full-validation path;
    dimensions, placement and every resulting BREP are rebuilt as before.
    No handle survives this scope or the feature's data-only serialization.
    """
    bindings = []
    try:
        for obj in doc.Objects:
            proxy = obj.Proxy if 'Proxy' in obj.PropertiesList else None
            if type(proxy) is ContourProxy:
                source = _ValidatedContourSource(obj.ContourData)
                previous = getattr(proxy, '_validated_source', None)
                bindings.append((proxy, previous))
                proxy._validated_source = source
        yield
    finally:
        for proxy, previous in reversed(bindings):
            if previous is None:
                del proxy._validated_source
            else:
                proxy._validated_source = previous


class ContourProxy(_FrozenProxy):
    def expected_solids(self, obj):
        _, inputs, _ = _imports()
        return inputs.contour_solid_count(json.loads(obj.ContourData))

    def construct(self, obj):
        import FreeCAD as App
        data = obj.ContourData
        record = json.loads(data)
        source = getattr(self, '_validated_source', None)
        if type(source) is not _ValidatedContourSource or source != data:
            if __package__:
                from .cad_verify_v4_contours import validate_contour
            else:
                from cad_verify_v4_contours import validate_contour
            validate_contour(record)
        width = _number(float(obj.Width), 'width', True)
        thickness = _number(float(obj.Thickness), 'thickness', True)
        nominal = _number(record['nominal_width_mm'], 'nominal_width', True)
        face = contour_face(record, width / nominal)
        solid = face.extrude(App.Vector(0, 0, thickness))
        solid.translate(obj.Origin)
        return solid


class EngravingProxy(_FrozenProxy):
    def expected_solids(self, obj):
        if obj.Base is None:
            raise ValueError('engraving_base_missing')
        proxy = obj.Base.Proxy if 'Proxy' in obj.Base.PropertiesList else None
        return proxy.expected_solids(obj.Base) if type(proxy) in (ContourProxy, EngravingProxy) else 1

    def construct(self, obj):
        import FreeCAD as App
        _, _, text_module = _imports()
        if obj.Base is None:
            raise ValueError('engraving_base_missing')
        base = _solid(obj.Base.Shape, self.expected_solids(obj))
        raw = base64.b64decode(obj.FontData, validate=True)
        if hashlib.sha256(raw).hexdigest() != obj.FontDigest:
            raise ValueError('embedded_font_digest')
        outline = text_module.outline_from_bytes(raw, obj.FontId, obj.GlyphRegistry,
                                                 obj.Text, float(obj.Height))
        entry = {'depth_mm': float(obj.Depth), 'origin_mm': list(obj.Origin),
                 'rotation_axis': list(obj.RotationAxis), 'rotation_deg': float(obj.RotationAngle)}
        tool = engraving_tool(entry, outline)
        numerical_volume = max(1e-7, tool.Volume * 1e-8)
        if tool.cut(base).Volume > numerical_volume:
            raise ValueError('engraving_not_fully_in_target')
        # Outside of the entry face must be void; below the end must remain material.
        # This verifies an actual surface recess in the declared full 3D frame.
        face = contour_face(outline)
        outside = face.extrude(App.Vector(0, 0, 1e-6))
        outside.Placement = engraving_placement(entry)
        floor = face.extrude(App.Vector(0, 0, -1e-6))
        floor.Placement = engraving_placement(entry).multiply(
            App.Placement(App.Vector(0, 0, -float(obj.Depth)), App.Rotation()))
        if outside.common(base).Volume > max(1e-12, outside.Volume * 1e-6):
            raise ValueError('engraving_entry_not_exposed')
        if floor.cut(base).Volume > max(1e-12, floor.Volume * 1e-6):
            raise ValueError('engraving_has_no_recess_floor')
        result = _solid(base.cut(tool), self.expected_solids(obj))
        if result.Volume >= base.Volume:
            raise ValueError('engraving_no_removed_material')
        return result


def _property(obj, kind, name, value):
    obj.addProperty(kind, name, 'S1')
    setattr(obj, name, value)


def build_plan(doc, plan, manifest_path, prepared):
    import FreeCAD as App
    cad_spec, inputs, text_module = _imports()
    if __package__:
        from .cad_verify_v4_plans import validate_plan
    else:
        from cad_verify_v4_plans import validate_plan
    plan = validate_plan(plan, manifest_path, prepared)
    expected = inputs.contour_solid_count(prepared['assets'][plan['contour_id']]) if plan['family'] == 'contour_extrude' else 1
    multiple = expected > 1
    if plan['family'] == 'reference_fixture':
        body = cad_spec.build_native(doc, cad_spec.validate_spec(plan['build_spec']))
    elif plan['family'] == 'contour_extrude':
        record = prepared['assets'][plan['contour_id']]
        if multiple:
            feature = body = doc.addObject('Part::FeaturePython', 'ContourExtrude')
        else:
            body = doc.addObject('PartDesign::Body', 'Model')
            feature = body.newObject('PartDesign::FeaturePython', 'ContourExtrude')
        _property(feature, 'App::PropertyString', 'ContourData', json.dumps(record, allow_nan=False))
        feature.setEditorMode('ContourData', 1)
        _property(feature, 'App::PropertyLength', 'Width', plan['width_mm'])
        _property(feature, 'App::PropertyLength', 'Thickness', plan['thickness_mm'])
        _property(feature, 'App::PropertyVector', 'Origin', App.Vector(*plan['origin_mm']))
        _property(feature, 'App::PropertyString', 'BuildStatus', 'new')
        feature.setEditorMode('BuildStatus', 1)
        feature.Proxy = ContourProxy()
        if not multiple:
            body.Tip = feature
        doc.recompute()
        _solid(feature.Shape, expected)
    else:
        raise ValueError('unsupported_s1_family')
    for index, entry in enumerate(plan['engravings']):
        # Validate font/license/glyph registry before any document-owned font state exists.
        text_module.text_outline(manifest_path, entry['font_id'], entry['text'], entry['height_mm'])
        asset = inputs.resolve_asset(manifest_path, entry['font_id'], 'font')
        raw = asset['path'].read_bytes()
        if hashlib.sha256(raw).hexdigest() != asset['digest']:
            raise ValueError('font_changed_during_compile')
        previous = body if multiple else body.Tip
        feature = (doc.addObject('Part::FeaturePython', 'Engraving' + str(index)) if multiple else
                   body.newObject('PartDesign::FeaturePython', 'Engraving' + str(index)))
        for kind, name, value in (
            ('App::PropertyLink', 'Base', previous),
            ('App::PropertyString', 'Text', entry['text']),
            ('App::PropertyLength', 'Height', entry['height_mm']),
            ('App::PropertyLength', 'Depth', entry['depth_mm']),
            ('App::PropertyVector', 'Origin', App.Vector(*entry['origin_mm'])),
            ('App::PropertyVector', 'RotationAxis', App.Vector(*entry['rotation_axis'])),
            ('App::PropertyAngle', 'RotationAngle', entry['rotation_deg']),
            ('App::PropertyString', 'FontId', entry['font_id']),
            ('App::PropertyString', 'FontDigest', asset['digest']),
            ('App::PropertyString', 'FontData', base64.b64encode(raw).decode('ascii')),
            ('App::PropertyString', 'GlyphRegistry', asset['record']['glyphs']),
            ('App::PropertyString', 'BuildStatus', 'new')):
            _property(feature, kind, name, value)
        for name in ('FontId', 'FontDigest', 'FontData', 'GlyphRegistry', 'BuildStatus'):
            feature.setEditorMode(name, 1)
        feature.Proxy = EngravingProxy()
        if multiple:
            body = feature
        else:
            body.Tip = feature
        doc.recompute()
        _solid(feature.Shape, expected)
    doc.recompute()
    check_document(doc, body)
    return body


def output_for_plan(doc, plan, prepared):
    """Select the actual frozen graph output; no native count override is trusted."""
    _, inputs, _ = _imports()
    expected = (inputs.contour_solid_count(prepared['assets'][plan['contour_id']])
                if plan.get('profile') == 'c-s1' and plan.get('family') == 'contour_extrude' else 1)
    if expected > 1:
        name = 'Engraving' + str(len(plan['engravings']) - 1) if plan['engravings'] else 'ContourExtrude'
        output = doc.getObject(name)
        proxy_type = EngravingProxy if plan['engravings'] else ContourProxy
        root = doc.getObject('ContourExtrude')
        if (output is None or output.TypeId != 'Part::FeaturePython' or type(output.Proxy) is not proxy_type or
                root is None or type(root.Proxy) is not ContourProxy or
                json.loads(root.ContourData) != prepared['assets'][plan['contour_id']]):
            raise ValueError('native_compound_output_graph')
    else:
        bodies = [obj for obj in doc.Objects if obj.TypeId == 'PartDesign::Body']
        if len(bodies) != 1:
            raise ValueError('native_body_count')
        output = bodies[0]
    check_document(doc, output)
    return output


def check_document(doc, body):
    multiple = body.TypeId == 'Part::FeaturePython' and type(body.Proxy) in (ContourProxy, EngravingProxy)
    expected = body.Proxy.expected_solids(body) if multiple else 1
    bodies = [obj for obj in doc.Objects if obj.TypeId == 'PartDesign::Body']
    if multiple:
        if expected <= 1 or bodies:
            raise ValueError('native_compound_output_graph')
    elif body.TypeId != 'PartDesign::Body' or body.Tip is None:
        raise ValueError('native_body_tip')
    elif bodies != [body]:
        raise ValueError('native_body_count')
    for obj in doc.Objects:
        if 'BuildStatus' in obj.PropertiesList and obj.BuildStatus != 'ok':
            raise ValueError('native_feature_recompute:' + obj.Name)
        if any(state in ('Invalid', 'Error', 'Touched') for state in obj.State):
            raise ValueError('native_document_state:' + obj.Name)
    if not multiple:
        _solid(body.Tip.Shape)
    _solid(body.Shape, expected)
    return True


def operative_evidence(doc, body):
    """Exercise native property edits, recompute, restore; never save altered probes."""
    check_document(doc, body)
    evidence = []
    features = body.Group if body.TypeId == 'PartDesign::Body' else doc.Objects
    for obj in features:
        if isinstance(obj.Proxy if 'Proxy' in obj.PropertiesList else None, ContourProxy):
            names = ('Width', 'Thickness')
        elif isinstance(obj.Proxy if 'Proxy' in obj.PropertiesList else None, EngravingProxy):
            names = ('Height', 'Depth', 'Text', 'Origin', 'RotationAngle')
        elif obj.TypeId in ('PartDesign::Pad', 'PartDesign::Pocket'):
            names = ('Length',)
        else:
            continue
        for name in names:
            old = getattr(obj, name)
            before = obj.Shape.copy()
            # A failed enlargement is still an operative dependency if invalid Shape is cleared.
            if name == 'Text':
                changed = old + next(character for character in old if not character.isspace())
            elif name == 'Origin':
                import FreeCAD as App
                changed = old + App.Vector(1e-3, 0, 0)
            elif name == 'RotationAngle':
                changed = float(old) + 0.01
            else:
                changed = float(old) * 1.01
            probe = dict(object=obj.Name, property=name)
            if name == 'Text':
                probe.update(kind='text', suffix=changed[len(old):])
            elif name == 'Origin':
                probe.update(kind='vector', delta_mm=list(changed - old))
            else:
                probe.update(kind='scalar', delta=float(changed) - float(old))
            try:
                setattr(obj, name, changed)
                doc.recompute()
                after = obj.Shape
                invalidated = after.isNull() and 'BuildStatus' in obj.PropertiesList and obj.BuildStatus.startswith('failed:')
                changed_indices = []
                if after.isNull():
                    operative = invalidated
                else:
                    # Symmetric-difference volume proves geometry changed, including placement/text.
                    operative = before.cut(after).Volume + after.cut(before).Volume > 1e-10
                    if len(before.Solids) > 1:
                        _solid(after, len(before.Solids))
                        changed_indices = [i for i, (a, b) in enumerate(zip(before.Solids, after.Solids))
                                           if a.cut(b).Volume + b.cut(a).Volume > 1e-10]
                        if name in ('Width', 'Thickness'):
                            operative = operative and len(changed_indices) == len(before.Solids)
                row = {'feature': obj.Name, 'property': name, 'operative': operative,
                       'invalidated_on_rejected_edit': invalidated, 'artifact_probe': probe}
                if len(before.Solids) > 1:
                    row['changed_solid_indices'] = changed_indices
                evidence.append(row)
            finally:
                setattr(obj, name, old)
                doc.recompute()
                check_document(doc, body)
    if not evidence or not all(row['operative'] for row in evidence):
        raise ValueError('native_inoperative_properties')
    return evidence


def check_model_inputs(body, plan, prepared, manifest_path):
    """Bind operative restored properties and embedded data to the admitted inputs."""
    _, inputs, _ = _imports()
    doc = body.Document
    expected_python = len(plan['engravings']) + (plan['family'] == 'contour_extrude')
    expected_type = 'Part::FeaturePython' if body.TypeId == 'Part::FeaturePython' else 'PartDesign::FeaturePython'
    if len([obj for obj in doc.Objects if obj.TypeId == expected_type]) != expected_python:
        raise ValueError('unexpected_native_python_features')
    if plan['family'] == 'contour_extrude':
        feature = doc.getObject('ContourExtrude')
        if feature is None or type(feature.Proxy) is not ContourProxy:
            raise ValueError('contour_feature_missing')
        if (float(feature.Width) != plan['width_mm'] or
                float(feature.Thickness) != plan['thickness_mm'] or
                list(feature.Origin) != plan['origin_mm'] or
                json.loads(feature.ContourData) != prepared['assets'][plan['contour_id']]):
            raise ValueError('restored_contour_input_mismatch')
    for index, entry in enumerate(plan['engravings']):
        feature = doc.getObject('Engraving' + str(index))
        if feature is None or type(feature.Proxy) is not EngravingProxy:
            raise ValueError('engraving_feature_missing')
        font = inputs.resolve_asset(manifest_path, entry['font_id'], 'font')
        if (feature.Text != entry['text'] or float(feature.Height) != entry['height_mm'] or
                float(feature.Depth) != entry['depth_mm'] or list(feature.Origin) != entry['origin_mm'] or
                list(feature.RotationAxis) != entry['rotation_axis'] or
                float(feature.RotationAngle) != entry['rotation_deg'] or
                feature.FontId != entry['font_id'] or feature.FontDigest != font['digest'] or
                feature.GlyphRegistry != font['record']['glyphs'] or
                hashlib.sha256(base64.b64decode(feature.FontData, validate=True)).hexdigest() != font['digest']):
            raise ValueError('restored_engraving_input_mismatch')
        expected_base = doc.getObject('Engraving' + str(index - 1)) if index else (
            doc.getObject('ContourExtrude') if plan['family'] == 'contour_extrude' else None)
        if feature.Base is None or (expected_base is not None and feature.Base != expected_base):
            raise ValueError('restored_engraving_dependency_mismatch')
    return True
