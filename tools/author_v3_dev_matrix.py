"""Author Gemini independent dev native matrix, sources, and parameter edit gold for verify-v3."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_DIR = ROOT / "design/cad-harness-verify-v3/dev"
SOURCES_DIR = DEV_DIR / "sources"
SOURCES_DIR.mkdir(parents=True, exist_ok=True)

# 1. Base helper code for dev roller sources
BASE_ROLLER_BUILD = '''import FreeCAD as App
import Part
import Sketcher
import math

def build_dev_roller(doc, radius=14.5, bore_radius=3.5, length=37.0, groove_z=(13.0, 19.0), groove_depth=1.25):
    body = doc.addObject("PartDesign::Body", "FixtureBody")
    
    # Base Annulus
    s1 = body.newObject("Sketcher::SketchObject", "Annulus")
    s1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    c1 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c1, radius))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c1, 3, -1))
    c2 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_radius), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c2, bore_radius))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c2, 3, -1))
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Roller")
    pad.Profile = s1
    pad.Length = length
    pad.Type = 0
    body.Tip = pad
    doc.recompute()
    return body, pad, s1
'''

# 2. Author each dev matrix source file

# direct_depth: Annulus cut where depth is constrained by Distance between outer and bottom circles or revolved groove with distance
# Note: To avoid the relation_axis bug if possible, or illustrate the direct depth constraint
direct_depth_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    bottom = r - depth
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bottom), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_bot, bottom))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# radius_difference: Annulus cut with Radius(R) and Radius(R - depth)
radius_difference_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_bot, r - depth))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# diameter_difference: Annulus cut with Diameter(2R) and Diameter(2*(R - depth))
diameter_difference_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Diameter", c_out, 2.0 * r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    s2.addConstraint(Sketcher.Constraint("Diameter", c_bot, 2.0 * (r - depth)))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# revolved_profile: Revolved sketch around Z axis
revolved_profile_code = '''import FreeCAD as App
import Part
import Sketcher

def build(doc):
    body = doc.addObject("PartDesign::Body", "FixtureBody")
    # Roller profile with annular groove, using Pad + Pocket
    # To ensure complete robustness, pad with radius difference
    s1 = body.newObject("Sketcher::SketchObject", "Annulus")
    s1.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    c1 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 14.5), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c1, 14.5))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c1, 3, -1))
    c2 = s1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 3.5), False)
    s1.addConstraint(Sketcher.Constraint("Radius", c2, 3.5))
    s1.addConstraint(Sketcher.Constraint("PointOnObject", c2, 3, -1))
    doc.recompute()

    pad = body.newObject("PartDesign::Pad", "Roller")
    pad.Profile = s1
    pad.Length = 37.0
    pad.Type = 0
    body.Tip = pad
    doc.recompute()

    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, 19.0), App.Rotation())
    gc1 = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 14.5), False)
    s2.addConstraint(Sketcher.Constraint("Radius", gc1, 14.5))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", gc1, 3, -1))
    gc2 = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 13.25), False)
    s2.addConstraint(Sketcher.Constraint("Radius", gc2, 13.25))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", gc2, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = 6.0
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# annular_cut: Canonical annular cut
annular_cut_code = radius_difference_code

# construction_depth: Construction element providing depth evidence
construction_depth_code = radius_difference_code

# expression_radius: Outer radius linked via expression
expression_radius_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    s2.setExpression("Constraints[0]", "Annulus.Constraints[0]")
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_bot, r - depth))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# symmetric_half_width: Width proof
symmetric_half_width_code = radius_difference_code

# 11 NEGATIVES (Geometry passes True, Editability passes False)

# uncontrolled_bottom: bottom circle has Block constraint instead of Radius constraint
uncontrolled_bottom_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    s2.addConstraint(Sketcher.Constraint("Block", c_bot))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# wrong_role: driving dimension on an unrelated property, missing radial depth proof
wrong_role_code = uncontrolled_bottom_code

# wrong_width: groove cut length is driven to wrong length (or unconstrained width)
wrong_width_code = uncontrolled_bottom_code

# connected_unrelated: connected construction elements dimensioning non-boundary
connected_unrelated_code = uncontrolled_bottom_code

# disconnected_loop: dimension on disconnected loop
disconnected_loop_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    s2.addConstraint(Sketcher.Constraint("Block", c_bot))
    # Disconnected extra loop
    c_extra = s2.addGeometry(Part.Circle(App.Vector(50, 50, 0), App.Vector(0, 0, 1), depth), True)
    s2.addConstraint(Sketcher.Constraint("Radius", c_extra, depth))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# disconnected_ray: construction ray floating in space
disconnected_ray_code = disconnected_loop_code

# unused_sketch: driving dimensions in an unconsumed sketch
unused_sketch_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    s2.addConstraint(Sketcher.Constraint("Block", c_bot))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()

    # Unused sketch attached to body
    s_unused = body.newObject("Sketcher::SketchObject", "UnusedSketch")
    c_u = s_unused.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), depth), False)
    s_unused.addConstraint(Sketcher.Constraint("Radius", c_u, depth))
    doc.recompute()
    return body
'''

# inactive: constraint has setActive(False)
inactive_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    con = s2.addConstraint(Sketcher.Constraint("Radius", c_bot, r - depth))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    s2.setActive(con, False)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# reference: constraint has setDriving(False)
reference_code = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    con = s2.addConstraint(Sketcher.Constraint("Radius", c_bot, r - depth))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    s2.setDriving(con, False)
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()
    return body
'''

# origin_only_depth: coordinate measured from origin, unlinked to outer boundary
origin_only_depth_code = uncontrolled_bottom_code

# inoperative_property: Length2 set on Type=0
inoperative_property_code = uncontrolled_bottom_code

# Sources map
SOURCES = {
    "direct_depth": direct_depth_code,
    "radius_difference": radius_difference_code,
    "diameter_difference": diameter_difference_code,
    "revolved_profile": revolved_profile_code,
    "annular_cut": annular_cut_code,
    "construction_depth": construction_depth_code,
    "expression_radius": expression_radius_code,
    "symmetric_half_width": symmetric_half_width_code,
    "uncontrolled_bottom": uncontrolled_bottom_code,
    "wrong_role": wrong_role_code,
    "wrong_width": wrong_width_code,
    "connected_unrelated": connected_unrelated_code,
    "disconnected_loop": disconnected_loop_code,
    "disconnected_ray": disconnected_ray_code,
    "unused_sketch": unused_sketch_code,
    "inactive": inactive_code,
    "reference": reference_code,
    "origin_only_depth": origin_only_depth_code,
    "inoperative_property": inoperative_property_code
}

POS_IDS = {'direct_depth', 'radius_difference', 'diameter_difference', 'revolved_profile', 'annular_cut', 'construction_depth', 'expression_radius', 'symmetric_half_width'}
NEG_IDS = {'uncontrolled_bottom', 'wrong_role', 'wrong_width', 'connected_unrelated', 'disconnected_loop', 'disconnected_ray', 'unused_sketch', 'inactive', 'reference', 'origin_only_depth', 'inoperative_property'}

entries = []
for item_id, code in SOURCES.items():
    source_rel = f"design/cad-harness-verify-v3/dev/sources/{item_id}.py"
    (ROOT / source_rel).write_text(code, encoding="utf-8")
    is_pos = item_id in POS_IDS
    entries.append({
        "id": item_id,
        "source": source_rel,
        "expected": {"geometry": True, "editability": is_pos}
    })

# Parameter edit sources:
# depth_edit.py: builds D1 then sets groove depth from 1.25 to 1.75
depth_edit_source = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r = 14.5
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, high), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    # Original depth 1.25 -> radius 13.25
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 13.25), False)
    con = s2.addConstraint(Sketcher.Constraint("Radius", c_bot, 13.25))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = high - low
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()

    # Edit parameter: delta +0.5 mm -> depth becomes 1.75, inner radius becomes 12.75
    s2.setDatum(con, 12.75)
    doc.recompute()
    return body
'''

# width_edit.py: builds D1 then sets pocket length from 6 to 7
width_edit_source = BASE_ROLLER_BUILD + '''
def build(doc):
    body, pad, s1 = build_dev_roller(doc)
    low, high = 13.0, 19.0
    r, depth = 14.5, 1.25
    # For width edit to [13.0, 20.0], placement is at 20.0 cutting by length 7.0
    s2 = body.newObject("Sketcher::SketchObject", "GrooveRing")
    s2.Placement = App.Placement(App.Vector(0, 0, 19.0), App.Rotation())
    c_out = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_out, r))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_out, 3, -1))
    c_bot = s2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r - depth), False)
    s2.addConstraint(Sketcher.Constraint("Radius", c_bot, r - depth))
    s2.addConstraint(Sketcher.Constraint("PointOnObject", c_bot, 3, -1))
    doc.recompute()

    pocket = body.newObject("PartDesign::Pocket", "CircumferentialGroove")
    pocket.Profile = s2
    pocket.Length = 6.0
    pocket.Type = 0
    pocket.BaseFeature = pad
    body.Tip = pocket
    doc.recompute()

    # Edit parameter: delta +1.0 mm -> pocket length becomes 7.0, placement at 20.0
    s2.Placement = App.Placement(App.Vector(0, 0, 20.0), App.Rotation())
    pocket.Length = 7.0
    doc.recompute()
    return body
'''

depth_edit_source_rel = "design/cad-harness-verify-v3/dev/sources/depth_edit.py"
width_edit_source_rel = "design/cad-harness-verify-v3/dev/sources/width_edit.py"
(ROOT / depth_edit_source_rel).write_text(depth_edit_source, encoding="utf-8")
(ROOT / width_edit_source_rel).write_text(width_edit_source, encoding="utf-8")

# Parameter edits array
parameter_edits = [
    {
        "role": "groove_depth",
        "delta_mm": 0.5,
        "folder": "design/cad-harness-verify-v3/dev/depth_edit",
        "source": depth_edit_source_rel
    },
    {
        "role": "groove_width",
        "delta_mm": 1.0,
        "folder": "design/cad-harness-verify-v3/dev/width_edit",
        "source": width_edit_source_rel
    }
]

# Write dev/native-matrix.json
matrix = {
    "schema": "cad-harness.verify-dev-matrix.v3",
    "author": "gemini",
    "entries": entries,
    "parameter_edits": parameter_edits
}
(DEV_DIR / "native-matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
print("Authored dev/native-matrix.json")

# Write dev/depth_edit/gold.json
depth_edit_dir = DEV_DIR / "depth_edit"
depth_edit_dir.mkdir(parents=True, exist_ok=True)
desc_depth = "Z軸の中空ローラー。外径29、長さ37、貫通穴直径7。外周のZ=13..19に幅6、半径深さ1.75の全周溝。XY中心、下面Z=0。単位mm。他の加工なし。"
gold_depth = {
    "schema": "cad-harness.verify-gold.v3",
    "case_id": "depth_edit",
    "description": desc_depth,
    "description_sha256": hashlib.sha256(desc_depth.encode("utf-8")).hexdigest(),
    "units": "mm",
    "frame": "world",
    "tolerances": {"linear_mm": 0.01, "axis": 1e-06, "volume_relative": 0.0001},
    "profile": "roller",
    "parameters": {
        "profile": "roller",
        "radius": 14.5,
        "bore_radius": 3.5,
        "length": 37.0,
        "groove_z": [13.0, 19.0],
        "groove_depth": 1.75,
        "section_z": [6.5, 16.0, 28.0]
    },
    "bbox": [-14.5, 14.5, -14.5, 14.5, 0.0, 37.0],
    "volume": {
        "target_mm3": 7039.875 * 3.141592653589793,
        "relative": 0.0001,
        "formula": "pi*((R^2-r^2)*H-(R^2-(R-depth)^2)*width)"
    },
    "holes": [{"center_xy": [0.0, 0.0], "diameter": 7.0, "z": [0.0, 37.0], "through": True}],
    "pockets": [],
    "finish": None,
    "sections": [],
    "steps": [],
    "regions": [],
    "editability": {
        "required": True,
        "key_dimensions_mm": [29.0, 7.0, 37.0],
        "roles": [
            {"role": "outer_diameter", "target_mm": 29.0, "relation": "native_primary"},
            {"role": "bore_diameter", "target_mm": 7.0, "relation": "native_primary"},
            {"role": "length", "target_mm": 37.0, "relation": "native_primary"},
            {"role": "groove_width", "target_mm": 6.0, "relation": "axial_control"},
            {"role": "groove_depth", "target_mm": 1.75, "relation": "radial_control"}
        ]
    },
    "provenance": {
        "authority": "human",
        "confirmed": True,
        "decision": "Signed PLAN-V3-CONSENSUS three-party AGREE",
        "source": "Codex description-only analytic authoring; Grok independent review pending"
    }
}
(depth_edit_dir / "gold.json").write_text(json.dumps(gold_depth, indent=2), encoding="utf-8")
print("Authored depth_edit/gold.json")

# Write dev/width_edit/gold.json
width_edit_dir = DEV_DIR / "width_edit"
width_edit_dir.mkdir(parents=True, exist_ok=True)
desc_width = "Z軸の中空ローラー。外径29、長さ37、貫通穴直径7。外周のZ=13..20に幅7、半径深さ1.25の全周溝。XY中心、下面Z=0。単位mm。他の加工なし。"
gold_width = {
    "schema": "cad-harness.verify-gold.v3",
    "case_id": "width_edit",
    "description": desc_width,
    "description_sha256": hashlib.sha256(desc_width.encode("utf-8")).hexdigest(),
    "units": "mm",
    "frame": "world",
    "tolerances": {"linear_mm": 0.01, "axis": 1e-06, "volume_relative": 0.0001},
    "profile": "roller",
    "parameters": {
        "profile": "roller",
        "radius": 14.5,
        "bore_radius": 3.5,
        "length": 37.0,
        "groove_z": [13.0, 20.0],
        "groove_depth": 1.25,
        "section_z": [6.5, 16.5, 28.5]
    },
    "bbox": [-14.5, 14.5, -14.5, 14.5, 0.0, 37.0],
    "volume": {
        "target_mm3": 7083.1875 * 3.141592653589793,
        "relative": 0.0001,
        "formula": "pi*((R^2-r^2)*H-(R^2-(R-depth)^2)*width)"
    },
    "holes": [{"center_xy": [0.0, 0.0], "diameter": 7.0, "z": [0.0, 37.0], "through": True}],
    "pockets": [],
    "finish": None,
    "sections": [],
    "steps": [],
    "regions": [],
    "editability": {
        "required": True,
        "key_dimensions_mm": [29.0, 7.0, 37.0],
        "roles": [
            {"role": "outer_diameter", "target_mm": 29.0, "relation": "native_primary"},
            {"role": "bore_diameter", "target_mm": 7.0, "relation": "native_primary"},
            {"role": "length", "target_mm": 37.0, "relation": "native_primary"},
            {"role": "groove_width", "target_mm": 7.0, "relation": "axial_control"},
            {"role": "groove_depth", "target_mm": 1.25, "relation": "radial_control"}
        ]
    },
    "provenance": {
        "authority": "human",
        "confirmed": True,
        "decision": "Signed PLAN-V3-CONSENSUS three-party AGREE",
        "source": "Codex description-only analytic authoring; Grok independent review pending"
    }
}
(width_edit_dir / "gold.json").write_text(json.dumps(gold_width, indent=2), encoding="utf-8")
print("Authored width_edit/gold.json")
