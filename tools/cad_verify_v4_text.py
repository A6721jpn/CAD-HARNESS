"""Registered fonts only; exact quadratic/cubic ink contours, never font fallback.

Height is the complete text's actual ink-bound height, not point size. Whitespace
advances are retained; all-whitespace strings have no engravable ink and fail.
"""
import hashlib
import io
import math


def _modules():
    if __package__:
        from . import cad_verify_v4_inputs as inputs, cad_verify_v4_ledger as ledger
    else:
        import cad_verify_v4_inputs as inputs
        import cad_verify_v4_ledger as ledger
    return inputs, ledger


def outline_from_bytes(raw, font_id, glyph_registry, text, height_mm):
    """Rebuild from embedded, digest-bound registered font bytes on recompute."""
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.pointInsidePen import PointInsidePen
    from fontTools.pens.areaPen import AreaPen
    if not isinstance(text, str) or not text or not isinstance(glyph_registry, str):
        raise ValueError('text_or_glyph_registry')
    if type(height_mm) not in (int, float) or not math.isfinite(height_mm) or height_mm <= 0:
        raise ValueError('text_height')
    font = TTFont(io.BytesIO(raw), lazy=False)
    try:
        cmap = font.getBestCmap()
        missing = [c for c in text if c not in glyph_registry or ord(c) not in cmap]
        if missing:
            raise ValueError('font_glyph_coverage:' + ','.join(str(ord(c)) for c in missing))
        glyph_set = font.getGlyphSet()
        raw_loops, glyphs = [], []
        cursor = 0.0

        class Collector(BasePen):
            def _moveTo(self, p):
                self.start = self.current = (p[0] + cursor, p[1])
                self.segments = []

            def _lineTo(self, p):
                end = (p[0] + cursor, p[1])
                if end != self.current:
                    self.segments.append({'kind': 'line', 'p0': list(self.current), 'p1': list(end)})
                self.current = end

            def _qCurveToOne(self, control, end):
                target = (end[0] + cursor, end[1])
                self.segments.append({'kind': 'bezier', 'poles': [list(self.current),
                    [control[0] + cursor, control[1]], list(target)]})
                self.current = target

            def _curveToOne(self, first, second, end):
                target = (end[0] + cursor, end[1])
                self.segments.append({'kind': 'bezier', 'poles': [list(self.current),
                    [first[0] + cursor, first[1]], [second[0] + cursor, second[1]], list(target)]})
                self.current = target

            def _closePath(self):
                self._lineTo((self.start[0] - cursor, self.start[1]))
                if self.segments:
                    raw_loops.append(self.segments)

            def _endPath(self):
                raise ValueError('font_open_ink_contour')

        collector = Collector(glyph_set)
        for character in text:
            name = cmap[ord(character)]
            glyph_set[name].draw(collector)
            advance = float(font['hmtx'].metrics[name][0])
            glyphs.append({'character': character, 'codepoint': ord(character),
                           'glyph_name': name, 'advance_font_units': advance})
            cursor += advance
        if not raw_loops:
            raise ValueError('text_has_no_ink')

        def replay(segments, pen):
            start = segments[0].get('p0', segments[0].get('poles', [None])[0])
            pen.moveTo(tuple(start))
            for segment in segments:
                if segment['kind'] == 'line':
                    pen.lineTo(tuple(segment['p1']))
                else:
                    poles = segment['poles']
                    if len(poles) == 3:
                        pen.qCurveTo(*map(tuple, poles[1:]))
                    else:
                        pen.curveTo(*map(tuple, poles[1:]))
            pen.closePath()

        bounds_pen = BoundsPen(glyph_set)
        for loop in raw_loops:
            replay(loop, bounds_pen)
        xmin, ymin, xmax, ymax = bounds_pen.bounds
        if ymax <= ymin:
            raise ValueError('text_degenerate_ink')
        scale = height_mm / (ymax - ymin)
        loops = []
        for index, segments in enumerate(raw_loops):
            point = segments[0].get('p0', segments[0].get('poles', [None])[0])
            containers = []
            for other_index, other in enumerate(raw_loops):
                if index == other_index:
                    continue
                inside = PointInsidePen(glyph_set, tuple(point), evenOdd=True)
                replay(other, inside)
                if inside.getResult():
                    area = AreaPen(glyph_set)
                    replay(other, area)
                    containers.append((abs(area.value), other_index))
            role = 'hole' if len(containers) % 2 else 'outer'
            area = AreaPen(glyph_set)
            replay(segments, area)
            if area.value == 0:
                raise ValueError('font_zero_area_contour')
            if (area.value > 0) != (role == 'outer'):
                reverse = []
                for segment in reversed(segments):
                    if segment['kind'] == 'line':
                        reverse.append({'kind': 'line', 'p0': segment['p1'], 'p1': segment['p0']})
                    else:
                        reverse.append({'kind': 'bezier', 'poles': list(reversed(segment['poles']))})
                segments = reverse
            scaled = []
            for segment in segments:
                if segment['kind'] == 'line':
                    scaled.append({'kind': 'line', 'p0': [v * scale for v in segment['p0']],
                                   'p1': [v * scale for v in segment['p1']]})
                else:
                    scaled.append({'kind': 'bezier', 'poles': [[v * scale for v in p] for p in segment['poles']]})
            loops.append({'role': role, 'segments': scaled,
                          'parent': min(containers)[1] if containers else None})
        for glyph in glyphs:
            glyph['advance_mm'] = glyph.pop('advance_font_units') * scale
        return {'schema': 'cad-harness.text-outline.v4c', 'profile': 'c-s1',
                'font_id': font_id, 'font_sha256': hashlib.sha256(raw).hexdigest(),
                'text': text, 'units': 'mm', 'height_mm': height_mm,
                'bounds_mm': [xmin * scale, xmax * scale, ymin * scale, ymax * scale],
                'nominal_width_mm': (xmax - xmin) * scale, 'loops': loops, 'glyphs': glyphs,
                'scaling': {'font_units_per_em': font['head'].unitsPerEm,
                            'scale_mm_per_font_unit': scale, 'height_basis': 'actual_text_ink_bounds'},
                'coverage': {'complete': True, 'missing': []}}
    finally:
        font.close()


def text_outline(manifest_path, font_id, text, height_mm, out=None):
    inputs, ledger = _modules()
    asset = inputs.resolve_asset(manifest_path, font_id, 'font')
    inputs.resolve_asset(manifest_path, asset['record']['license_asset_id'], 'license')
    raw = asset['path'].read_bytes()
    if ledger.sha(raw) != asset['digest']:
        raise ValueError('font_changed_during_read')
    result = outline_from_bytes(raw, font_id, asset['record']['glyphs'], text, height_mm)
    result['source_manifest_sha256'] = ledger.file_sha(manifest_path)
    if out is not None:
        ledger.write_json(out, result)
    return result
