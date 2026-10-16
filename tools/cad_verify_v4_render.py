"""Deterministic output-only STEP views for the model judge, never metrology.

Tessellation settings are visualization settings, not acceptance tolerances.
The trusted worker supplies runtime/ownership/cleanup evidence. No GUI, model,
original pilot image, input solution, or ambient font is used.
"""
import hashlib
import math
from pathlib import Path

SETTINGS = dict(width=640, height=640, views=['front', 'right', 'top', 'isometric'],
                deflection_divisor=300, light_direction_world=[1., -2., 3.])
CAMERAS = dict(front=((0., -1., 0.), (0., 0., 1.)),
               right=((1., 0., 0.), (0., 0., 1.)),
               top=((0., 0., 1.), (0., 1., 0.)),
               isometric=((1., -1., 1.), (0., 0., 1.)))


def _module(name):
    import importlib
    return importlib.import_module(('tools.' if __package__ else '') + name)


def _unit(vector):
    length = math.sqrt(sum(value*value for value in vector))
    if not length:
        raise ValueError('render_camera_zero')
    return tuple(value/length for value in vector)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _record(path):
    payload = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))


def _view(points, triangles, name, out):
    from PIL import Image, ImageDraw, ImageFont
    forward, up = CAMERAS[name]
    forward = _unit(forward)
    right = _unit(_cross(up, forward))
    vertical = _unit(_cross(forward, right))
    light_direction = _unit(SETTINGS['light_direction_world'])
    projected = [(_dot(point, right), _dot(point, vertical), _dot(point, forward)) for point in points]
    x0, x1 = min(p[0] for p in projected), max(p[0] for p in projected)
    y0, y1 = min(p[1] for p in projected), max(p[1] for p in projected)
    width, height = SETTINGS['width'], SETTINGS['height']
    span = max(x1-x0, y1-y0)
    if not math.isfinite(span) or span <= 0:
        raise ValueError('render_projected_extent')
    scale = (min(width, height)-64)/span
    screen = [((p[0]-(x0+x1)/2)*scale+width/2,
               height/2-(p[1]-(y0+y1)/2)*scale, p[2]) for p in projected]
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    for face in sorted(triangles, key=lambda tri: sum(screen[i][2] for i in tri)):
        a, b, c = (points[i] for i in face)
        normal = _cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
        length = math.sqrt(sum(v*v for v in normal))
        light = abs(_dot(normal, light_direction))/length if length else 0.
        shade = int(95+100*light)
        draw.polygon([(screen[i][0], screen[i][1]) for i in face], fill=(shade-20, shade, min(255, shade+25)))
    # Default Pillow bitmap font is deterministic and requires no host font file.
    draw.text((12, 12), 'ACTUAL OUTPUT / '+name, fill='black', font=ImageFont.load_default())
    path = out / (name+'.png')
    image.save(path, format='PNG', optimize=False)
    return _record(path)


def render(job, out):
    import Part
    inputs = _module('cad_verify_v4_inputs')
    ledger = _module('cad_verify_v4_ledger')
    if job.get('settings') != SETTINGS:
        raise ValueError('render_frozen_settings_required')
    record = job.get('step')
    if (not isinstance(record, dict) or set(record) != {'path', 'sha256', 'bytes'}
            or type(record['bytes']) is not int or record['bytes'] <= 0):
        raise ValueError('render_step_record_required')
    path = inputs.guarded_path(record['path'])
    if path.stat().st_size != record['bytes'] or ledger.file_sha(path) != record['sha256']:
        raise ValueError('render_step_commitment_changed')
    shape = Part.Shape()
    shape.read(str(path))
    if shape.isNull() or not shape.isValid() or not shape.Solids:
        raise ValueError('render_valid_output_solid_required')
    bounds = shape.BoundBox
    extent = max(bounds.XLength, bounds.YLength, bounds.ZLength)
    if not math.isfinite(extent) or extent <= 0:
        raise ValueError('render_output_extent')
    deflection = extent/SETTINGS['deflection_divisor']
    vertices, triangles = shape.tessellate(deflection)
    if len(vertices) > 1000000 or len(triangles) > 2000000:
        raise ValueError('render_mesh_resource_limit')
    points = [(v.x, v.y, v.z) for v in vertices]
    if not points or not triangles or any(not all(math.isfinite(v) for v in p) for p in points):
        raise ValueError('render_mesh_invalid')
    images = [_view(points, triangles, name, Path(out)) for name in SETTINGS['views']]
    if path.stat().st_size != record['bytes'] or ledger.file_sha(path) != record['sha256']:
        raise ValueError('render_step_changed_during_capture')
    return dict(schema='cad-harness.render-evidence.v1', profile=job.get('profile', 'c-s1'), status='PASS',
                step=dict(record), images=images, settings=SETTINGS, mesh_deflection_mm=deflection,
                triangles=len(triangles), bounds_mm=[bounds.XMin, bounds.XMax, bounds.YMin, bounds.YMax,
                                                   bounds.ZMin, bounds.ZMax],
                evidence_kind='actual_native_step_tessellation_views', not_a_metrology_certificate=True)
